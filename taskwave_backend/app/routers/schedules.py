from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from uuid import uuid4
from datetime import date, timedelta
from typing import List

from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.models.subject import Subject
from app.models.schedule import Week, Session as SessionModel
from app.schemas.subject import ManualScheduleIn, SessionForWeekView

router = APIRouter()

WEEKDAY_MAP = {"월": 0, "화": 1, "수": 2, "목": 3, "금": 4, "토": 5, "일": 6}

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
        
        if subject_title in subject_cache:
            subject = subject_cache[subject_title]
        else:
            subject = db.query(Subject).filter(
                Subject.user_id == current.id,
                Subject.title == subject_title
            ).first()
            if not subject:
                subject = Subject(
                    id=str(uuid4()),
                    user_id=current.id,
                    title=subject_title
                )
                db.add(subject)
            subject_cache[subject_title] = subject

        target_weekday = WEEKDAY_MAP.get(slot.weekday)
        if target_weekday is None:
            continue

        days_ahead = target_weekday - today.weekday()
        if days_ahead < 0:
            days_ahead += 7
        first_date = today + timedelta(days=days_ahead)

        for week_num in range(1, SEMESTER_WEEKS + 1):
            current_date = first_date + timedelta(weeks=week_num - 1)

            week = next((w for w in subject.weeks if w.week_no == week_num), None)

            if not week:
                week = Week(
                    id=str(uuid4()),
                    week_no=week_num,
                    month=current_date.month
                )
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
                # 향후 과목별 색상을 여기에 할당할 수 있습니다.
                color="#4A90E2" 
            )
        )
    return result
