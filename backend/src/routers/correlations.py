from fastapi import APIRouter, Depends
from typing import Dict, List, Any
from ..services.market_data_service import market_data_service
from ..services.correlation_analyzer import correlation_analyzer
from ..services.mt5_service import mt5_service
from pydantic import BaseModel
import asyncio

router = APIRouter(
    prefix="/correlations",
    tags=["correlations"]
)

class CorrelationData(BaseModel):
    correlations: Dict[str, Any]
    market_status: Dict[str, Any]
    insights: List[str]

@router.get("/overview", response_model=CorrelationData)
async def get_correlation_overview():
    # 1. Get Market Data (Current Prices)
    market_prices = await market_data_service.get_current_prices()
    
    # 2. Get Historical Data for Correlation Calculation
    # Fetch parallelly
    mt5_history_task = mt5_service.get_historical_data("D1", num_bars=50)
    market_history_task = market_data_service.get_historical_returns(days=30)
    
    usdjpy_history, market_history = await asyncio.gather(mt5_history_task, market_history_task)
    
    correlations = {}
    insights = []

    if not usdjpy_history.empty and not market_history.empty:
        # 3. Calculate Correlations
        correlations = correlation_analyzer.analyze_correlations(usdjpy_history, market_history)
        
        # 4. Generate Insights
        # Prepare current moves for insight generation
        current_moves = {k: v.get('change_pct', 0) for k, v in market_prices.items()}
        insights = correlation_analyzer.generate_insight(correlations, current_moves)
    
    return {
        "correlations": correlations,
        "market_status": market_prices,
        "insights": insights
    }
