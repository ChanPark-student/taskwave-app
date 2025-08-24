
# routers/feedback.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from demopj.database import get_session
from demopj.models    import Feedback
from demopj.schemas   import FeedbackCreate, FeedbackOut

router = APIRouter()

@router.post("/submit", response_model=FeedbackOut)
async def submit_feedback(
    payload: FeedbackCreate,
    db: AsyncSession = Depends(get_session),
):
    fb = Feedback(**payload.model_dump())
    db.add(fb)
    await db.commit()
    await db.refresh(fb)
    return fb

@router.get("/admin/feedbacks", response_model=list[FeedbackOut])
async def get_all_feedbacks(db: AsyncSession = Depends(get_session)):
    result = await db.execute(
        select(Feedback).order_by(Feedback.created_at.desc())
    )
    return result.scalars().all()
