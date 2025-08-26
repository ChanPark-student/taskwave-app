import logging
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import get_current_user, get_db
from app.models.user import User
# 'parse_timetable_from_file' 함수와 'ParsedSlot'을 임포트합니다.
from app.services.timetable import ParsedSlot, parse_timetable_from_file

# 로거 설정
logger = logging.getLogger(__name__)

router = APIRouter()

# 지원하는 이미지 파일 확장자
ALLOWED_IMAGE_SUFFIX = {".png", ".jpg", ".jpeg", ".webp"}


@router.post("/timetable/upload")
async def upload_timetable(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    시간표 파일(이미지 또는 PDF)을 업로드하여 OCR로 분석하고 파싱된 슬롯 목록을 반환합니다.
    디버깅을 위해 파싱된 슬롯과 함께 OCR로 추출된 원본 텍스트도 반환합니다.
    """
    # 1) 파일 저장
    suffix = Path(file.filename or "").suffix.lower()
    save_dir = Path(settings.MEDIA_ROOT) / "timetables"
    save_dir.mkdir(parents=True, exist_ok=True)
    
    # 고유한 파일명 생성
    save_path = save_dir / f"{uuid4()}{suffix}"

    try:
        content = await file.read()
        save_path.write_bytes(content)
    except Exception:
        logger.exception("파일 저장 실패")
        raise HTTPException(status_code=500, detail="파일을 서버에 저장하는 중 오류가 발생했습니다.")

    # 2) 파싱 시도
    slots: list[ParsedSlot] = []
    raw_text = ""
    try:
        if suffix == ".pdf" or suffix in ALLOWED_IMAGE_SUFFIX:
            # 수정된 서비스 함수는 (slots, raw_text) 튜플을 반환합니다.
            slots, raw_text = parse_timetable_from_file(save_path)
        else:
            raise HTTPException(status_code=400, detail="지원하는 형식은 pdf, png, jpg, jpeg, webp 입니다.")
            
    except Exception as e:
        logger.exception("OCR/파싱 실패")
        # 클라이언트에게 더 유용한 에러 메시지 제공
        raise HTTPException(status_code=422, detail=f"시간표 분석에 실패했습니다: {type(e).__name__}: {e}")

    # 3) 파싱 결과 반환 (DB 저장은 추후 구현)
    return {
        "count": len(slots),
        "slots": [s.__dict__ for s in slots],
        "debug_raw_ocr_text": raw_text, # 디버깅을 위한 OCR 원본 텍스트
    }