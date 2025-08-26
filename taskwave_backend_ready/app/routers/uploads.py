
import io
from uuid import uuid4
from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session
from app.core.deps import get_db, get_current_user
from app.schemas.upload import TimetableUploadOut
from app.models.user import User
from app.models.upload import Upload
from app.services.storage import StorageService

router = APIRouter(tags=["timetable"])
storage = StorageService()

@router.post("/timetable/upload", response_model=TimetableUploadOut, status_code=201)
async def upload_timetable(file: UploadFile = File(...), db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    data = await file.read()
    storage_path, public_url = storage.save(io.BytesIO(data), "timetables", file.filename)
    uid = str(uuid4())
    rec = Upload(id=uid, user_id=current.id, filename=file.filename, content_type=file.content_type or None, storage_path=storage_path, size=len(data))
    db.add(rec); db.commit()
    return TimetableUploadOut(id=uid, file_url=public_url, status="received", message="Stored successfully")
