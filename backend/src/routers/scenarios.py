from fastapi import APIRouter, Depends
from typing import List
from ..services.scenario_service import scenario_service, MarketScenario
from ..services.mt5_service import mt5_service

router = APIRouter(
    prefix="/scenarios",
    tags=["scenarios"]
)

@router.get("/current", response_model=List[MarketScenario])
async def get_current_scenarios():
    tick = await mt5_service.get_current_price()
    usdjpy_price = tick.get('bid') if tick else 0.0
    
    if usdjpy_price == 0.0:
        return []

    scenarios = await scenario_service.generate_scenarios(usdjpy_price)
    return scenarios
