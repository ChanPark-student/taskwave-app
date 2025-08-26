from pydantic import BaseModel

class TimetableUploadOut(BaseModel):
    id: str
    file_url: str
    status: str
    message: str | None = None
    model_config = {"from_attributes": True}
