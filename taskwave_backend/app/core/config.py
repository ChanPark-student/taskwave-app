from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import List
import json
import os # Import os
from pathlib import Path

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "Taskwave API"
    ENV: str = "dev"
    API_V1_PREFIX: str = "/api"

    # DB
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./taskwave.db")

    # Security
    SECRET_KEY: str = "change-me"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    ALGORITHM: str = "HS256"

    # CORS (JSON 배열 또는 콤마 문자열 모두 허용)
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors(cls, v):
        if v is None or (isinstance(v, str) and v.strip() == ""):
            return ["http://localhost:3000"]
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            s = v.strip()
            if s.startswith("["):
                try:
                    arr = json.loads(s)
                    return [x.strip() for x in arr if isinstance(x, str) and x.strip()]
                except Exception:
                    pass
            return [x.strip() for x in s.split(",") if x.strip()]
        return v

    # Storage
    STORAGE_BACKEND: str = "local"   # "local" 또는 "s3"
    MEDIA_ROOT: str = str(Path(__file__).parent.parent.parent / "media")

    # (선택) S3 전환용
    S3_BUCKET: str | None = None
    S3_REGION: str | None = None
    AWS_ACCESS_KEY_ID: str | None = None
    AWS_SECRET_ACCESS_KEY: str | None = None
    S3_BASE_URL: str | None = None
    TESSERACT_CMD: str | None = None
    TESSDATA_PREFIX: str | None = None

settings = Settings()
