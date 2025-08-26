
from pydantic import BaseModel
from datetime import datetime

class SubjectCreate(BaseModel):
    title: str

class SubjectOut(BaseModel):
    id: int
    title: str
    class Config:
        from_attributes = True

class WeekOut(BaseModel):
    id: int
    subject_id: int
    week_index: int
    class Config:
        from_attributes = True

class SessionOut(BaseModel):
    id: int
    week_id: int
    title: str
    starts_at: datetime | None = None
    note: str | None = None
    class Config:
        from_attributes = True
