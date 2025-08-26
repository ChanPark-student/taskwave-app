import os
import uuid
from typing import Tuple
from fastapi import UploadFile
from app.core.config import settings

class StorageService:
    def __init__(self):
        self.backend = settings.STORAGE_BACKEND

    async def save_upload(self, file: UploadFile, subdir: str = "uploads") -> Tuple[str, str]:
        if self.backend == "local":
            return await self._save_local(file, subdir)
        elif self.backend == "s3":
            # You can implement S3 here later
            raise NotImplementedError("S3 storage not yet implemented in MVP")
        else:
            raise ValueError("Unknown storage backend")

    async def _save_local(self, file: UploadFile, subdir: str) -> Tuple[str, str]:
        # returns (file_url, abs_path)
        os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
        dest_dir = os.path.join(settings.MEDIA_ROOT, subdir)
        os.makedirs(dest_dir, exist_ok=True)
        ext = os.path.splitext(file.filename or "")[1]
        fname = f"{uuid.uuid4().hex}{ext or ''}"
        abs_path = os.path.join(dest_dir, fname)
        with open(abs_path, "wb") as f:
            content = await file.read()
            f.write(content)
        # For local, public URL is served under /media
        rel_path = os.path.relpath(abs_path, settings.MEDIA_ROOT).replace(os.sep, "/")
        url = f"/media/{rel_path}"


        return url, abs_path
