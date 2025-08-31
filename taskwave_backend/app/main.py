# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

import os
import json
import logging
import sys # Import sys for stderr
from typing import Any, List

from app.core.config import settings
from app.routers.auth import router as auth_router
from app.routers.users import router as users_router
from app.routers.subjects import router as subjects_router
from app.routers.materials import router as materials_router
from app.routers.uploads import router as uploads_router
from app.routers.schedules import router as schedules_router
from app.routers.files import router as files_router
from app.routers.events import router as events_router # 이벤트 라우터 추가
from app.routers import misc
from app.db.session import engine
from app.db.base import Base

app = FastAPI()

# --- 정적 파일 마운트 --- #
try:
    media_path = Path(settings.MEDIA_ROOT)
    media_path.mkdir(parents=True, exist_ok=True)
    app.mount("/media", StaticFiles(directory=media_path), name="media")
except Exception as e:
    print(f"Error creating or mounting media directory: {e}", file=sys.stderr)
    raise # Re-raise to ensure the application doesn't start in a broken state


def _parse_origins(val: Any) -> List[str]:
    origins: List[str] = []
    if not val:
        return origins
    if isinstance(val, (list, tuple)):
        return [str(s).strip() for s in val if str(s).strip()]
    if isinstance(val, str):
        try:
            parsed = json.loads(val)
            if isinstance(parsed, (list, tuple)):
                return [str(s).strip() for s in parsed if str(s).strip()]
            if isinstance(parsed, str):
                s = parsed.strip()
                return [s] if s else []
        except Exception:
            return [s.strip() for s in val.split(",") if s.strip()]
    return [str(val).strip()] if str(val).strip() else []

# ---- CORS allow_origins 구성 ----
origins: List[str] = _parse_origins(getattr(settings, "BACKEND_CORS_ORIGINS", None))
if not origins and os.getenv("FRONTEND_URL"):
    origins = _parse_origins(os.environ["FRONTEND_URL"])
if not origins:
    origins = ["http://localhost:5173", "https://taskwave-app.onrender.com"]
if "https://taskwave-app.onrender.com" not in origins:
    origins.append("https://taskwave-app.onrender.com")

logging.getLogger("uvicorn.error").info("CORS allow_origins=%s", origins)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def _startup_create_tables():
    Base.metadata.create_all(bind=engine)
    
# 라우터
app.include_router(auth_router, prefix="/api")
app.include_router(users_router, prefix="/api")
app.include_router(subjects_router, prefix="/api")
app.include_router(materials_router, prefix="/api")
app.include_router(schedules_router, prefix="/api")
app.include_router(uploads_router, prefix="/api")
app.include_router(files_router, prefix="/api")
app.include_router(events_router, prefix="/api") # 이벤트 라우터 추가
app.include_router(misc.router, prefix="/api")

@app.get("/api/health", tags=["health"])
def health():
    return {"status": "ok"}
