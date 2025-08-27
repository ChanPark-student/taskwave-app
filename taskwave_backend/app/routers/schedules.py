from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import uuid4
from datetime import date, timedelta

from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.models.subject import Subject
from app.models.schedule import Week, Session as SessionModel
from app.schemas.subject import ManualScheduleIn

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
    week_cache = {}

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

            week_key = (subject.id, week_num)
            if week_key in week_cache:
                week = week_cache[week_key]
            else:
                week = db.query(Week).filter(
                    Week.subject_id == subject.id,
                    Week.week_no == week_num
                ).first()
                if not week:
                    week = Week(
                        id=str(uuid4()),
                        subject_id=subject.id,
                        week_no=week_num,
                        month=current_date.month
                    )
                    db.add(week)
                week_cache[week_key] = week

            session = SessionModel(
                id=str(uuid4()),
                week_id=week.id,
                date=current_date,
                title=f"{subject_title} 강의",
                start_time=slot.start_time,
                end_time=slot.end_time
            )
            db.add(session)

    db.commit()
    return {"status": "ok", "message": f"{len(payload.slots)} schedule slots processed."}

@router.get("/schedules/ping")
def ping():
    return {"ok": True}