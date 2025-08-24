# test_ocr — Timetable OCR API (FastAPI + Tesseract + OpenCV)

이 프로젝트는 시간표 **이미지**를 업로드하면 과목 블록을 감지하고, 요일/시간/과목명을 추출하여 JSON으로 반환합니다.
Swagger (자동 문서화)에서 바로 테스트할 수 있습니다.

## 0) 사전 준비
- **Python 3.10+** 권장
- **Tesseract OCR 엔진** 설치 필요
  - Windows: https://github.com/UB-Mannheim/tesseract/wiki
  - macOS (brew): `brew install tesseract`
  - Linux (Debian/Ubuntu): `sudo apt-get install tesseract-ocr`
- 설치 후 `tesseract` 실행이 PATH에 잡히지 않으면 환경변수 설정:
  - Windows 예시: 환경변수 `TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe`

## 1) 설치
```bash
python -m venv .venv
. .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## 2) 실행
```bash
uvicorn app.main:app --reload --port 8000
```

실행 후 브라우저에서 Swagger 접속:  
http://127.0.0.1:8000/docs

## 3) 사용법
- **POST** `/api/parse-image` 에 `file` (form-data, 이미지 파일) 업로드
- 응답 JSON 예시:
```json
{
  "count": 6,
  "slots": [
    {
      "weekday": "월",
      "start_time": "09:00",
      "end_time": "12:00",
      "title": "산업공학종합설계(캡스톤디자인)",
      "professor": "정영선",
      "location": "공1A-312",
      "raw_text": "산업공학종합설계(캡스톤디자인)\n정영선 공1A-312"
    }
  ],
  "debug": { "...": "추출 디버그 정보" }
}
```

## 4) 설계 요약
- **텍스트 인식:** Tesseract (pytesseract) `image_to_data` 사용
- **요일 헤더 탐지:** 인식된 텍스트에서 `월,화,수,목,금,토,일` 또는 `Mon..Sun` 후보의 x 좌표를 수집
- **시간 행 탐지:** `오전/오후 N시`, `HH:MM`, `H시` 등의 패턴을 정규식으로 잡아 y 좌표를 수집 후 정렬
- **과목 블록 탐지:** 이미지 HSV에서 **채색 영역**(Saturation) 기반 마스크 → 모폴로지 연산 → 컨투어 바운딩 박스
  - 시간표가 무채색이라면 Tesseract 라인 그룹으로 대체 추정
- **블록 → 요일/시간 매칭:**
  - 블록 중심 x를 가장 가까운 요일 헤더 x와 매칭
  - 블록 상단/하단 y를 가장 가까운 **시간 라인** 사이로 매핑해 `start_time`, `end_time` 계산
- **과목명/교수/강의실 파싱:**
  - 블록 내부 텍스트 라인을 y 순서로 결합
  - 한글 비중/길이가 큰 라인을 **과목명 후보**로 선택
  - 위치 패턴(예: `공1A-312`, `S1A-519` 등)과 한글 이름(2~4자) 정규식으로 교수/강의실 추출

## 5) 한계와 팁
- 원본 이미지 해상도가 낮으면 정확도가 떨어질 수 있습니다. (권장: 150 dpi 이상 스크린샷)
- 테두리선이 없는 시간표도 지원하지만, **요일/시간 텍스트**가 인식되지 않으면 시간이 부정확할 수 있습니다.
- 색이 거의 없는 시간표는 `채색 영역` 검출이 약해질 수 있으므로, 이 경우 Tesseract 라인 군집으로 보조합니다.

## 6) 라이선스
MIT
