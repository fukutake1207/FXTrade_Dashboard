from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from ..database import get_db
from ..models import TradeLog, TradeContext
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from ..services.trade_analysis_service import trade_analysis_service
import json

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
    exit_price: Optional[float] = None
    profit_loss_pips: Optional[float] = None
    profit_loss_amount: Optional[float] = None
    trade_duration_minutes: Optional[int] = None
    post_trade_evaluation: Optional[str] = None
    lessons_learned: Optional[str] = None

class TradeContextBase(BaseModel):
    session: Optional[str] = None
    market_condition: Optional[str] = None
    ai_narrative_summary: Optional[str] = None
    active_scenarios: List[str] = Field(default_factory=list)
    key_levels_nearby: List[float] = Field(default_factory=list)
    correlation_status: Dict[str, float] = Field(default_factory=dict)
    economic_events_upcoming: List[str] = Field(default_factory=list)

class TradeLogCreate(TradeLogBase):
    entry_context: Optional[TradeContextBase] = None
    exit_context: Optional[TradeContextBase] = None

class TradeContextResponse(TradeContextBase):
    context_type: str

class TradeLogResponse(TradeLogBase):
    trade_id: str
    timestamp: datetime
    entry_context: Optional[TradeContextResponse] = None
    exit_context: Optional[TradeContextResponse] = None

    class Config:
        from_attributes = True

def _parse_context(context: TradeContext) -> TradeContextResponse:
    return TradeContextResponse(
        context_type=context.context_type,
        session=context.session,
        market_condition=context.market_condition,
        ai_narrative_summary=context.ai_narrative_summary,
        active_scenarios=json.loads(context.active_scenarios or "[]"),
        key_levels_nearby=json.loads(context.key_levels_nearby or "[]"),
        correlation_status=json.loads(context.correlation_status or "{}"),
        economic_events_upcoming=json.loads(context.economic_events_upcoming or "[]")
    )

def _build_trade_response(trade: TradeLog) -> TradeLogResponse:
    entry_context = None
    exit_context = None
    for context in trade.contexts or []:
        if context.context_type == "entry" and entry_context is None:
            entry_context = _parse_context(context)
        elif context.context_type == "exit" and exit_context is None:
            exit_context = _parse_context(context)

    return TradeLogResponse(
        trade_id=trade.trade_id,
        timestamp=trade.timestamp,
        symbol=trade.symbol,
        direction=trade.direction,
        entry_price=trade.entry_price,
        position_size=trade.position_size,
        pre_trade_confidence=trade.pre_trade_confidence,
        exit_price=trade.exit_price,
        profit_loss_pips=trade.profit_loss_pips,
        profit_loss_amount=trade.profit_loss_amount,
        trade_duration_minutes=trade.trade_duration_minutes,
        post_trade_evaluation=trade.post_trade_evaluation,
        lessons_learned=trade.lessons_learned,
        entry_context=entry_context,
        exit_context=exit_context
    )

@router.get("/stats", response_model=Dict[str, Any])
async def get_trade_stats(db: AsyncSession = Depends(get_db)):
    return await trade_analysis_service.get_performance_stats(db)

@router.get("/", response_model=List[TradeLogResponse])
async def get_trades(skip: int = 0, limit: int = 20, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(TradeLog)
        .options(selectinload(TradeLog.contexts))
        .order_by(TradeLog.timestamp.desc())
        .offset(skip)
        .limit(limit)
    )
    trades = result.scalars().all()
    return [_build_trade_response(trade) for trade in trades]

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
        exit_price=trade.exit_price,
        profit_loss_pips=trade.profit_loss_pips,
        profit_loss_amount=trade.profit_loss_amount,
        trade_duration_minutes=trade.trade_duration_minutes,
        post_trade_evaluation=trade.post_trade_evaluation,
        lessons_learned=trade.lessons_learned,
        timestamp=datetime.utcnow()
    )
    db.add(new_trade)

    if trade.entry_context:
        db.add(TradeContext(
            context_id=str(uuid.uuid4()),
            trade_id=new_trade.trade_id,
            context_type="entry",
            session=trade.entry_context.session,
            market_condition=trade.entry_context.market_condition,
            ai_narrative_summary=trade.entry_context.ai_narrative_summary,
            active_scenarios=json.dumps(trade.entry_context.active_scenarios),
            key_levels_nearby=json.dumps(trade.entry_context.key_levels_nearby),
            correlation_status=json.dumps(trade.entry_context.correlation_status),
            economic_events_upcoming=json.dumps(trade.entry_context.economic_events_upcoming)
        ))

    if trade.exit_context:
        db.add(TradeContext(
            context_id=str(uuid.uuid4()),
            trade_id=new_trade.trade_id,
            context_type="exit",
            session=trade.exit_context.session,
            market_condition=trade.exit_context.market_condition,
            ai_narrative_summary=trade.exit_context.ai_narrative_summary,
            active_scenarios=json.dumps(trade.exit_context.active_scenarios),
            key_levels_nearby=json.dumps(trade.exit_context.key_levels_nearby),
            correlation_status=json.dumps(trade.exit_context.correlation_status),
            economic_events_upcoming=json.dumps(trade.exit_context.economic_events_upcoming)
        ))

    await db.commit()
    await db.refresh(new_trade)

    result = await db.execute(
        select(TradeLog).options(selectinload(TradeLog.contexts)).where(TradeLog.trade_id == new_trade.trade_id)
    )
    trade_with_context = result.scalar_one()
    return _build_trade_response(trade_with_context)
