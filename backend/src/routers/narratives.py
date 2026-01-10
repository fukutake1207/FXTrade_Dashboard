from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import pytz

from ..database import get_db
from ..models import HistoricalNarrative
from ..services.gemini_service import gemini_service
from ..services.claude_service import claude_service
from ..services.narrative_provider import get_provider
from ..services.market_data_service import market_data_service
from ..services.correlation_analyzer import correlation_analyzer
from ..services.mt5_service import mt5_service
from ..services.session_service import session_service

import asyncio

router = APIRouter(
    prefix="/narratives",
    tags=["narratives"]
)

class NarrativeResponse(BaseModel):
    id: str
    timestamp: datetime
    content: str

    class Config:
        from_attributes = True

class NarrativeHistoryResponse(BaseModel):
    id: str
    timestamp: datetime
    session: str
    content: str

    class Config:
        from_attributes = True

@router.get("/history", response_model=List[NarrativeHistoryResponse])
async def get_narrative_history(
    session: Optional[str] = None,
    limit: int = 10,
    skip: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """
    Get narrative history with optional session filter.
    Returns most recent narratives first.
    """
    query = select(HistoricalNarrative).order_by(desc(HistoricalNarrative.generated_at))

    if session:
        query = query.where(HistoricalNarrative.session == session)

    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    narratives = result.scalars().all()

    return [
        NarrativeHistoryResponse(
            id=n.narrative_id,
            timestamp=n.generated_at,
            session=n.session,
            content=n.content
        )
        for n in narratives
    ]

@router.get("/latest", response_model=Optional[NarrativeResponse])
async def get_latest_narrative(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(HistoricalNarrative).order_by(desc(HistoricalNarrative.generated_at)).limit(1)
    )
    narrative = result.scalar_one_or_none()
    
    if not narrative:
        return None
        
    return NarrativeResponse(
        id=narrative.narrative_id,
        timestamp=narrative.generated_at,
        content=narrative.content
    )

@router.post("/generate", response_model=NarrativeResponse)
async def generate_narrative(db: AsyncSession = Depends(get_db)):
    # 1. Gather Context Data
    # We need to gather data from various services to build the context

    # USDJPY Current Price from MT5
    usdjpy_tick = await mt5_service.get_current_price()
    if not usdjpy_tick:
        raise HTTPException(status_code=503, detail="MT5に接続できないためナラティブを生成できませんでした")

    usdjpy_current = {
        "bid": usdjpy_tick.get('bid', 0),
        "ask": usdjpy_tick.get('ask', 0),
        "mid": (usdjpy_tick.get('bid', 0) + usdjpy_tick.get('ask', 0)) / 2
    }

    # Prices (Current - Other Markets)
    market_prices = await market_data_service.get_current_prices()

    # Session Status
    session_status = session_service.get_session_status()

    # Correlations (need historical retrieval, simplified here to just reuse logic or fetch fresh)
    # For speed, let's just get the last known correlation from analyzer if cached, or recalculate quickly
    # Re-using the logic from correlations router somewhat duplicated here,
    # ideally should be in a cohesive service method.
    mt5_history = await mt5_service.get_historical_data("D1", num_bars=50)
    market_history = await market_data_service.get_historical_returns(days=30)

    correlations = {}
    if not mt5_history.empty and not market_history.empty:
        correlations = correlation_analyzer.analyze_correlations(mt5_history, market_history)

    # 日本時間を取得
    jst = pytz.timezone('Asia/Tokyo')
    current_time_jst = datetime.now(jst)

    context_data = {
        "usdjpy_current_price": usdjpy_current,
        "market_prices": market_prices,
        "correlations": correlations,
        "active_sessions": [k for k,v in session_status.items() if v.is_active],
        "timestamp": current_time_jst.strftime('%Y年%m月%d日 %H:%M JST（日本時間）'),
        "timezone": "Asia/Tokyo (JST, UTC+9)"
    }
    
    # 3. Call AI Provider (default: Gemini, switchable via env)
    provider = get_provider()
    if provider == "claude":
        content = await claude_service.generate_market_narrative(context_data)
    else:
        content = await gemini_service.generate_market_narrative(context_data)
    
    # 4. Save to DB
    import uuid
    new_narrative = HistoricalNarrative(
        narrative_id=str(uuid.uuid4()),
        generated_at=datetime.now(),
        session=max(session_status, key=lambda k: session_status[k].is_active) if any(s.is_active for s in session_status.values()) else "global",
        content=content,
        market_data_snapshot=str(list(market_prices.keys())) # Simple string representation
    )
    
    db.add(new_narrative)
    await db.commit()
    await db.refresh(new_narrative)
    
    # Map back to response model fields (alias hacking or just changing response model)
    # The response model expects 'timestamp'. We should update it too or map it.
    # Actually, let's just cheat and return an object with the right fields for Pydantic
    return NarrativeResponse(
        id=new_narrative.narrative_id,
        timestamp=new_narrative.generated_at,
        content=new_narrative.content
    )
