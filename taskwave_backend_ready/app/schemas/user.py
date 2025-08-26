
from pydantic import BaseModel, EmailStr

class UserOut(BaseModel):
    id: str
    email: EmailStr
    name: str | None = None
    school: str | None = None
    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    name: str | None = None
    school: str | None = None
