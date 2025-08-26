from pydantic import BaseModel, AnyUrl

class MaterialCreate(BaseModel):
    subject_id: str
    week_id: str | None = None
    session_id: str | None = None
    name: str | None = None

class MaterialOut(BaseModel):
    id: str
    name: str
    file_url: str
    mime_type: str
    size_bytes: int | None = None
    model_config = {"from_attributes": True}
