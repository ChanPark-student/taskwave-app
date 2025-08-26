
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.deps import get_db, get_current_user
from app.schemas.subject import SessionOut
from app.models.user import User
from app.models.schedule import Week, Session as SessionModel

router = APIRouter(tags=["schedules"])

@router.get("/weeks/{week_id}/sessions", response_model=List[SessionOut])
def week_sessions(week_id: int, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    w = db.query(Week).join(Week.subject).filter(Week.id == week_id, Week.subject.has(user_id=current.id)).first()
    if not w:
        raise HTTPException(404, "Week not found")
    return w.sessions

@router.get("/schedules/ping")
def ping():
    return {"ok": True}
