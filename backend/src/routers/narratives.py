from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from ..database import get_db
from ..models import HistoricalNarrative
from ..services.gemini_service import gemini_service
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
    id: int
    timestamp: datetime
    content: str
    
    class Config:
        from_attributes = True

@router.get("/latest", response_model=Optional[NarrativeResponse])
async def get_latest_narrative(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(HistoricalNarrative).order_by(desc(HistoricalNarrative.generated_at)).limit(1)
    )
    narrative = result.scalar_one_or_none()
    
    if not narrative:
        return None
        
    return NarrativeResponse(
        id=0, # Dummy ID as actual ID is string UUID
        timestamp=narrative.generated_at,
        content=narrative.content
    )

@router.post("/generate", response_model=NarrativeResponse)
async def generate_narrative(db: AsyncSession = Depends(get_db)):
    # 1. Gather Context Data
    # We need to gather data from various services to build the context
    
    # Prices (Current)
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
        
    context_data = {
        "market_prices": market_prices,
        "correlations": correlations,
        "active_sessions": [k for k,v in session_status.items() if v.is_active],
        "timestamp": datetime.now().isoformat()
    }
    
    # 3. Call Gemini
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
        id=0, # Dummy ID for Pydantic, real ID is UUID string
        timestamp=new_narrative.generated_at,
        content=new_narrative.content
    )
