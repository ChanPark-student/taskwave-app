
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.deps import get_db
from app.schemas.auth import SignUpIn, LoginIn, TokenPair
from app.models.user import User
from app.core.security import hash_password, verify_password, create_access_token

router = APIRouter(tags=["auth"])

@router.post("/auth/signup", response_model=TokenPair)
def signup(payload: SignUpIn, db: Session = Depends(get_db)):
    email = payload.email.lower()
    exists = db.query(User).filter(User.email == email).first()
    if exists:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(email=email, password_hash=hash_password(payload.password), name=payload.name)
    db.add(user); db.commit(); db.refresh(user)
    token = create_access_token(user.id)
    return TokenPair(access_token=token)

@router.post("/auth/login", response_model=TokenPair)
def login(payload: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token(user.id)
    return TokenPair(access_token=token)
