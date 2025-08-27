from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import uuid4
from app.core.deps import get_db, get_current_user
from app.schemas.subject import SubjectCreate, SubjectOut, WeekCreate, WeekOut, SessionCreate, SessionOut
from app.models.user import User
from app.models.subject import Subject
from app.models.schedule import Week, Session as SessionModel

router = APIRouter()

@router.get("/subjects", response_model=list[SubjectOut])
def list_subjects(db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    return db.query(Subject).filter(Subject.user_id == current.id).order_by(Subject.created_at.desc()).all()

@router.post("/subjects", response_model=SubjectOut, status_code=201)
def create_subject(payload: SubjectCreate, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    subj = Subject(id=str(uuid4()), user_id=current.id, title=payload.title)
    db.add(subj)
    db.commit()
    db.refresh(subj)
    return subj

@router.get("/subjects/{subject_id}", response_model=SubjectOut)
def get_subject(subject_id: str, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    subj = db.get(Subject, subject_id)
    if not subj or subj.user_id != current.id:
        raise HTTPException(status_code=404, detail="Subject not found")
    return subj

@router.delete("/subjects/{subject_id}", status_code=204)
def delete_subject(subject_id: str, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    subj = db.get(Subject, subject_id)
    if not subj or subj.user_id != current.id:
        raise HTTPException(status_code=404, detail="Subject not found")
    db.delete(subj)
    db.commit()
    return

# Weeks
@router.post("/subjects/{subject_id}/weeks", response_model=WeekOut, status_code=201)
def create_week(subject_id: str, payload: WeekCreate, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    subj = db.get(Subject, subject_id)
    if not subj or subj.user_id != current.id:
        raise HTTPException(status_code=404, detail="Subject not found")
    week = Week(id=str(uuid4()), subject_id=subject_id, week_no=payload.week_no, month=payload.month)
    db.add(week)
    db.commit()
    db.refresh(week)
    return week

@router.get("/subjects/{subject_id}/weeks", response_model=list[WeekOut])
def list_weeks(subject_id: str, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    subj = db.get(Subject, subject_id)
    if not subj or subj.user_id != current.id:
        raise HTTPException(status_code=404, detail="Subject not found")
    return db.query(Week).filter(Week.subject_id == subject_id).order_by(Week.week_no.asc()).all()

# Sessions (class days)
@router.post("/weeks/{week_id}/sessions", response_model=SessionOut, status_code=201)
def create_session(week_id: str, payload: SessionCreate, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    week = db.get(Week, week_id)
    if not week:
        raise HTTPException(status_code=404, detail="Week not found")
    subj = db.get(Subject, week.subject_id)
    if subj.user_id != current.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    sess = SessionModel(id=str(uuid4()), week_id=week_id, date=payload.date, title=payload.title, start_time=payload.start_time, end_time=payload.end_time)
    db.add(sess)
    db.commit()
    db.refresh(sess)
    return sess

@router.get("/weeks/{week_id}/sessions", response_model=list[SessionOut])
def list_sessions(week_id: str, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    week = db.get(Week, week_id)
    if not week:
        raise HTTPException(status_code=404, detail="Week not found")
    subj = db.get(Subject, week.subject_id)
    if subj.user_id != current.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    return db.query(SessionModel).filter(SessionModel.week_id == week_id).order_by(SessionModel.date.asc()).all()
