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

# bcrypt 재설치 (bcrypt 오류 방지)
echo "[start.sh] Reinstalling passlib[bcrypt]..."
pip install --force-reinstall passlib[bcrypt]
echo "[start.sh] passlib[bcrypt] reinstalled."

# 마이그레이션
echo "[start.sh] Running database migrations..."
# 288fb98f9629 이전 버전으로 다운그레이드하여 깨진 상태를 해결하고, 실패 시 오류를 무시합니다.
alembic downgrade ecdc6627387a || true
# 최신 버전으로 업그레이드합니다.
alembic upgrade head
echo "[start.sh] Migrations complete."

# 앱 실행
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
