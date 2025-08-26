#!/bin/sh
set -e

# Tesseract 경로 보정 (Render env, Docker ENV 모두 커버)
export TESSERACT_CMD="${TESSERACT_CMD:-/usr/bin/tesseract}"
if [ ! -x "$TESSERACT_CMD" ]; then
  if command -v tesseract >/dev/null 2>&1; then
    export TESSERACT_CMD="$(command -v tesseract)"
  fi
fi
echo "[start.sh] Using TESSERACT_CMD=$TESSERACT_CMD"

# 마이그레이션 (실패해도 서비스 계속)
alembic upgrade head || echo "alembic not configured or failed; continuing..."

# 앱 실행
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
