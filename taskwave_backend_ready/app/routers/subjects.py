
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.deps import get_db, get_current_user
from app.schemas.subject import SubjectCreate, SubjectOut, WeekOut
from app.models.user import User
from app.models.subject import Subject
from app.models.schedule import Week

router = APIRouter(tags=["subjects"])

@router.get("/subjects", response_model=List[SubjectOut])
def list_subjects(db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    return db.query(Subject).filter(Subject.user_id == current.id).all()

@router.post("/subjects", response_model=SubjectOut, status_code=201)
def create_subject(payload: SubjectCreate, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    s = Subject(title=payload.title, user_id=current.id)
    db.add(s); db.commit(); db.refresh(s)
    for i in range(1, 16):
        db.add(Week(subject_id=s.id, week_index=i))
    db.commit()
    return s

@router.get("/subjects/{subject_id}", response_model=SubjectOut)
def get_subject(subject_id: int, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    s = db.query(Subject).filter(Subject.id == subject_id, Subject.user_id == current.id).first()
    if not s:
        raise HTTPException(404, "Subject not found")
    return s

@router.delete("/subjects/{subject_id}", status_code=204)
def delete_subject(subject_id: int, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    s = db.query(Subject).filter(Subject.id == subject_id, Subject.user_id == current.id).first()
    if not s:
        raise HTTPException(404, "Subject not found")
    db.delete(s); db.commit()
    return None

@router.get("/subjects/{subject_id}/weeks", response_model=List[WeekOut])
def subject_weeks(subject_id: int, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    s = db.query(Subject).filter(Subject.id == subject_id, Subject.user_id == current.id).first()
    if not s:
        raise HTTPException(404, "Subject not found")
    return db.query(Week).filter(Week.subject_id == s.id).order_by(Week.week_index).all()
