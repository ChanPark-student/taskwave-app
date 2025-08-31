from __future__ import annotations
from datetime import time
from typing import List
from .models import ClassEntry
from .config import WEEKDAY_KO_TO_INT

def _parse_time(hhmm: str) -> time:
    s = hhmm.strip()
    if ":" in s:
        hh, mm = s.split(":", 1)
    else:
        if len(s) not in (3,4):
            raise ValueError(f"Invalid time: {hhmm}")
        if len(s) == 3:
            hh, mm = s[0], s[1:]
        else:
            hh, mm = s[:2], s[2:]
    hh_i = int(hh); mm_i = int(mm)
    if not (0 <= hh_i <= 23 and 0 <= mm_i <= 59):
        raise ValueError(f"Invalid time range: {hhmm}")
    return time(hour=hh_i, minute=mm_i)

def parse_manual_entries(text_block: str) -> List[ClassEntry]:
    entries = []
    for raw in text_block.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = [p.strip() for p in line.split(",")]
        if len(parts) != 3:
            raise ValueError(f"Line should have 3 comma-separated fields: {line}")
        subject, day_ko, tspan = parts
        if day_ko not in WEEKDAY_KO_TO_INT:
            raise ValueError(f"Unknown weekday (KO): {day_ko}")
        weekday = WEEKDAY_KO_TO_INT[day_ko]
        if "-" not in tspan:
            raise ValueError(f"Time span must be 'start-end': {tspan}")
        s_str, e_str = [p.strip() for p in tspan.split("-", 1)]
        start = _parse_time(s_str); end = _parse_time(e_str)
        if (end.hour, end.minute) <= (start.hour, start.minute):
            raise ValueError(f"End must be after start: {tspan}")
        entries.append(ClassEntry(subject=subject, weekday=weekday, start=start, end=end))
    return entries

