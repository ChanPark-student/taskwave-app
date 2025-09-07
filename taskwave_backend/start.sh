#!/bin/sh
set -e
export PYTHONUNBUFFERED=1
export PYTHONPATH=${PYTHONPATH}:/app

# --- Tesseract 경로 보정 ---
export TESSERACT_CMD="${TESSERACT_CMD:-/usr/bin/tesseract}"
if [ ! -x "$TESSERACT_CMD" ]; then
  if command -v tesseract >/dev/null 2>&1; then
    export TESSERACT_CMD="$(command -v tesseract)"
  fi
fi
echo "[start.sh] Using TESSERACT_CMD=$TESSERACT_CMD"

# --- bcrypt 재설치 (간헐적 import 에러 예방) ---
echo "[start.sh] Reinstalling passlib[bcrypt]..."
pip install --force-reinstall passlib[bcrypt] >/dev/null
echo "[start.sh] passlib[bcrypt] reinstalled."

# --- DATABASE_URL 보정 (psycopg v3 접두어 + sslmode=require) ---
if [ -n "${DATABASE_URL:-}" ]; then
  case "$DATABASE_URL" in
    postgres://*)
      DATABASE_URL="postgresql+psycopg://${DATABASE_URL#postgres://}"
      ;;
    postgresql://*)
      # 이미 +psycopg면 유지
      case "$DATABASE_URL" in
        postgresql+psycopg://*) : ;;
        *) DATABASE_URL="postgresql+psycopg://${DATABASE_URL#postgresql://}" ;;
      esac
      ;;
  esac
  # SSL 보정
  case "$DATABASE_URL" in
    *sslmode=*) : ;;
    *\?*) DATABASE_URL="${DATABASE_URL}&sslmode=require" ;;
    *)    DATABASE_URL="${DATABASE_URL}?sslmode=require" ;;
  esac
  export DATABASE_URL
fi
echo "[start.sh] Using DATABASE_URL=${DATABASE_URL:+(set)}"

# --- DB 준비 대기 ---
echo "[start.sh] Waiting for database to be ready..."
python - <<'PY'
import os, time, sys
from sqlalchemy import create_engine
url = os.environ.get("DATABASE_URL")
if not url:
    print("DATABASE_URL not set", file=sys.stderr); sys.exit(2)
for i in range(40):
    try:
        create_engine(url, pool_pre_ping=True).connect().close()
        print("DB is ready"); sys.exit(0)
    except Exception as e:
        print(f"DB not ready ({i+1}/40): {e}")
        time.sleep(2)
print("DB never became ready", file=sys.stderr); sys.exit(3)
PY

# --- Alembic 버전 테이블 초기 가드 ---
if ! alembic current >/dev/null 2>&1; then
  echo "[alembic] No version table detected. Stamping base..."
  alembic stamp base
fi

# --- 분기(heads) 자동 감지 & 업그레이드 ---
echo "[start.sh] Running database migrations..."
HEADS="$(alembic heads | awk '{print $1}')"
NHEADS="$(printf '%s\n' "$HEADS" | awk 'NF{c++} END{print c+0}')"

if [ "$NHEADS" -gt 1 ]; then
  echo "[alembic] Multiple heads detected: $HEADS"
  echo "[alembic] Upgrading to all heads..."
  alembic upgrade heads
else
  alembic upgrade head
fi
echo "[start.sh] Migrations complete."

# --- 앱 실행 ---
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
