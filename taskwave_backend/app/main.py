# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# ✅ routers 서브패키지에서 상대 임포트
from app.routers.auth import router as auth_router
from app.routers.users import router as users_router
from app.routers.subjects import router as subjects_router
from app.routers.materials import router as materials_router
from app.routers.uploads import router as uploads_router
from app.routers.schedules import router as schedules_router
from app.routers import misc  # 이미 있는 라우터들과 함께

app = FastAPI()

# ---- CORS from env ----
origins = []

# .env에 BACKEND_CORS_ORIGINS가 있을 때(쉼표 or JSON 배열 모두 지원)
val = getattr(settings, "BACKEND_CORS_ORIGINS", None)
if val:
    if isinstance(val, str):
        try:
            # JSON 배열 ["https://a","https://b"] 형태
            origins = [s.strip() for s in json.loads(val)]
        except Exception:
            # 쉼표 구분 "https://a,https://b" 형태
            origins = [s.strip() for s in val.split(",") if s.strip()]
elif "FRONTEND_URL" in os.environ:
    origins = [os.environ["FRONTEND_URL"]]

# 기본값(없다면 모두 허용보다는 최소 한 개라도 넣는 게 안전)
if not origins:
    origins = ["http://localhost:5173"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ⚠️ 라우터 안에 이미 prefix="/auth" 등 개별 prefix가 있다면,
# 여기서는 공통으로 "/api"만 한 번 붙이면 됩니다. (/api/auth, /api/users 등)
app.include_router(auth_router, prefix="/api")
app.include_router(users_router, prefix="/api")
app.include_router(subjects_router, prefix="/api")
app.include_router(materials_router, prefix="/api")
app.include_router(schedules_router, prefix="/api")
app.include_router(uploads_router, prefix="/api")

@app.get("/api/health")
def health():
    return {"status": "ok"}
