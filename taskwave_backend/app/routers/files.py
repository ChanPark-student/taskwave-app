from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Dict, List
from collections import defaultdict

from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.models.subject import Subject
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
    'etc' 과목이 없더라도 항상 표시될 수 있도록 기본 포함합니다.
    """
    user_materials = db.query(Material).filter(Material.owner_id == current_user.id).all()
    materials_by_session_id = defaultdict(list)
    for material in user_materials:
        if material.session_id:
            materials_by_session_id[material.session_id].append(FileInfo.model_validate(material))

    file_system: Dict[str, SubjectInfo] = {}
    
    # 'etc' 과목을 먼저 찾거나, 없으면 임시 ID로 생성 준비
    etc_subject = db.query(Subject).filter(Subject.user_id == current_user.id, Subject.title == "etc").first()
    etc_subject_id = etc_subject.id if etc_subject else "temp_etc_id"
    
    # etc 과목에 속하지만 특정 세션에는 속하지 않은 파일들을 추가
    etc_files_dates = defaultdict(lambda: {"session_id": "N/A", "files": []})
    etc_materials = db.query(Material).filter(
        Material.owner_id == current_user.id,
        Material.subject_id == etc_subject_id,
        Material.session_id == None
    ).all()
    
    if etc_materials:
        # 날짜가 없으므로, 생성된 날짜를 키로 사용
        for mat in etc_materials:
            date_key = mat.created_at.strftime("%Y-%m-%d")
            etc_files_dates[date_key]["files"].append(FileInfo.model_validate(mat))

    # 실제 과목들 처리
    sorted_subjects = sorted(current_user.subjects, key=lambda s: s.title)
    for subject in sorted_subjects:
        if subject.title == 'etc': continue # etc는 나중에 처리
        dates_for_subject: Dict[str, DateInfo] = {}
        for week in subject.weeks:
            for session in week.sessions:
                date_str = session.date.isoformat()
                if date_str not in dates_for_subject:
                    dates_for_subject[date_str] = DateInfo(
                        session_id=session.id,
                        files=materials_by_session_id.get(session.id, [])
                    )
        
        if dates_for_subject:
            file_system[subject.title] = SubjectInfo(
                subject_id=subject.id,
                dates=dict(sorted(dates_for_subject.items()))
            )

    # 'etc' 과목 정보 최종 추가 (실제 파일이 없더라도 항상 보이도록)
    file_system['etc'] = SubjectInfo(
        subject_id=etc_subject_id,
        dates=dict(sorted(etc_files_dates.items()))
    )
            
    return file_system
