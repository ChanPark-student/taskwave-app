from pydantic import BaseModel
from datetime import date

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

class SessionOut(BaseModel):
    id: str
    date: date
    title: str | None = None
    model_config = {"from_attributes": True}
