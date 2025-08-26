# demopj/routers/community.py
from uuid import UUID
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from demopj.database import get_session
from demopj.models import Post, Comment, User
from demopj.schemas import (
    PostCreate, CommentCreate, CommentOut,
    UserCreate, UserOut
)
from passlib.hash import bcrypt

router = APIRouter(prefix="/community", tags=["community"])

# ──────────── 게시글 ──────────────────────────────────
@router.post("/post")
async def create_post(
    payload: PostCreate,
    db: AsyncSession = Depends(get_session)
):
    post = Post(**payload.model_dump())
    db.add(post)
    await db.commit()
    await db.refresh(post)
    return post

@router.get("/posts")
async def get_posts(db: AsyncSession = Depends(get_session)):
    rows = (await db.execute(select(Post))).scalars().all()
    return rows

# ──────────── 댓글 ───────────────────────────────────
@router.post("/comment", response_model=CommentOut)
async def create_comment(
    payload: CommentCreate,
    db: AsyncSession = Depends(get_session)
):
    comment = Comment(**payload.model_dump())
    db.add(comment)
    await db.commit()
    await db.refresh(comment)
    return comment

@router.get("/comments", response_model=list[CommentOut])
async def list_comments(
    post_id: UUID = Query(...),
    db: AsyncSession = Depends(get_session)
):
    q = select(Comment).where(Comment.post_id == post_id).order_by(Comment.created_at)
    rows = (await db.execute(q)).scalars().all()
    return rows                    # 빈 리스트면 200 + []

# ──────────── 사용자 ─────────────────────────────────
@router.post("/user", response_model=UserOut)
async def create_user(payload: UserCreate, db: AsyncSession = Depends(get_session)):
    exists = await db.scalar(select(User).where(User.username == payload.username))
    if exists:
        raise HTTPException(status_code=409, detail="이미 사용 중인 이름입니다.")

    user = User(
        username=payload.username,
        password_hash=bcrypt.hash(payload.password)
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user



@router.get("/users", response_model=list[UserOut])
async def list_users(db: AsyncSession = Depends(get_session)):
    rows = (await db.execute(select(User))).scalars().all()
    return rows
