
from fastapi import APIRouter
from datetime import datetime, timezone

router = APIRouter(tags=["misc"])

@router.get("/health")
def health():
    return {"status": "ok"}

@router.get("/ping")
def ping():
    return {"ok": True, "ts": datetime.now(timezone.utc).isoformat()}
