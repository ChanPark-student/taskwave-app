# database.py
import os
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from dotenv import load_dotenv  # 로컬 테스트용

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("환경변수 DATABASE_URL이 설정되어 있지 않습니다.")
engine = create_async_engine(DATABASE_URL, echo=True)

async_session_factory = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession,
)

Base = declarative_base()


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session

# demopj/database.py
import os
from urllib.parse import urlparse, urlunparse

ASYNC_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://demopj_db_user:Yxna31Ay2hZRHZLrLyvut5ZVj8pXuhdr@dpg-d1ihop6r433s73alcc90-a/demopj_db"
)

# 동기용 URL로 변환
parsed = urlparse(ASYNC_DATABASE_URL)
SYNC_DATABASE_URL = urlunparse(parsed._replace(scheme="postgresql+psycopg2"))