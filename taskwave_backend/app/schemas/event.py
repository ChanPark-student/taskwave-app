from pydantic import BaseModel, Field
from typing import Optional
from datetime import date
from app.models.event import EventType

class EventBase(BaseModel):
    title: Optional[str] = None
    event_type: Optional[EventType] = None
    date: Optional[date] = None
    warning_days: Optional[int] = Field(3, ge=0, le=14, description="경고 시작일 (0-14일)")

class EventCreate(EventBase):
    subject_id: str
    title: str
    event_type: EventType
    date: date

class EventUpdate(EventBase):
    pass

class EventOut(EventBase):
    id: str
    subject_id: str

    model_config = {"from_attributes": True}
