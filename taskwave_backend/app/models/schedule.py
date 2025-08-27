from sqlalchemy import String, Integer, Date, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

class Week(Base):
    __tablename__ = "weeks"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    subject_id: Mapped[str] = mapped_column(ForeignKey("subjects.id"), index=True, nullable=False)
    week_no: Mapped[int] = mapped_column(Integer, nullable=False)
    month: Mapped[int | None] = mapped_column(Integer, nullable=True)

    subject = relationship("Subject", back_populates="weeks")
    sessions = relationship("Session", back_populates="week", cascade="all, delete-orphan")

class Session(Base):
    __tablename__ = "sessions"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    week_id: Mapped[str] = mapped_column(ForeignKey("weeks.id"), index=True, nullable=False)
    date: Mapped[Date] = mapped_column(Date, nullable=False)
    title: Mapped[str | None] = mapped_column(String, nullable=True)
    start_time: Mapped[str] = mapped_column(String, nullable=False)
    end_time: Mapped[str] = mapped_column(String, nullable=False)

    week = relationship("Week", back_populates="sessions")
