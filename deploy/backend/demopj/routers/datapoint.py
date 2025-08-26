from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from demopj.database import get_session
from demopj.models import DataPoint
from demopj.schemas import DataPointIn, DataPointOut

router = APIRouter(prefix="/data", tags=["data"])

@router.post("/", response_model=DataPointOut)
async def create_data(
    payload: DataPointIn, db: AsyncSession = Depends(get_session)
):
    obj = DataPoint(**payload.model_dump())
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj

@router.get("/{item_id}", response_model=DataPointOut)
async def read_data(item_id: str, db: AsyncSession = Depends(get_session)):
    res = await db.get(DataPoint, item_id)
    if not res:
        raise HTTPException(status_code=404, detail="DataPoint not found")
    return res
