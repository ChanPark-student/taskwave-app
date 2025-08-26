from uuid import uuid4
from sqlalchemy import Column, String, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from sqlalchemy.orm import synonym

class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    school: Mapped[str | None] = mapped_column(String, nullable=True)
    birth: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())

    subjects = relationship("Subject", back_populates="user", cascade="all, delete")
    materials = relationship("Material", back_populates="owner")
    password_hash = synonym("hashed_password")
    hashed_password = Column(String, nullable=True)
