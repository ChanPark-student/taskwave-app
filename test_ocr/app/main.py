from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from .ocr import parse_timetable
from .models import ParseResponse, Slot
import uvicorn

app = FastAPI(
    title="Timetable OCR API",
    version="1.0.0",
    description="시간표 이미지에서 과목/요일/시간을 추출하는 API"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/api/parse-image", response_model=ParseResponse)
async def parse_image(file: UploadFile = File(...)):
    try:
        content = await file.read()
        result = parse_timetable(content)
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
