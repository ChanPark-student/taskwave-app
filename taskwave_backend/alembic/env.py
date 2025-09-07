import os
import sys
from pathlib import Path
from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool

# --- Alembic Config 객체 ---
config = context.config

# --- /app 를 PYTHONPATH에 추가 (컨테이너 기준) ---
BASE_DIR = Path(__file__).resolve().parents[1]  # /app
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# --- 로깅 설정 (alembic.ini가 있으면 적용) ---
if config.config_file_name:
    fileConfig(config.config_file_name)

# --- 모델 메타데이터 (Autogenerate용) ---
try:
    from app.db.base import Base  # 모델이 여기서 import 가능해야 한다
    target_metadata = Base.metadata
except Exception:
    target_metadata = None

# --- DB URL 보정: psycopg v3 접두어 + sslmode=require ---
def _normalize_url(url: str) -> str:
    if url.startswith("postgres://"):
        url = "postgresql+psycopg://" + url[len("postgres://"):]
    elif url.startswith("postgresql://") and "+psycopg" not in url:
        url = "postgresql+psycopg://" + url[len("postgresql://"):]
    if url.startswith("postgresql+psycopg://") and "sslmode=" not in url:
        url += ("&" if "?" in url else "?") + "sslmode=require"
    return url

def get_url() -> str:
    env_url = os.getenv("DATABASE_URL")
    if env_url:
        return _normalize_url(env_url)
    # 로컬/기본값 (sqlite)
    return "sqlite:///./taskwave.db"

# --- Offline Migrations ---
def run_migrations_offline() -> None:
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()

# --- Online Migrations ---
def run_migrations_online() -> None:
    url = get_url()
    connectable = create_engine(url, poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()

# --- 진입점 ---
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
