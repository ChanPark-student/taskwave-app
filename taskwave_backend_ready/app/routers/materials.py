from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List
import io
from app.core.deps import get_db, get_current_user
from app.schemas.material import MaterialOut
from app.models.user import User
from app.models.subject import Subject
from app.models.material import Material
from app.services.storage import StorageService

router = APIRouter(tags=["materials"])
storage = StorageService()

@router.post("/materials/upload", response_model=MaterialOut, status_code=201)
async def upload_material(
    subject_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    subj = db.query(Subject).filter(Subject.id == subject_id, Subject.user_id == current.id).first()
    if not subj:
        raise HTTPException(404, "Subject not found")
    contents = await file.read()
    path, url = storage.save(io.BytesIO(contents), "materials", file.filename)
    m = Material(
        subject_id=subj.id,
        filename=file.filename,
        storage_path=path,
        content_type=file.content_type or None,
        size_bytes=len(contents),
    )
    db.add(m)
    db.commit()
    db.refresh(m)
    return m

@router.get("/subjects/{subject_id}/materials", response_model=List[MaterialOut])
def list_materials(
    subject_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    subj = db.query(Subject).filter(Subject.id == subject_id, Subject.user_id == current.id).first()
    if not subj:
        raise HTTPException(404, "Subject not found")
    return db.query(Material).filter(Material.subject_id == subj.id).order_by(Material.id.desc()).all()

@router.get("/materials/{material_id}", response_model=MaterialOut)
def get_material(
    material_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    m = (
        db.query(Material)
        .join(Material.subject)
        .filter(Material.id == material_id, Material.subject.has(user_id=current.id))
        .first()
    )
    if not m:
        raise HTTPException(404, "Material not found")
    return m

@router.delete("/materials/{material_id}", status_code=204)
def delete_material(
    material_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    m = (
        db.query(Material)
        .join(Material.subject)
        .filter(Material.id == material_id, Material.subject.has(user_id=current.id))
        .first()
    )
    if not m:
        raise HTTPException(404, "Material not found")
    db.delete(m)
    db.commit()
    return None
