from sqlalchemy import String, Integer, Date, ForeignKey, Time
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
    title: Mapped[str | None] = mapped_column(String)
    # 참고: TIME 타입은 타임존 정보를 포함하지 않음. 클라이언트가 보낸 시각 그대로 저장.
    start_time: Mapped[Time] = mapped_column(Time, nullable=False)
    end_time: Mapped[Time] = mapped_column(Time, nullable=False)

    week = relationship("Week", back_populates="sessions")
