from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..database import get_db
from ..models import PriceStatistic
from ..services.data_collector import data_collector
from typing import List
from pydantic import BaseModel
from datetime import date

router = APIRouter(
    prefix="/prices",
    tags=["prices"]
)

class PriceStatResponse(BaseModel):
    date: date
    session: str
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    range_pips: float
    volatility: float

    class Config:
        from_attributes = True

@router.post("/collect")
async def trigger_collection(db: AsyncSession = Depends(get_db)):
    """Trigger manual data collection"""
    await data_collector.collect_and_store_prices(db)
    return {"status": "success", "message": "Data collection triggered"}

@router.get("/stats/today", response_model=List[PriceStatResponse])
async def get_today_stats(db: AsyncSession = Depends(get_db)):
    # In a real app, 'today' would be determined dynamically or passed as param
    # For now, we return the latest available
    result = await db.execute(select(PriceStatistic).order_by(PriceStatistic.date.desc()).limit(10))
    stats = result.scalars().all()
    return stats
