from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.deps import get_db, get_current_user
from app.schemas.user import UserOut, UserUpdate
from app.models.user import User

router = APIRouter()

@router.get("/users/me", response_model=UserOut)
def get_me(current: User = Depends(get_current_user)):
    return current

@router.patch("/users/me", response_model=UserOut)
def update_me(payload: UserUpdate, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    if payload.name is not None:
        current.name = payload.name
    if payload.school is not None:
        current.school = payload.school
    if payload.birth is not None:
        current.birth = payload.birth
    db.add(current)
    db.commit()
    db.refresh(current)
    return current
