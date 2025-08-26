
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import List
import json

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    APP_NAME: str = "Taskwave API"
    ENV: str = "dev"
    API_V1_PREFIX: str = "/api"
    DATABASE_URL: str = "sqlite:///./taskwave.db"
    SECRET_KEY: str = "change-me"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    CORS_ORIGINS: List[str] = []
    STORAGE_BACKEND: str = "local"
    MEDIA_ROOT: str = "./media"
    S3_BUCKET: str | None = None
    S3_REGION: str | None = None
    AWS_ACCESS_KEY_ID: str | None = None
    AWS_SECRET_ACCESS_KEY: str | None = None
    S3_BASE_URL: str | None = None

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors(cls, v):
        if v is None: return []
        if isinstance(v, list): return v
        s = str(v).strip()
        if not s: return []
        if s.startswith("["):
            try: return json.loads(s)
            except Exception: pass
        return [x.strip() for x in s.split(",") if x.strip()]

settings = Settings()
