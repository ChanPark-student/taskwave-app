
# TaskWave – 시간표 기반 자동 폴더 생성 (완성 패키지)

두 가지 사용 모드:
1. **frontend_client/**: 브라우저에서 바로 ZIP 생성 (서버 불필요)
2. **backend_fastapi/** + **frontend_server/**: FastAPI로 ZIP 생성/미리보기 (서버 연동)

## 0) 공통 입력 포맷
```
과목, 요일, 시작-끝
예) 데이터베이스설계, 월요일, 10:30-12:00
    확률및통계, 수, 0900-1020
    자료구조, 금, 13:00-14:15
```
- 요일: `월/화/수/목/금/토/일` 또는 `월요일/...`
- 시간: `1030` 또는 `10:30`
- 폴더명 패턴 변수: `{YYYY}`, `{MM}`, `{DD}`, `{WEEKDAY_KO}`, `{SUBJECT}`

---
## 1) 클라이언트 전용(frontend_client)

### 실행
- VSCode Live Server 또는 파일 더블클릭로 `frontend_client/index.html` 열기
- 입력 → 미리보기 → ZIP 다운로드

---
## 2) 서버 연동(back + front)

### FastAPI 백엔드 실행
```bash
cd backend_fastapi
python -m venv .venv
# Windows
. .venv/Scripts/activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### 서버 연동 프론트 실행
- `frontend_server/index.html`을 Live Server로 열기
- 기본 API 주소는 `http://127.0.0.1:8000`
  - 변경 필요 시, 브라우저 콘솔에서:
    ```js
    localStorage.setItem('apiBase', 'http://localhost:8000')
    ```

### API 명세
- `POST /preview` → `{ count, sample[] }`
- `POST /generate.zip` → ZIP 파일 다운로드 응답
- 공통 Request JSON:
```json
{
  "text": "데이터베이스설계, 월요일, 10:30-12:00\n자료구조, 금, 13:00-14:15",
  "start_date": "2025-09-01",
  "end_date": "2025-12-20",
  "pattern": "{YYYY}/{MM}{DD}_{WEEKDAY_KO}_{SUBJECT}",
  "holidays": ["2025-10-03"],
  "write_meta": true
}
```

---
## 3) 구조
```
full_taskwave/
  taskwave/
    __init__.py
    models.py
    config.py
    parser.py
    schedule.py
    foldergen.py
  backend_fastapi/
    main.py
    requirements.txt
  frontend_client/
    index.html
    styles.css
    client.js
  frontend_server/
    index.html
    styles.css
  README.md
```

---
## 4) 확장 아이디어
- 휴강/보강 일정 CSV 업로드
- 과목별 서브폴더 템플릿(노트/슬라이드/과제) 자동 생성
- iCal/구글캘린더 import → 시간표 자동 반영
- OCR/LLM 연결 → 강의계획서/시간표 이미지에서 자동 파싱
