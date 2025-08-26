#!/bin/sh
set -e
alembic upgrade head || echo "alembic not configured or failed; continuing..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
