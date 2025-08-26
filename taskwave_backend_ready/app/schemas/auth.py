
from pydantic import BaseModel, EmailStr
from typing import Optional

class SignUpIn(BaseModel):
    email: EmailStr
    password: str
    name: Optional[str] = None

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class TokenPair(BaseModel):
    access_token: str
    token_type: str = "bearer"
