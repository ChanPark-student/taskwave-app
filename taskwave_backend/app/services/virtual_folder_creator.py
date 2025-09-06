from sqlalchemy.orm import Session
from app.models.subject import Subject
from app.models.material import Material
from app.models.user import User
from typing import List, Dict
from uuid import uuid4
from datetime import date, datetime, timedelta

WEEKDAY_MAP = {
    "월": 0, "화": 1, "수": 2, "목": 3, "금": 4, "토": 5, "일": 6
}

async def create_virtual_folders_from_timetable_entries(
    entries: List[Dict],
    db: Session,
    user: User
):
    for entry in entries:
        # Find or create Subject
        subject = db.query(Subject).filter(Subject.title == entry['subject'], Subject.user_id == user.id).first()
        if not subject:
            subject = Subject(
                id=str(uuid4()),
                owner_id=user.id,
                title=entry['subject'],
                color="#CCCCCC" # Default color
            )
            db.add(subject)
            db.flush() # Flush to get subject.id

        # Date calculation
        today = date.today()
        # Get integer representation of weekday from the entry
        entry_weekday_int = WEEKDAY_MAP.get(entry['weekday_ko'], -1)
        if entry_weekday_int == -1:
            # Handle unknown weekday, maybe skip or log error
            continue

        # Find the next occurrence of the weekday
        days_until_weekday = (entry_weekday_int - today.weekday() + 7) % 7
        material_date = today + timedelta(days=days_until_weekday)

        material = Material(
            id=str(uuid4()),
            owner_id=user.id,
            subject_id=subject.id,
            date=material_date,
            name=f"{entry['start']}-{entry['end']} {entry['subject']}", # Name of the virtual file
            mime_type="application/x-virtual-folder", # Custom mime type for virtual items
            file_url="", # No actual file URL
            file_path="" # No actual file path
        )
        db.add(material)
    db.commit()