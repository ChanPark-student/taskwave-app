# app/schemas/auth.py
from pydantic import BaseModel, EmailStr
from typing import Optional

class SignUpIn(BaseModel):
    email: EmailStr
    password: str
    name: Optional[str] = None   # ← 선택값

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class TokenPair(BaseModel):
    access_token: str
    token_type: str = "bearer"   # ← 기본값으로 검증 통과
