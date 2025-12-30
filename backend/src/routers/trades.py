from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..database import get_db
from ..models import TradeLog, TradeContext
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from ..services.trade_analysis_service import trade_analysis_service
from typing import List, Dict, Any

router = APIRouter(
    prefix="/trades",
    tags=["trades"]
)

class TradeLogBase(BaseModel):
    symbol: str
    direction: str
    entry_price: float
    position_size: float
    pre_trade_confidence: Optional[int] = None

class TradeLogCreate(TradeLogBase):
    pass

class TradeLogResponse(TradeLogBase):
    trade_id: str
    timestamp: datetime
    exit_price: Optional[float] = None
    profit_loss_pips: Optional[float] = None
    pnl: Optional[float] = None
    status: str

    class Config:
        from_attributes = True

@router.get("/stats", response_model=Dict[str, Any])
async def get_trade_stats(db: AsyncSession = Depends(get_db)):
    return await trade_analysis_service.get_performance_stats(db)

@router.get("/", response_model=List[TradeLogResponse])
async def get_trades(skip: int = 0, limit: int = 20, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TradeLog).order_by(TradeLog.timestamp.desc()).offset(skip).limit(limit))
    trades = result.scalars().all()
    return trades

@router.post("/", response_model=TradeLogResponse)
async def create_trade(trade: TradeLogCreate, db: AsyncSession = Depends(get_db)):
    import uuid
    new_trade = TradeLog(
        trade_id=str(uuid.uuid4()),
        symbol=trade.symbol,
        direction=trade.direction,
        entry_price=trade.entry_price,
        position_size=trade.position_size,
        pre_trade_confidence=trade.pre_trade_confidence,
        timestamp=datetime.utcnow()
    )
    db.add(new_trade)
    await db.commit()
    await db.refresh(new_trade)
    return new_trade
