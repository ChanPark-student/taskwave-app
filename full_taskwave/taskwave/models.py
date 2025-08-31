from dataclasses import dataclass
from datetime import time

@dataclass(frozen=True)
class ClassEntry:
    subject: str
    weekday: int  # Monday=0 ... Sunday=6
    start: time
    end: time
