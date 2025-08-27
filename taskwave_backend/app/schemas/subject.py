from pydantic import BaseModel, Field
from datetime import date
from typing import List

class SubjectCreate(BaseModel):
    title: str

class SubjectOut(BaseModel):
    id: str
    title: str
    model_config = {"from_attributes": True}

class WeekCreate(BaseModel):
    week_no: int
    month: int | None = None

class WeekOut(BaseModel):
    id: str
    week_no: int
    month: int | None = None
    model_config = {"from_attributes": True}

class SessionCreate(BaseModel):
    week_id: str
    date: date
    title: str | None = None
    start_time: str
    end_time: str

class SessionOut(BaseModel):
    id: str
    date: date
    title: str | None = None
    start_time: str
    end_time: str
    model_config = {"from_attributes": True}

class ManualSlotIn(BaseModel):
    subject_title: str = Field(..., min_length=1)
    weekday: str
    start_time: str
    end_time: str

class ManualScheduleIn(BaseModel):
    slots: List[ManualSlotIn]

