from pydantic import BaseModel, Field
from datetime import date
from app.models.event import EventType

class EventBase(BaseModel):
    title: str | None = None
    event_type: EventType | None = None
    date: date | None = None
    warning_days: int | None = Field(3, ge=0, le=14, description="경고 시작일 (0-14일)")

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
