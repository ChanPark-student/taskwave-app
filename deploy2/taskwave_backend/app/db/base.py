# app/db/base.py
from sqlalchemy.orm import declarative_base

Base = declarative_base()

# 아래 줄들이 있어야 테이블이 생성됩니다.
# (다른 모델도 이미 있다면 그대로 두고, upload만 추가)
from app.models import user, subject, schedule, material, upload  # <-- 여기!
