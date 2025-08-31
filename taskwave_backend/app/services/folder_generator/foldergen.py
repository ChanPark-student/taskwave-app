from __future__ import annotations
import os, io, zipfile
from typing import Iterable, Callable, Tuple
from datetime import date
from .models import ClassEntry
from .config import WEEKDAY_INT_TO_KO

def default_namer(entry: ClassEntry, d: date) -> str:
    yyyy = f"{d.year:04d}"; mm = f"{d.month:02d}"; dd = f"{d.day:02d}"
    weekday_ko = WEEKDAY_INT_TO_KO[entry.weekday]
    return os.path.join(yyyy, f"{mm}{dd}_{weekday_ko}_{entry.subject}")

def build_zip_bytes(
    class_dates: Iterable[Tuple[ClassEntry, date]],
    namer: Callable[[ClassEntry, date], str] = default_namer,
    write_meta: bool = True
) -> bytes:
    mem = io.BytesIO()
    with zipfile.ZipFile(mem, "w", zipfile.ZIP_DEFLATED) as z:
        for entry, d in class_dates:
            rel = namer(entry, d).replace("\", "/").strip("/")
            if not rel: 
                continue
            z.writestr(f"{rel}/.keep", "")
            if write_meta:
                meta = (
                    f"subject: {entry.subject}\n"
                    f"weekday: {entry.weekday}\n"
                    f"date: {d.isoformat()}\n"
                    f"start: {entry.start.strftime('%H:%M')}\n"
                    f"end: {entry.end.strftime('%H:%M')}\n"
                )
                z.writestr(f"{rel}/_meta.txt", meta)
    mem.seek(0)
    return mem.getvalue()

