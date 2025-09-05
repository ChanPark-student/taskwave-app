from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Dict, List, Optional
from collections import defaultdict

from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.models.subject import Subject
from app.models.material import Material
from app.models.event import Event
from app.schemas.material import MaterialOut
from app.schemas.event import EventOut

# --- API 응답을 위한 스키마 정의 ---
class FileInfo(MaterialOut):
    pass

class DateInfo(BaseModel):
    session_id: str | None = None
    files: List[FileInfo]
    events: List[EventOut] # 한 날짜에 여러 이벤트를 위해 리스트로 변경

class SubjectInfo(BaseModel):
    subject_id: str
    dates: Dict[str, DateInfo]

FileSystemStructure = Dict[str, SubjectInfo]

router = APIRouter()

@router.get(
    "/files/structure",
    response_model=FileSystemStructure,
    summary="Get user's file and folder structure with files and events",
    description="Builds a nested dictionary representing subjects, dates, associated files, and events."
)
def get_files_structure(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        # 1. 사용자의 모든 과목, 자료, 이벤트를 한 번에 조회
        subjects = db.query(Subject).filter(Subject.user_id == current_user.id).all()
        materials = db.query(Material).filter(Material.owner_id == current_user.id).all()
        events = db.query(Event).join(Subject).filter(Subject.user_id == current_user.id).all()

        # 2. 빠른 조회를 위해 데이터를 딕셔너리로 가공
        materials_by_session_id = defaultdict(list)
        materials_by_date_and_subject = defaultdict(list)
        unclassified_materials = []

        for material in materials:
            if material.session_id:
                materials_by_session_id[material.session_id].append(FileInfo.model_validate(material))
            elif material.date and material.subject_id:
                key = (material.subject_id, material.date.isoformat())
                materials_by_date_and_subject[key].append(FileInfo.model_validate(material))
            else:
                unclassified_materials.append(FileInfo.model_validate(material))

        events_by_date_and_subject = defaultdict(list)
        for event in events:
            events_by_date_and_subject[(event.date.isoformat(), event.subject_id)].append(EventOut.model_validate(event))

        # 3. 최종 파일 시스템 구조 빌드
        file_system: Dict[str, SubjectInfo] = {}
        sorted_subjects = sorted(subjects, key=lambda s: s.title)

        for subject in sorted_subjects:
            dates_for_subject: Dict[str, DateInfo] = defaultdict(lambda: DateInfo(session_id=None, files=[], events=[]))

            # 세션 기반 날짜 채우기
            for week in subject.weeks:
                for session in week.sessions:
                    date_str = session.date.isoformat()
                    dates_for_subject[date_str].session_id = session.id
                    dates_for_subject[date_str].files.extend(materials_by_session_id.get(session.id, []))

            # 이벤트 기반 날짜 채우기 (세션이 없는 날에도 이벤트가 있을 수 있음)
            for event in subject.events:
                date_str = event.date.isoformat()
                # 이벤트 목록은 덮어쓰지 않고 추가
                if event not in dates_for_subject[date_str].events:
                     dates_for_subject[date_str].events.append(EventOut.model_validate(event))

            # 날짜만 지정된 Material 채우기
            for (subj_id, date_str), mats in materials_by_date_and_subject.items():
                if subj_id == subject.id:
                    # 중복 추가를 방지하기 위해 파일 ID 세트 사용
                    existing_file_ids = {f.id for f in dates_for_subject[date_str].files}
                    for mat in mats:
                        if mat.id not in existing_file_ids:
                            dates_for_subject[date_str].files.append(mat)

            if dates_for_subject:
                file_system[subject.title] = SubjectInfo(
                    subject_id=subject.id,
                    dates=dict(sorted(dates_for_subject.items()))
                )
        
        # NEW: Handle unclassified materials (etc folder)
        if unclassified_materials:
            etc_subject_id = "etc_subject_id" # A dummy ID for the 'etc' subject
            etc_date_str = "unclassified" # A generic date string for unclassified materials

            etc_date_info = DateInfo(
                session_id=None,
                files=unclassified_materials,
                events=[]
            )
            
            file_system["etc"] = SubjectInfo(
                subject_id=etc_subject_id,
                dates={etc_date_str: etc_date_info}
            )
                
        return file_system
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve file structure: {e}")
