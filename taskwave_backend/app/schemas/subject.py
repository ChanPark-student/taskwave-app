from pydantic import BaseModel, Field, model_validator
from datetime import date, time
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
    start_time: time
    end_time: time
    title: str | None = None

class SessionOut(BaseModel):
    id: str
    date: date
    start_time: time
    end_time: time
    title: str | None = None
    model_config = {"from_attributes": True}

class ManualSlotIn(BaseModel):
    subject_title: str = Field(..., min_length=1)
    weekday: str
    start_time: str # "HH:MM"
    end_time: str   # "HH:MM"

class ManualScheduleIn(BaseModel):
    slots: List[ManualSlotIn]

    @model_validator(mode='after')
    def check_times_in_slots(self) -> 'ManualScheduleIn':
        for slot in self.slots:
            if time.fromisoformat(slot.start_time) >= time.fromisoformat(slot.end_time):
                raise ValueError(f"Slot for '{slot.subject_title}' has end_time before or same as start_time.")
        return self

# API: GET /schedules/week-view 를 위한 응답 스키마
class SessionForWeekView(BaseModel):
    subject_title: str
    session_id: str
    day_of_week: str  # 예: "월", "화"
    start_time: time
    end_time: time
    color: str | None = "#4A90E2" # 과목별 색상 (향후 구현)

    model_config = {"from_attributes": True}

# API: POST /schedules/recurring 를 위한 입력 스키마
class RecurringScheduleIn(BaseModel):
    title: str = Field(..., min_length=1, description="일정의 이름 (예: 알고리즘 스터디)")
    start_date: date
    end_date: date
    start_time: time
    end_time: time
    weekdays: List[str] = Field(..., min_length=1, description='반복할 요일 목록 (예: ["월", "수"])')

    @model_validator(mode='after')
    def validate_dates_and_times(self) -> 'RecurringScheduleIn':
        if self.start_date > self.end_date:
            raise ValueError("시작 날짜는 종료 날짜보다 이전이어야 합니다.")
        if self.start_time >= self.end_time:
            raise ValueError("시작 시간은 종료 시간보다 이전이어야 합니다.")
        
        valid_weekdays = {"월", "화", "수", "목", "금", "토", "일"}
        for day in self.weekdays:
            if day not in valid_weekdays:
                raise ValueError(f"'{day}'는 유효한 요일이 아닙니다. (월, 화, 수, 목, 금, 토, 일 중 선택)")
        return self
