from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Dict, List
from collections import defaultdict

from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.models.material import Material
from app.schemas.material import MaterialOut

# --- API 응답을 위한 새로운 스키마 정의 ---
class FileInfo(MaterialOut):
    pass

class DateInfo(BaseModel):
    session_id: str
    files: List[FileInfo]

class SubjectInfo(BaseModel):
    subject_id: str
    dates: Dict[str, DateInfo]

FileSystemStructure = Dict[str, SubjectInfo]

router = APIRouter()

@router.get(
    "/files/structure",
    response_model=FileSystemStructure,
    summary="Get user's file and folder structure with files",
    description="Builds a nested dictionary representing subjects, session dates, and associated materials."
)
def get_files_structure(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    사용자의 과목, 강의 세션 날짜, 그리고 각 세션에 연결된 파일 목록으로 파일 시스템 구조를 생성합니다.
    프론트엔드가 파일 업로드에 필요한 subject_id와 session_id를 포함합니다.
    """
    # 1. 사용자의 모든 자료를 효율적으로 조회하여 session_id 기준으로 그룹화합니다.
    user_materials = db.query(Material).filter(Material.owner_id == current_user.id).all()
    materials_by_session_id = defaultdict(list)
    for material in user_materials:
        if material.session_id:
            materials_by_session_id[material.session_id].append(FileInfo.model_validate(material))

    # 2. 최종적으로 반환할 파일 시스템 구조를 빌드합니다.
    file_system: Dict[str, SubjectInfo] = {}
    sorted_subjects = sorted(current_user.subjects, key=lambda s: s.title)

    for subject in sorted_subjects:
        dates_for_subject: Dict[str, DateInfo] = {}
        for week in subject.weeks:
            for session in week.sessions:
                date_str = session.date.isoformat()
                if date_str not in dates_for_subject:
                    # 각 날짜별로 session_id와 해당 세션에 속한 파일 목록으로 구성
                    dates_for_subject[date_str] = DateInfo(
                        session_id=session.id,
                        files=materials_by_session_id.get(session.id, [])
                    )
        
        if dates_for_subject:
            # 과목별로 subject_id와 날짜 목록을 포함하여 구성
            file_system[subject.title] = SubjectInfo(
                subject_id=subject.id,
                dates=dict(sorted(dates_for_subject.items()))
            )
            
    return file_system
