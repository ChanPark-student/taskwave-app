from pydantic import BaseModel, Field
from typing import Optional

class WebParseRequest(BaseModel):
    url: str
    mode: str = Field(default="css", description="auto | kor | dom | text | css")
    start_hour: int | None = 9
    px_per_30: float | None = 40.33
    top_offset: float | None = 540.0
    head_selector: str | None = ".tablehead td,.fc-col-header th,.header td,thead th,.days td,.fc-col-header-cell,.rbc-time-header,.tui-full-calendar-dayname"
    body_selector: str | None = ".tablebody,.fc-timegrid,.timetable,.timeTable,.schedule-body,.weekly-schedule,.calendar,.fc-scroller-harness,.rbc-time-content,.rbc-time-view,.tui-full-calendar-timegrid-container,.timeGrid,.schedule"
    block_selector: str | None = ".subject,.fc-timegrid-event,.fc-event,.lesson,.class,.event,.lecture,.rbc-event,.tui-full-calendar-time-schedule,[data-event],[class*='event']"
    interactive_login: bool = False
    wait_login_seconds: int | None = 120

class WebDiagnoseRequest(BaseModel):
    url: str
    max_samples: int | None = 20
    for_mode: str | None = "auto"