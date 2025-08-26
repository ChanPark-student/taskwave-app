
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.core.config import settings
from app.routers.auth import router as auth_router
from app.routers.users import router as users_router
from app.routers.subjects import router as subjects_router
from app.routers.materials import router as materials_router
from app.routers.uploads import router as uploads_router
from app.routers.schedules import router as schedules_router
from app.routers.misc import router as misc_router
import os

app = FastAPI(title=settings.APP_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS or (["*"] if settings.ENV != "prod" else []),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

media_root = os.path.abspath(settings.MEDIA_ROOT)
os.makedirs(media_root, exist_ok=True)
app.mount("/media", StaticFiles(directory=media_root), name="media")

prefix = settings.API_V1_PREFIX.rstrip("/")
app.include_router(auth_router, prefix=prefix)
app.include_router(users_router, prefix=prefix)
app.include_router(subjects_router, prefix=prefix)
app.include_router(materials_router, prefix=prefix)
app.include_router(uploads_router, prefix=prefix)
app.include_router(schedules_router, prefix=prefix)
app.include_router(misc_router, prefix=prefix)
