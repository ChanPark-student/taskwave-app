
from pydantic import BaseModel

class MaterialOut(BaseModel):
    id: int
    subject_id: int
    filename: str
    storage_path: str
    content_type: str | None = None
    size_bytes: int | None = None
    class Config:
        from_attributes = True
