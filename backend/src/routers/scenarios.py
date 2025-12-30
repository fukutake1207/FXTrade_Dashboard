from fastapi import APIRouter, Depends
from typing import List
from ..services.scenario_service import scenario_service, MarketScenario
from ..services.market_data_service import market_data_service

router = APIRouter(
    prefix="/scenarios",
    tags=["scenarios"]
)

@router.get("/current", response_model=List[MarketScenario])
async def get_current_scenarios():
    prices = await market_data_service.get_current_prices()
    usdjpy_price = prices.get('USDJPY', {}).get('price', 0.0)
    
    if usdjpy_price == 0.0:
        return []

    scenarios = await scenario_service.generate_scenarios(usdjpy_price)
    return scenarios
