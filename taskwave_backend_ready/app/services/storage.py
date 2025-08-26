
import os
from uuid import uuid4
from pathlib import Path
from typing import BinaryIO
from app.core.config import settings

class StorageService:
    def __init__(self) -> None:
        self.backend = settings.STORAGE_BACKEND
        self.media_root = Path(settings.MEDIA_ROOT).resolve()

    def ensure_dirs(self, *parts: str) -> Path:
        path = self.media_root.joinpath(*parts)
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    def save(self, fileobj: BinaryIO, subdir: str, filename: str) -> tuple[str, str]:
        uid = str(uuid4())
        safe_name = f"{uid}_{filename}"
        dest = self.ensure_dirs(subdir, safe_name)
        with open(dest, "wb") as out:
            out.write(fileobj.read())
        rel = str(dest.relative_to(self.media_root))
        return rel, f"/media/{rel}"
