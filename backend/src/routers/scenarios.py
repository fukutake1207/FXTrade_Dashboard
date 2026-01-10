from fastapi import APIRouter, Depends, HTTPException
from typing import List
from ..services.scenario_service import scenario_service, MarketScenario
from ..database import require_mt5

router = APIRouter(
    prefix="/scenarios",
    tags=["scenarios"]
)

@router.get("/current", response_model=List[MarketScenario])
async def get_current_scenarios(mt5_service = Depends(require_mt5)):
    tick = await mt5_service.get_current_price()
    if not tick:
        raise HTTPException(status_code=503, detail="MT5に接続できないためシナリオを取得できませんでした")
    usdjpy_price = tick.get('bid') if tick else 0.0
    
    if usdjpy_price == 0.0:
        return []

    scenarios = await scenario_service.generate_scenarios(usdjpy_price)
    return scenarios
