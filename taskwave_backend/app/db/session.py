# taskwave_backend/app/db/session.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

def _normalize_db_url(url: str) -> str:
    # Render/Heroku 스타일 'postgres://' -> SQLAlchemy 표준 + psycopg v3 드라이버
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg://", 1)
    if url.startswith("postgresql://") and "+psycopg" not in url:
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./taskwave.db")
DATABASE_URL = _normalize_db_url(DATABASE_URL)

# sqlite일 때만 특수 connect_args가 필요
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    connect_args=connect_args,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
