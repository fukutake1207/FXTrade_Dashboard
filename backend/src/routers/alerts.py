from fastapi import APIRouter, HTTPException
from typing import List
from pydantic import BaseModel
from ..services.alert_service import alert_service, AlertRule

router = APIRouter(
    prefix="/alerts",
    tags=["alerts"]
)

class CreateAlertRequest(BaseModel):
    symbol: str
    condition: str
    price: float
    message: str = ""

@router.get("/", response_model=List[AlertRule])
async def get_alerts():
    # Check alerts whenever list is requested (for MVP polling)
    # In production, checking should be background task
    await alert_service.check_alerts()
    return alert_service.get_alerts()

@router.post("/", response_model=AlertRule)
async def create_alert(request: CreateAlertRequest):
    return alert_service.create_alert(
        symbol=request.symbol,
        condition=request.condition,
        price=request.price,
        message=request.message
    )

@router.delete("/{alert_id}")
async def delete_alert(alert_id: str):
    success = alert_service.delete_alert(alert_id)
    if not success:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"status": "success"}
