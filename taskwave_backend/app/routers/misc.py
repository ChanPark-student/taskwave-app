from fastapi import APIRouter
from datetime import datetime, timezone

router = APIRouter(prefix="/api", tags=["misc"])

@router.get("/ping")
def ping():
    return {"ok": True, "ts": datetime.now(timezone.utc).isoformat()}
