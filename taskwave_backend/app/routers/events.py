from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import uuid4
from typing import List

from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.models.subject import Subject
from app.models.event import Event
from app.schemas.event import EventCreate, EventUpdate, EventOut

router = APIRouter()

@router.post("/events", response_model=EventOut, status_code=status.HTTP_201_CREATED)
def create_event(
    payload: EventCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """새로운 시험/과제 이벤트를 생성합니다."""
    # 해당 과목이 현재 사용자의 소유인지 확인
    subject = db.query(Subject).filter(
        Subject.id == payload.subject_id,
        Subject.user_id == current_user.id
    ).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found or not owned by user")

    event = Event(
        id=str(uuid4()),
        subject_id=payload.subject_id,
        title=payload.title,
        event_type=payload.event_type,
        date=payload.date,
        warning_days=payload.warning_days or 3
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event

@router.patch("/events/{event_id}", response_model=EventOut)
def update_event(
    event_id: str,
    payload: EventUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """기존 이벤트를 수정합니다."""
    event = db.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # 해당 이벤트가 현재 사용자의 과목에 속해 있는지 확인
    subject = db.query(Subject).filter(
        Subject.id == event.subject_id,
        Subject.user_id == current_user.id
    ).first()
    if not subject:
        raise HTTPException(status_code=403, detail="Not authorized to update this event")

    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(event, key, value)
    
    db.add(event)
    db.commit()
    db.refresh(event)
    return event

@router.delete("/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event(
    event_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """이벤트를 삭제합니다."""
    event = db.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    subject = db.query(Subject).filter(
        Subject.id == event.subject_id,
        Subject.user_id == current_user.id
    ).first()
    if not subject:
        raise HTTPException(status_code=403, detail="Not authorized to delete this event")

    db.delete(event)
    db.commit()
    return
