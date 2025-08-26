# app/models/upload.py
from __future__ import annotations

import uuid
from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.sql import func
from app.db.base import Base

class Upload(Base):
    __tablename__ = "uploads"

    # UUID 문자열 PK
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # 업로더(유저) 식별자 — users.id 타입과 맞추세요(현재 String/UUID 문자열로 운용 중)
    user_id = Column(String, nullable=False, index=True)

    # 파일 메타
    filename = Column(String(255), nullable=False)
    content_type = Column(String(100), nullable=True)
    storage_path = Column(String(500), nullable=False)  # MEDIA_ROOT 기준 상대 경로
    size = Column(Integer, nullable=True)               # 바이트

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self) -> str:
        return f"<Upload id={self.id} filename={self.filename}>"
