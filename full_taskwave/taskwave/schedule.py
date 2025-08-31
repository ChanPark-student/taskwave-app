from __future__ import annotations
from typing import Iterable, Iterator, Set, Tuple
from datetime import date, timedelta
from .models import ClassEntry

def _daterange(start: date, end: date) -> Iterator[date]:
    cur = start
    while cur <= end:
        yield cur
        cur += timedelta(days=1)

def generate_class_dates(
    entries: Iterable[ClassEntry],
    start_date: date,
    end_date: date,
    holidays: Set[date] | None = None,
) -> Iterator[Tuple[ClassEntry, date]]:
    holidays = holidays or set()
    for d in _daterange(start_date, end_date):
        for e in entries:
            if d.weekday() == e.weekday and d not in holidays:
                yield (e, d)
