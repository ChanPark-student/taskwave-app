# app/core/security.py
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Union

import jwt
from fastapi import HTTPException, status
from fastapi.security import HTTPBearer
from passlib.context import CryptContext

from app.core.config import settings

# 비밀번호 해시 컨텍스트
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Swagger/요청에서 Authorization: Bearer <token> 읽기용 스킴
bearer_scheme = HTTPBearer(auto_error=False)

# JWT 설정
ALGORITHM = "HS256"
SECRET_KEY = getattr(settings, "SECRET_KEY", "change-me")
ACCESS_TOKEN_EXPIRE_MINUTES = getattr(settings, "ACCESS_TOKEN_EXPIRE_MINUTES", 60)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_access_token(
    data: Union[str, Dict[str, Any]],
    expires_minutes: Optional[int] = None,
) -> str:
    # 문자열이면 sub에 담고, dict면 복사해서 사용
    if isinstance(data, str):
        to_encode: Dict[str, Any] = {"sub": data}
    elif isinstance(data, dict):
        to_encode = data.copy()
    else:
        raise ValueError("data must be str or dict")

    expire = datetime.now(timezone.utc) + timedelta(
        minutes=expires_minutes or ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_access_token(token: str) -> str:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        sub = payload.get("sub")
        if not sub:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
        return str(sub)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
