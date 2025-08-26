# Optional: placeholder router if you want a flat schedule list later.
from fastapi import APIRouter

router = APIRouter()

@router.get("/schedules/ping")
def ping():
    return {"ok": True}
