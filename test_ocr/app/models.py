from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class Slot(BaseModel):
    weekday: str
    start_time: str
    end_time: str
    title: str
    professor: Optional[str] = None
    location: Optional[str] = None
    raw_text: str

class ParseResponse(BaseModel):
    count: int
    slots: List[Slot]
    debug: Dict[str, Any]
