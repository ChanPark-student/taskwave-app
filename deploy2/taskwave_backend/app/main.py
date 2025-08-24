from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.routers import auth, users, subjects, schedules, materials, uploads
import os
app = FastAPI(title=settings.APP_NAME)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
api_prefix = settings.API_V1_PREFIX
app.include_router(auth.router, prefix=api_prefix, tags=["auth"])
app.include_router(users.router, prefix=api_prefix, tags=["users"])
app.include_router(subjects.router, prefix=api_prefix, tags=["subjects"])
app.include_router(schedules.router, prefix=api_prefix, tags=["schedules"])
app.include_router(materials.router, prefix=api_prefix, tags=["materials"])
app.include_router(uploads.router, prefix=api_prefix, tags=["uploads"])

# Static media
os.makedirs(settings.MEDIA_ROOT, exist_ok=True)

app.mount("/media", StaticFiles(directory=settings.MEDIA_ROOT), name="media")

@app.get("/health")
def health():
    return {"status": "ok"}
