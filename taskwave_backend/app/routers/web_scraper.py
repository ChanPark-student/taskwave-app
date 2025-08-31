from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict
import inspect

from app.core.deps import get_db
from app.schemas.web_scraper import WebParseRequest, WebDiagnoseRequest
from app.services.web_scraper import parse_schedule_from_web, diagnose_schedule_page

router = APIRouter()

def _call_parse_schedule_from_web(**kwargs):
    func = parse_schedule_from_web
    sig = inspect.signature(func)
    filtered = {k: v for k, v in kwargs.items() if k in sig.parameters}
    return func(**filtered)

@router.post("/web/parse")
def web_parse(req: WebParseRequest):
    try:
        entries = _call_parse_schedule_from_web(
            url=req.url,
            mode=req.mode,
            start_hour=req.start_hour,
            px_per_30=req.px_per_30,
            top_offset=req.top_offset,
            head_selector=req.head_selector,
            body_selector=req.body_selector,
            block_selector=req.block_selector,
            interactive_login=req.interactive_login,
            wait_login_seconds=req.wait_login_seconds or 120,
        )
        if not entries:
            raise HTTPException(status_code=400, detail="시간표를 찾지 못했습니다.")
        lines = [f"{e['subject']}, {e['weekday_ko']}, {e['start']}-{e['end']}" for e in entries]
        return {"entries_text": "\n".join(lines), "entries": entries}
    except Exception as e:
        msg = str(e)
        if ("everytime.kr" in (req.url or "").lower()) and ("로그인" in msg):
            msg += "  (Tip: 에브리타임 앱/웹에서 시간표 > 공유 > 링크 복사 후 /@... 형태 URL을 사용하세요)"
        raise HTTPException(status_code=400, detail=f"Web parse failed: {msg}")

@router.post("/web/diagnose")
def web_diagnose(req: WebDiagnoseRequest):
    try:
        info = diagnose_schedule_page(
            req.url,
            max_samples=req.max_samples or 20,
            for_mode=req.for_mode or "auto",
        )
        return info
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Web diagnose failed: {e}")
