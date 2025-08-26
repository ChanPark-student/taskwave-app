
from pydantic import BaseModel

class TimetableUploadOut(BaseModel):
    id: str
    file_url: str
    status: str
    message: str | None = None
    class Config:
        from_attributes = True
