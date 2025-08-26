import os
import sys
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

# === PYTHONPATH 보정: /app 추가 (컨테이너에서 /app/app 가 패키지 루트) ===
BASE_DIR = Path(__file__).resolve().parents[1]  # /app
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

config = context.config

# === psycopg(v3) 드라이버 사용하도록 URL 정규화 ===
def _normalize_url(url: str) -> str:
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg://", 1)
    if url.startswith("postgresql://") and "+psycopg" not in url:
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url

# 모델 메타데이터
try:
    from app.db.base import Base  # noqa
    target_metadata = Base.metadata
except Exception:
    target_metadata = None

def run_migrations_offline() -> None:
    url = _normalize_url(os.getenv("DATABASE_URL", "sqlite:///./taskwave.db"))
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    cfg = config.get_section(config.config_ini_section) or {}
    url_env = _normalize_url(os.getenv("DATABASE_URL", "sqlite:///./taskwave.db"))
    cfg["sqlalchemy.url"] = url_env

    connectable = engine_from_config(
        cfg,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
