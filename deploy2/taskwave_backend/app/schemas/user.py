from pydantic import BaseModel, EmailStr
from uuid import UUID

class UserOut(BaseModel):
    id: str | None = None 
    email: EmailStr
    name: str | None = None 
    school: str | None = None
    birth: str | None = None

    model_config = {"from_attributes": True}

class UserUpdate(BaseModel):
    name: str | None = None
    school: str | None = None
    birth: str | None = None
