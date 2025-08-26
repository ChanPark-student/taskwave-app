# backend/main.py
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from demopj.database import engine, Base        # ✅ 절대 경로
from demopj.routers import feedback, datapoint, cluster, community

import inspect, sys
from demopj.database import get_session    # ← 기존 코드

import os, sys
# ---------- 진단용 (임시) ----------
db_url = os.getenv("DATABASE_URL", "(not set)")
print("### DATABASE_URL at runtime ###")
print(db_url, file=sys.stderr)          # STDERR 로 찍으면 Render 로그에 바로 보임
print("### ----------------------- ###")
# -----------------------------------

app = FastAPI()

@app.get("/", tags=["health"])
async def health():
    return {"status": "ok"}

# CORS 설정 (프론트 연동 위해 필요)
origins = [
    "https://deploy-frontend-hm85.onrender.com",    #  ← 이 줄!!

]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# DB 테이블 생성
@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# 라우터 등록
app.include_router(feedback.router)
app.include_router(datapoint.router) 
app.include_router(cluster.router)  
app.include_router(community.router)
