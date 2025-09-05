from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.orm import Session
from uuid import uuid4
from typing import Optional
from datetime import datetime
from app.core.deps import get_db, get_current_user
from app.schemas.material import MaterialOut
from app.models.user import User
from app.models.subject import Subject
from app.models.schedule import Week, Session as SessionModel
from app.models.material import Material
from app.services.storage import StorageService
import os

router = APIRouter()

@router.post("/materials/upload", response_model=MaterialOut, status_code=201)
async def upload_material(
    file: UploadFile = File(...),
    subject_id: str = Form(...),
    date: Optional[str] = Form(None),
    name: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    subj = db.get(Subject, subject_id)
    if not subj or subj.user_id != current.id:
        raise HTTPException(status_code=404, detail="Subject not found")

    # Parse date if provided
    parsed_date = None
    if date:
        try:
            parsed_date = datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")

    storage = StorageService()
    file_url, abs_path = await storage.save_upload(file, subdir="materials")

    mat = Material(
        id=str(uuid4()),
        owner_id=current.id,
        subject_id=subject_id,
        week_id=None,
        session_id=None,
        date=parsed_date,
        name=name or (file.filename or "file"),
        mime_type=file.content_type or "application/octet-stream",
        file_url=file_url,
        size_bytes=os.path.getsize(abs_path) if abs_path else None,
    )
    db.add(mat)
    db.commit()
    db.refresh(mat)
    return mat

@router.get("/subjects/{subject_id}/materials", response_model=list[MaterialOut])
def list_materials(
    subject_id: str,
    week_id: Optional[str] = Query(None),
    session_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    subj = db.get(Subject, subject_id)
    if not subj or subj.user_id != current.id:
        raise HTTPException(status_code=404, detail="Subject not found")

    q = db.query(Material).filter(Material.subject_id == subject_id, Material.owner_id == current.id)
    if week_id:
        q = q.filter(Material.week_id == week_id)
    if session_id:
        q = q.filter(Material.session_id == session_id)
    return q.order_by(Material.created_at.desc()).all()

@router.delete("/materials/{material_id}", status_code=204)
def delete_material(material_id: str, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    mat = db.get(Material, material_id)
    if not mat or mat.owner_id != current.id:
        raise HTTPException(status_code=404, detail="Material not found")
    db.delete(mat)
    db.commit()
    return
