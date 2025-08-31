from sqlalchemy import String, Integer, Date, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
import enum

class EventType(enum.Enum):
    EXAM = "exam"
    ASSIGNMENT = "assignment"

class Event(Base):
    __tablename__ = "events"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    subject_id: Mapped[str] = mapped_column(ForeignKey("subjects.id"), index=True, nullable=False)
    
    title: Mapped[str] = mapped_column(String, nullable=False)
    event_type: Mapped[EventType] = mapped_column(Enum(EventType), nullable=False)
    date: Mapped[Date] = mapped_column(Date, nullable=False)
    warning_days: Mapped[int] = mapped_column(Integer, default=3, nullable=False)

    subject = relationship("Subject")
