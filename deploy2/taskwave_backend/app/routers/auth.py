from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import uuid4
from app.core.deps import get_db
from app.schemas.auth import SignUpIn, LoginIn, TokenPair
from app.models.user import User
from app.core.security import pwd_context, create_access_token   # ✅ 이것만 가져오면 됨

router = APIRouter()

@router.post("/auth/login", response_model=TokenPair)
def login(payload: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if not user or not pwd_context.verify(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    access = create_access_token({"sub": str(user.id)})
    return TokenPair(access_token=access, token_type="bearer")  # ✅

@router.post("/auth/signup", response_model=TokenPair, status_code=201)
def signup(payload: SignUpIn, db: Session = Depends(get_db)):
    email = payload.email.lower().strip()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    name = (payload.name or email.split("@")[0]).strip()
    user = User(email=email, name=name, hashed_password=pwd_context.hash(payload.password))
    db.add(user); db.commit(); db.refresh(user)

    access = create_access_token({"sub": str(user.id)})
    return TokenPair(access_token=access, token_type="bearer")  # ✅


