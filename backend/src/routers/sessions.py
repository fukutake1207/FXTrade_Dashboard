from fastapi import APIRouter
from typing import Dict, List
from ..services.session_service import session_service, SessionInfo
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(
    prefix="/sessions",
    tags=["sessions"]
)

class SessionResponse(BaseModel):
    current_time: str
    timeline_progress: float
    sessions: Dict[str, SessionInfo]

from ..services.mt5_service import mt5_service

@router.get("/status", response_model=SessionResponse)
async def get_session_status():
    # Check if market is actually open (MT5 connectivity + ticks)
    market_open = await mt5_service.is_market_open()
    
    # If market is closed (e.g. weekend), force sessions to be closed
    status = session_service.get_session_status(force_closed=not market_open)
    
    progress = session_service.get_timeline_progress()
    current_time_str = datetime.now(session_service.timezone).strftime("%H:%M")
    
    return {
        "current_time": current_time_str,
        "timeline_progress": progress,
        "sessions": status
    }
