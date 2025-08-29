import logging
from pathlib import Path
from uuid import uuid4
from datetime import datetime, timedelta, timezone
import os

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, Form, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.models.subject import Subject
from app.models.schedule import Week, Session as SessionModel
from app.models.material import Material
from app.schemas.material import MaterialOut
from app.services.storage import StorageService
from app.services.timetable import ParsedSlot, parse_timetable_from_file

logger = logging.getLogger(__name__)
router = APIRouter()
ALLOWED_IMAGE_SUFFIX = {".png", ".jpg", ".jpeg", ".webp"}

@router.post("/uploads/auto-sort", response_model=MaterialOut, status_code=201)
async def upload_and_auto_sort_file(
    file: UploadFile = File(...),
    last_modified: int = Form(...), # JS Date.now()와 같은 밀리초 타임스탬프
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    파일을 업로드하고, 파일의 최종 수정 시간을 기준으로 가장 적합한 강의 세션에 자동으로 연결합니다.
    """
    # 1. 타임스탬프를 KST로 변환
    try:
        # JS에서 받은 밀리초 타임스탬프를 초 단위로 바꾸고 UTC datetime 객체 생성
        dt_utc = datetime.fromtimestamp(last_modified / 1000, tz=timezone.utc)
        # 한국 시간(KST, UTC+9)으로 변환
        dt_kst = dt_utc + timedelta(hours=9)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid timestamp format")

    # 2. 일치하는 세션 찾기
    # 먼저 날짜(date)로 필터링하여 성능 최적화
    sessions_on_date = (
        db.query(SessionModel)
        .join(Week).join(Subject)
        .filter(
            Subject.user_id == current_user.id,
            SessionModel.date == dt_kst.date()
        ).all()
    )

    matched_session = None
    for session in sessions_on_date:
        # DB의 start_time, end_time은 timezone 정보가 없으므로, KST 시간과 직접 비교
        if session.start_time <= dt_kst.time() <= session.end_time:
            matched_session = session
            break

    # 3. 파일 저장 및 Material 레코드 생성
    storage = StorageService()
    file_url, abs_path = await storage.save_upload(file, subdir="materials")

    subject_id, week_id, session_id = None, None, None
    if matched_session:
        subject_id = matched_session.week.subject_id
        week_id = matched_session.week_id
        session_id = matched_session.id

    mat = Material(
        id=str(uuid4()),
        owner_id=current_user.id,
        subject_id=subject_id, # 일치하는 경우에만 ID 저장
        week_id=week_id,
        session_id=session_id,
        name=file.filename or "untitled",
        mime_type=file.content_type or "application/octet-stream",
        file_url=file_url,
        size_bytes=os.path.getsize(abs_path) if abs_path else 0,
    )
    db.add(mat)
    db.commit()
    db.refresh(mat)
    return mat


@router.post("/timetable/upload")
async def upload_timetable(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    시간표 파일(이미지 또는 PDF)을 업로드하여 OCR로 분석하고 파싱된 슬롯 목록을 반환합니다.
    """
    suffix = Path(file.filename or "").suffix.lower()
    save_dir = Path(settings.MEDIA_ROOT) / "timetables"
    save_dir.mkdir(parents=True, exist_ok=True)
    save_path = save_dir / f"{uuid4()}{suffix}"

    try:
        content = await file.read()
        save_path.write_bytes(content)
    except Exception:
        logger.exception("파일 저장 실패")
        raise HTTPException(status_code=500, detail="파일을 서버에 저장하는 중 오류가 발생했습니다.")

    try:
        if suffix == ".pdf" or suffix in ALLOWED_IMAGE_SUFFIX:
            slots, raw_text = parse_timetable_from_file(save_path)
        else:
            raise HTTPException(status_code=400, detail="지원하는 형식은 pdf, png, jpg, jpeg, webp 입니다.")
    except Exception as e:
        logger.exception("OCR/파싱 실패")
        raise HTTPException(status_code=422, detail=f"시간표 분석에 실패했습니다: {type(e).__name__}: {e}")

    return {
        "count": len(slots),
        "slots": [s.__dict__ for s in slots],
        "debug_raw_ocr_text": raw_text,
    }
