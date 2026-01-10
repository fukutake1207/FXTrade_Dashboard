from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from ..database import get_db
from ..models import TradeLog, TradeContext
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
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
    position_id: Optional[str] = None
    entry_ticket: Optional[str] = None
    exit_ticket: Optional[str] = None
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
        position_id=trade.position_id,
        entry_ticket=trade.entry_ticket,
        exit_ticket=trade.exit_ticket,
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

@router.put("/{trade_id}", response_model=TradeLogResponse)
async def update_trade(trade_id: str, trade: TradeLogCreate, db: AsyncSession = Depends(get_db)):
    """
    Update a trade (only for manually created trades).
    """
    result = await db.execute(
        select(TradeLog).options(selectinload(TradeLog.contexts)).where(TradeLog.trade_id == trade_id)
    )
    existing_trade = result.scalar_one_or_none()

    if not existing_trade:
        raise HTTPException(status_code=404, detail="Trade not found")

    # Prevent editing MT5-synced trades
    if existing_trade.position_id or existing_trade.entry_ticket:
        raise HTTPException(status_code=403, detail="Cannot edit MT5-synced trades")

    # Update fields
    existing_trade.symbol = trade.symbol
    existing_trade.direction = trade.direction
    existing_trade.entry_price = trade.entry_price
    existing_trade.position_size = trade.position_size
    existing_trade.pre_trade_confidence = trade.pre_trade_confidence
    existing_trade.exit_price = trade.exit_price
    existing_trade.profit_loss_pips = trade.profit_loss_pips
    existing_trade.profit_loss_amount = trade.profit_loss_amount
    existing_trade.trade_duration_minutes = trade.trade_duration_minutes
    existing_trade.post_trade_evaluation = trade.post_trade_evaluation
    existing_trade.lessons_learned = trade.lessons_learned

    await db.commit()
    await db.refresh(existing_trade)

    return _build_trade_response(existing_trade)

@router.delete("/{trade_id}")
async def delete_trade(trade_id: str, db: AsyncSession = Depends(get_db)):
    """
    Delete a trade (only for manually created trades).
    """
    result = await db.execute(
        select(TradeLog).where(TradeLog.trade_id == trade_id)
    )
    existing_trade = result.scalar_one_or_none()

    if not existing_trade:
        raise HTTPException(status_code=404, detail="Trade not found")

    # Prevent deleting MT5-synced trades
    if existing_trade.position_id or existing_trade.entry_ticket:
        raise HTTPException(status_code=403, detail="Cannot delete MT5-synced trades")

    await db.delete(existing_trade)
    await db.commit()

    return {"message": "Trade deleted successfully"}

@router.post("/sync", response_model=List[TradeLogResponse])
async def sync_trades(db: AsyncSession = Depends(get_db)):
    """
    Sync trades from MT5 history.
    Fetches deals from MT5, identifies completed trades, and upserts them into the database.
    """
    from ..services.mt5_service import mt5_service
    import logging
    logger = logging.getLogger(__name__)

    try:
        # Sync open positions first
        positions = await mt5_service.get_positions()
        if positions is None:
             raise HTTPException(status_code=503, detail="Failed to connect to MT5 or fetch positions")
        
        logger.info(f"Fetched {len(positions)} open positions")
        
        synced_ids = set()

        # Process open positions
        for pos in positions:
            position_id = pos.get('position_id')
            ticket = pos.get('ticket')
            trade_id = str(position_id if position_id is not None else ticket)

            # volumeの検証
            volume = pos.get('volume')
            if volume is None or volume == 0:
                logger.warning(f"Invalid volume for open position {position_id or ticket}: {volume}. Skipping.")
                continue

            profit = pos.get('profit', 0.0) + pos.get('swap', 0.0)

            # Map fields
            direction = "LONG" if pos['type'] == 0 else "SHORT" # 0=BUY, 1=SELL

            # Upsert
            existing = await db.execute(select(TradeLog).where(TradeLog.trade_id == trade_id))
            obj = existing.scalar()

            if not obj:
                obj = TradeLog(trade_id=trade_id)
                db.add(obj)

            obj.timestamp = pos['time']
            obj.symbol = pos['symbol']
            obj.direction = direction
            obj.entry_price = pos['price_open']
            obj.exit_price = None # Open
            obj.position_size = volume
            obj.profit_loss_amount = profit
            obj.profit_loss_pips = 0 # Calculate if needed
            obj.trade_duration_minutes = int((datetime.now() - pos['time']).total_seconds() / 60)
            obj.position_id = str(position_id) if position_id is not None else None
            obj.entry_ticket = str(ticket) if ticket is not None else None

            synced_ids.add(trade_id)

        # Sync history deals
        to_date = datetime.now() + timedelta(days=1)
        # Set to 2020-01-01 to ensure we fetch EVERYTHING for debugging
        from_date = datetime(2020, 1, 1)
        
        deals = await mt5_service.get_deals(from_date=from_date, to_date=to_date)
        if deals is None:
             raise HTTPException(status_code=503, detail="Failed to connect to MT5 or fetch deals")
        
        logger.info(f"Fetched {len(deals)} deals from MT5 (Range: 2020-01-01 to {to_date})")

        # 修正: ENTRYとEXITディールの両方を処理する
        for deal in deals:
            # Debug log for every deal with full details
            logger.info(f"Processing Deal: Ticket={deal.get('ticket')}, PositionID={deal.get('position_id')}, Entry={deal.get('entry')}, Type={deal.get('type')}, Volume={deal.get('volume')}, Price={deal.get('price')}, Time={deal.get('time')}")

            position_id = deal.get('position_id')
            trade_id = str(position_id if position_id is not None else deal.get('ticket'))

            existing = await db.execute(select(TradeLog).where(TradeLog.trade_id == trade_id))
            obj = existing.scalar()

            # ENTRYディールの処理（新規ポジション）
            if deal.get('entry') == 0:  # ENTRY
                # volumeの検証を最初に行う（オブジェクト作成前）
                volume = deal.get('volume')
                if volume is None or volume == 0:
                    logger.warning(f"Invalid volume for entry deal {deal.get('ticket')}: {volume}. Skipping.")
                    continue

                if not obj:
                    obj = TradeLog(trade_id=trade_id)
                    db.add(obj)

                obj.timestamp = deal['time']  # エントリー時刻
                obj.direction = "LONG" if deal['type'] == 0 else "SHORT"  # 0=BUY, 1=SELL
                obj.entry_price = deal['price']  # エントリー価格
                obj.position_size = volume
                obj.entry_ticket = str(deal.get('ticket'))
                obj.position_id = str(position_id) if position_id is not None else None

                synced_ids.add(trade_id)

            # OUT/OUT_BY ディールの処理（決済）
            elif deal.get('entry') in [1, 2]:  # OUT, OUT_BY
                if not obj:
                    # ENTRYディールがない場合は警告してスキップ
                    logger.warning(f"Exit deal without entry: position_id={position_id}, ticket={deal.get('ticket')}")
                    # または、同じposition_idのENTRYディールを検索
                    entry_deal = next((d for d in deals if d.get('position_id') == position_id and d.get('entry') == 0), None)
                    if entry_deal:
                        # volumeの検証
                        entry_volume = entry_deal.get('volume')
                        if entry_volume is None or entry_volume == 0:
                            logger.warning(f"Invalid volume in entry_deal for position {position_id}: {entry_volume}. Skipping this trade.")
                            continue

                        # ENTRYディールが見つかった場合、先に処理
                        logger.info(f"Found entry deal for position {position_id}, creating trade record")
                        obj = TradeLog(trade_id=trade_id)
                        obj.timestamp = entry_deal['time']
                        obj.direction = "LONG" if entry_deal['type'] == 0 else "SHORT"
                        obj.entry_price = entry_deal['price']
                        obj.position_size = entry_volume
                        obj.entry_ticket = str(entry_deal.get('ticket'))
                        obj.position_id = str(position_id) if position_id is not None else None
                        db.add(obj)
                    else:
                        continue  # ENTRYディールが見つからない場合はスキップ

                # クローズ情報の更新
                obj.exit_price = deal['price']
                profit = deal.get('profit', 0.0) + deal.get('swap', 0.0) + deal.get('commission', 0.0)
                obj.profit_loss_amount = profit
                obj.exit_ticket = str(deal.get('ticket')) if deal.get('ticket') is not None else obj.exit_ticket

                # 取引期間の計算
                if obj.timestamp and obj.timestamp < deal['time']:
                    obj.trade_duration_minutes = int((deal['time'] - obj.timestamp).total_seconds() / 60)

                synced_ids.add(trade_id)

        await db.commit()
        
        # Return all trades after sync
        return await get_trades(limit=50, db=db)

    except Exception as e:
        logger.error(f"Error syncing trades: {e}")
        raise HTTPException(status_code=500, detail=str(e))
