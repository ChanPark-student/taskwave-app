
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, ForeignKey, DateTime, Text
from app.db.base import Base

class Week(Base):
    __tablename__ = "weeks"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    subject_id: Mapped[int] = mapped_column(Integer, ForeignKey("subjects.id", ondelete="CASCADE"))
    week_index: Mapped[int] = mapped_column(Integer, nullable=False)
    subject = relationship("Subject", back_populates="weeks")
    sessions = relationship("Session", back_populates="week", cascade="all, delete-orphan")

class Session(Base):
    __tablename__ = "sessions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    week_id: Mapped[int] = mapped_column(Integer, ForeignKey("weeks.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String, nullable=False)
    starts_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    week = relationship("Week", back_populates="sessions")
