# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import os
import json
import logging
from typing import Any, List

from app.core.config import settings
from app.routers.auth import router as auth_router
from app.routers.users import router as users_router
from app.routers.subjects import router as subjects_router
from app.routers.materials import router as materials_router
from app.routers.uploads import router as uploads_router
from app.routers.schedules import router as schedules_router
from app.routers.files import router as files_router  # 추가
from app.routers import misc  # misc.router 사용
from app.db.session import engine
from app.db.base import Base
app = FastAPI()


def _parse_origins(val: Any) -> List[str]:
    """
    BACKEND_CORS_ORIGINS를 유연하게 파싱:
    - 리스트/튜플 그대로
    - JSON 문자열  '["https://a","https://b"]'
    - 콤마 문자열  'https://a,https://b'
    - 단일 문자열  'https://a'
    """
    origins: List[str] = []
    if not val:
        return origins

    if isinstance(val, (list, tuple)):
        origins = [str(s).strip() for s in val if str(s).strip()]
        return origins

    if isinstance(val, str):
        # JSON 배열 시도
        try:
            parsed = json.loads(val)
            if isinstance(parsed, (list, tuple)):
                return [str(s).strip() for s in parsed if str(s).strip()]
            if isinstance(parsed, str):
                s = parsed.strip()
                return [s] if s else []
        except Exception:
            # 콤마 구분
            return [s.strip() for s in val.split(",") if s.strip()]

    # 기타 타입 방어
    return [str(val).strip()] if str(val).strip() else []


# ---- CORS allow_origins 구성 ----
origins: List[str] = _parse_origins(getattr(settings, "BACKEND_CORS_ORIGINS", None))

# FRONTEND_URL 단일 값도 허용
if not origins and os.getenv("FRONTEND_URL"):
    origins = _parse_origins(os.environ["FRONTEND_URL"])

# 기본값(개발 환경)
if not origins:
    origins = ["http://localhost:5173", "https://taskwave-app.onrender.com"]

# Add the deployed frontend URL for convenience
if "https://taskwave-app.onrender.com" not in origins:
    origins.append("https://taskwave-app.onrender.com")

logging.getLogger("uvicorn.error").info("CORS allow_origins=%s", origins)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,   # 크리덴셜 필요 시 True (와일드카드 '*' 불가)
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def _startup_create_tables():
    # alembic이 실패하더라도 최소한 필요한 테이블은 생성
    Base.metadata.create_all(bind=engine)
    
# 라우터: 각 라우터 안에 /auth 등 개별 prefix가 이미 있으므로 여기서는 공통 "/api"만
app.include_router(auth_router, prefix="/api")
app.include_router(users_router, prefix="/api")
app.include_router(subjects_router, prefix="/api")
app.include_router(materials_router, prefix="/api")
app.include_router(schedules_router, prefix="/api")
app.include_router(uploads_router, prefix="/api")
app.include_router(files_router, prefix="/api")  # 추가
app.include_router(misc.router, prefix="/api")

@app.get("/api/health", tags=["health"])
def health():
    return {"status": "ok"}
