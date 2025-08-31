# --- ensure project root on sys.path ---
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]  # .../full_taskwave
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
# --- end patch ---

from fastapi import FastAPI, HTTPException, UploadFile, File, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse, PlainTextResponse
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date, datetime
import tempfile, shutil
import inspect

from taskwave.parser import parse_manual_entries
from taskwave.schedule import generate_class_dates
from taskwave.foldergen import build_zip_bytes
from taskwave.config import WEEKDAY_INT_TO_KO
from taskwave.ocr import parse_timetable_file_to_entries
from taskwave.webscrape import parse_schedule_from_web, diagnose_schedule_page

app = FastAPI(title="TaskWave Folder Generator", version="1.8.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.options("/{rest_of_path:path}")
async def preflight(rest_of_path: str, request: Request):
    resp = PlainTextResponse("", status_code=204)
    origin = request.headers.get("Origin", "*")
    req_method = request.headers.get("Access-Control-Request-Method", "*")
    req_headers = request.headers.get("Access-Control-Request-Headers", "*")
    resp.headers["Access-Control-Allow-Origin"] = origin
    resp.headers["Vary"] = "Origin"
    resp.headers["Access-Control-Allow-Methods"] = req_method
    resp.headers["Access-Control-Allow-Headers"] = req_headers
    resp.headers["Access-Control-Max-Age"] = "600"
    resp.headers["Access-Control-Allow-Private-Network"] = "true"
    return resp

@app.get("/health")
def health():
    return {"ok": True, "version": app.version}

# ---------- 공용 스키마 ----------
class GenerateRequest(BaseModel):
    text: str = Field(..., description="사용자 시간표 텍스트")
    start_date: date
    end_date: date
    pattern: Optional[str] = Field(default="{SUBJECT}/주차{WEEK2}/{WEEKDAY_KO}_{MM}-{DD}")
    holidays: Optional[List[date]] = None
    write_meta: bool = True

def make_namer(pattern: str, base_date: date):
    def _namer(entry, d: date):
        YYYY = f"{d.year:04d}"
        MM = f"{d.month:02d}"
        DD = f"{d.day:02d}"
        WEEKDAY_KO = WEEKDAY_INT_TO_KO[entry.weekday]
        SUBJECT = entry.subject
        week = ((d - base_date).days // 7) + 1
        WEEK = str(week)
        WEEK2 = f"{week:02d}"
        return (pattern
                .replace("{YYYY}", YYYY)
                .replace("{MM}", MM)
                .replace("{DD}", DD)
                .replace("{WEEKDAY_KO}", WEEKDAY_KO)
                .replace("{SUBJECT}", SUBJECT)
                .replace("{WEEK}", WEEK)
                .replace("{WEEK2}", WEEK2))
    return _namer

from fastapi.responses import JSONResponse as JR

@app.post("/preview")
def preview(req: GenerateRequest):
    try:
        if req.end_date < req.start_date:
            raise HTTPException(status_code=400, detail="종료일이 시작일보다 앞입니다.")
        entries = parse_manual_entries(req.text)
        hol = set(req.holidays or [])
        namer = make_namer(req.pattern or "{SUBJECT}/주차{WEEK2}/{WEEKDAY_KO}_{MM}-{DD}", req.start_date)
        items = []
        cur = req.start_date
        while cur <= req.end_date:
            for e in entries:
                if cur.weekday() == e.weekday and cur not in hol:
                    path = namer(e, cur).strip("/")
                    items.append(path)
            cur = cur.fromordinal(cur.toordinal() + 1)
        limited = items[:200]
        return JR({"count": len(items), "sample": limited})
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/generate.zip")
def generate(req: GenerateRequest):
    try:
        if req.end_date < req.start_date:
            raise HTTPException(status_code=400, detail="종료일이 시작일보다 앞입니다.")
        entries = parse_manual_entries(req.text)
        hol = set(req.holidays or [])
        namer = make_namer(req.pattern or "{SUBJECT}/주차{WEEK2}/{WEEKDAY_KO}_{MM}-{DD}", req.start_date)
        class_dates = generate_class_dates(entries, req.start_date, req.end_date, holidays=hol)
        data = build_zip_bytes(class_dates, namer=namer, write_meta=req.write_meta)
        filename = f"generated_folders_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        return StreamingResponse(
            iter([data]),
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ---------- OCR 업로드 ----------
@app.post("/ocr/parse")
async def ocr_parse(file: UploadFile = File(...)):
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename or 'in').suffix) as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = Path(tmp.name)
        entries = parse_timetable_file_to_entries(tmp_path)
        lines = [f"{e['subject'].strip()}, {e['weekday_ko']}, {e['start']}-{e['end']}" for e in entries]
        text = "\n".join(lines)
        tmp_path.unlink(missing_ok=True)
        return JR({"entries_text": text, "entries": entries})
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"OCR parse failed: {e}")

# ---------- 웹 ----------
class WebParseRequest(BaseModel):
    url: str
    mode: str = Field(default="css", description="auto | kor | dom | text | css") # auto -> css로 수정
    start_hour: int | None = 9
    px_per_30: float | None = 40.33 # 25 -> 40.33으로 수정
    top_offset: float | None = 540.0 # 450 -> 540으로 수정
    head_selector: str | None = ".tablehead td,.fc-col-header th,.header td,thead th,.days td,.fc-col-header-cell,.rbc-time-header,.tui-full-calendar-dayname"
    body_selector: str | None = ".tablebody,.fc-timegrid,.timetable,.timeTable,.schedule-body,.weekly-schedule,.calendar,.fc-scroller-harness,.rbc-time-content,.rbc-time-view,.tui-full-calendar-timegrid-container,.timeGrid,.schedule"
    block_selector: str | None = ".subject,.fc-timegrid-event,.fc-event,.lesson,.class,.event,.lecture,.rbc-event,.tui-full-calendar-time-schedule,[data-event],[class*='event']"
    interactive_login: bool = False
    wait_login_seconds: int | None = 120

def _call_parse_schedule_from_web(**kwargs):
    func = parse_schedule_from_web
    sig = inspect.signature(func)
    filtered = {k: v for k, v in kwargs.items() if k in sig.parameters}
    return func(**filtered)

@app.post("/web/parse")
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
        return JR({"entries_text": "\n".join(lines), "entries": entries})
    except Exception as e:
        msg = str(e)
        if ("everytime.kr" in (req.url or "").lower()) and ("로그인" in msg):
            msg += "  (Tip: 에브리타임 앱/웹에서 시간표 > 공유 > 링크 복사 후 /@... 형태 URL을 사용하세요)"
        raise HTTPException(status_code=400, detail=f"Web parse failed: {msg}")

class WebDiagnoseRequest(BaseModel):
    url: str
    max_samples: int | None = 20
    for_mode: str | None = "auto"

@app.post("/web/diagnose")
def web_diagnose(req: WebDiagnoseRequest):
    try:
        info = diagnose_schedule_page(
            req.url,
            max_samples=req.max_samples or 20,
            for_mode=req.for_mode or "auto",
        )
        return JR(info)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Web diagnose failed: {e}")