from fastapi import APIRouter, Depends
from typing import Dict, List

from app.core.deps import get_current_user
from app.models.user import User

# 응답 모델 정의: Dict[과목명, Dict[날짜, 파일리스트]]
FileSystemStructure = Dict[str, Dict[str, List]]

router = APIRouter()

@router.get(
    "/files/structure",
    response_model=FileSystemStructure,
    summary="Get user's file and folder structure",
    description="Builds a nested dictionary representing the user's subjects and all their session dates."
)
def get_files_structure(
    current_user: User = Depends(get_current_user)
):
    """
    사용자의 과목과 각 강의 세션 날짜로부터 파일 시스템과 유사한 구조를 생성합니다.
    - 최상위 키: 과목명
    - 두 번째 레벨 키: "YYYY-MM-DD" 형식의 실제 강의 날짜
    - 값: 향후 파일 메타데이터를 위해 예약된 빈 리스트
    """
    file_system: Dict[str, Dict[str, List]] = {}

    # SQLAlchemy relationship을 통해 current_user 객체에서 바로 과목 목록에 접근 가능
    # 일관된 순서를 위해 과목명을 기준으로 정렬
    sorted_subjects = sorted(current_user.subjects, key=lambda s: s.title)

    for subject in sorted_subjects:
        dates_for_subject: Dict[str, List] = {}
        
        for week in subject.weeks:
            for session in week.sessions:
                # session.date는 Python의 date 객체이므로 .isoformat()으로 "YYYY-MM-DD" 문자열로 변환
                date_str = session.date.isoformat()
                
                # 해당 날짜 키가 처음 나타나는 경우, 빈 리스트로 초기화
                if date_str not in dates_for_subject:
                    dates_for_subject[date_str] = []
        
        if dates_for_subject:
            # 날짜를 시간순으로 정렬하여 최종 객체에 추가
            sorted_dates = dict(sorted(dates_for_subject.items()))
            file_system[subject.title] = sorted_dates
            
    return file_system
