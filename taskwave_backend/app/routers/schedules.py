from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from uuid import uuid4
from datetime import date, timedelta
from typing import List
from pydantic import BaseModel

from app.services.folder_generator import webscrape, parser as manual_parser

from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.models.subject import Subject
from app.models.schedule import Week, Session as SessionModel
from app.schemas.subject import ManualScheduleIn, SessionForWeekView, RecurringScheduleIn

router = APIRouter()

WEEKDAY_MAP = {"월": 0, "화": 1, "수": 2, "목": 3, "금": 4, "토": 5, "일": 6}

class ScrapeRequest(BaseModel):
    url: str
    start_date: date
    end_date: date

@router.post("/schedules/recurring", status_code=201)
def create_recurring_schedule(
    payload: RecurringScheduleIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    지정된 기간과 요일에 따라 반복되는 개인 일정을 생성합니다.
    """
    subject = db.query(Subject).filter(
        Subject.user_id == current_user.id,
        Subject.title == payload.title
    ).first()
    if not subject:
        subject = Subject(
            id=str(uuid4()),
            user_id=current_user.id,
            title=payload.title
        )
        db.add(subject)
        db.flush()

    target_weekdays = {WEEKDAY_MAP[day] for day in payload.weekdays}
    current_date = payload.start_date
    start_monday = payload.start_date - timedelta(days=payload.start_date.weekday())
    sessions_created = 0

    while current_date <= payload.end_date:
        if current_date.weekday() in target_weekdays:
            week_no = (current_date - start_monday).days // 7 + 1
            week = db.query(Week).filter(
                Week.subject_id == subject.id,
                Week.week_no == week_no
            ).first()
            if not week:
                week = Week(
                    id=str(uuid4()),
                    subject_id=subject.id,
                    week_no=week_no,
                    month=current_date.month
                )
                db.add(week)
                db.flush()

            session = SessionModel(
                id=str(uuid4()),
                week_id=week.id,
                date=current_date,
                title=payload.title,
                start_time=payload.start_time,
                end_time=payload.end_time
            )
            db.add(session)
            sessions_created += 1
        
        current_date += timedelta(days=1)

    db.commit()
    return {"status": "ok", "message": f"{sessions_created} sessions created for '{payload.title}'."}


@router.post("/schedules/manual", status_code=201)
def create_manual_schedule(
    payload: ManualScheduleIn,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user)
):
    SEMESTER_WEEKS = 16
    today = date.today()
    subject_cache = {}

    for slot in payload.slots:
        subject_title = slot.subject_title
        if subject_title not in subject_cache:
            subject = db.query(Subject).filter(
                Subject.user_id == current.id,
                Subject.title == subject_title
            ).first()
            if not subject:
                subject = Subject(id=str(uuid4()), user_id=current.id, title=subject_title)
                db.add(subject)
            subject_cache[subject_title] = subject
        else:
            subject = subject_cache[subject_title]

        target_weekday = WEEKDAY_MAP.get(slot.weekday)
        if target_weekday is None: continue

        days_ahead = (target_weekday - today.weekday() + 7) % 7
        first_date = today + timedelta(days=days_ahead)

        for week_num in range(1, SEMESTER_WEEKS + 1):
            current_date = first_date + timedelta(weeks=week_num - 1)
            week = next((w for w in subject.weeks if w.week_no == week_num), None)
            if not week:
                week = Week(id=str(uuid4()), week_no=week_num, month=current_date.month)
                subject.weeks.append(week)
                db.add(week)

            session = SessionModel(
                id=str(uuid4()),
                date=current_date,
                title=f"{subject_title} 강의",
                start_time=slot.start_time,
                end_time=slot.end_time
            )
            week.sessions.append(session)
            db.add(session)

    db.commit()
    return {"status": "ok", "message": f"{len(payload.slots)} schedule slots processed."}

@router.post("/schedules/scrape-from-url")
def scrape_and_create_schedule(
    payload: ScrapeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    주어진 URL에서 시간표를 스크래핑하고, 파싱하여 DB에 저장합니다.
    """
    try:
        scraped_entries = webscrape.parse_schedule_from_web(payload.url)
        if not scraped_entries:
            raise HTTPException(status_code=404, detail="Failed to scrape any schedule entries from the URL.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Web scraping failed: {str(e)}")

    text_block_for_parser = "\n".join([f"{e['subject']},{e['weekday_ko']},{e['start']}-{e['end']}" for e in scraped_entries])

    try:
        class_entries = manual_parser.parse_manual_entries(text_block_for_parser)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse scraped data: {str(e)}")

    subject_cache = {}
    start_monday = payload.start_date - timedelta(days=payload.start_date.weekday())

    for entry in class_entries:
        subject_title = entry.subject
        subject = subject_cache.get(subject_title)
        if not subject:
            subject = db.query(Subject).filter(Subject.user_id == current_user.id, Subject.title == subject_title).first()
            if not subject:
                subject = Subject(id=str(uuid4()), user_id=current_user.id, title=subject_title)
                db.add(subject)
                db.flush()
            subject_cache[subject_title] = subject

        current_date = payload.start_date
        while current_date <= payload.end_date:
            if current_date.weekday() == entry.weekday:
                week_no = (current_date - start_monday).days // 7 + 1
                week = db.query(Week).filter(Week.subject_id == subject.id, Week.week_no == week_no).first()
                if not week:
                    week = Week(id=str(uuid4()), subject_id=subject.id, week_no=week_no, month=current_date.month)
                    db.add(week)
                    db.flush()

                session = SessionModel(
                    id=str(uuid4()),
                    week_id=week.id,
                    date=current_date,
                    title=subject.title,
                    start_time=entry.start,
                    end_time=entry.end
                )
                db.add(session)
            current_date += timedelta(days=1)
    
    db.commit()
    return {"status": "ok", "message": "Schedule scraped and saved successfully."}

@router.get("/schedules/ping")
def ping():
    return {"ok": True}

@router.get("/schedules/week-view", response_model=List[SessionForWeekView])
def get_week_view(
    week_no: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    현재 사용자의 특정 주차에 해당하는 모든 강의 세션을 조회합니다.
    """
    weekday_to_kor = {0: "월", 1: "화", 2: "수", 3: "목", 4: "금", 5: "토", 6: "일"}

    sessions = db.query(SessionModel).join(Week).join(Subject).filter(
        Subject.user_id == current_user.id,
        Week.week_no == week_no
    ).options(
        joinedload(SessionModel.week).joinedload(Week.subject)
    ).order_by(SessionModel.date, SessionModel.start_time).all()

    if not sessions:
        return []

    result = []
    for s in sessions:
        result.append(
            SessionForWeekView(
                subject_title=s.week.subject.title,
                session_id=s.id,
                day_of_week=weekday_to_kor.get(s.date.weekday(), "알수없음"),
                start_time=s.start_time,
                end_time=s.end_time,
                color="#4A90E2"
            )
        )
    return result