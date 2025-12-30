from typing import List, Optional, Dict
from pydantic import BaseModel
from datetime import datetime
from ..services.market_data_service import market_data_service

class AlertRule(BaseModel):
    id: str
    symbol: str
    condition: str # 'above', 'below'
    price: float
    active: bool
    triggered: bool
    triggered_at: Optional[datetime] = None
    message: str

class AlertService:
    def __init__(self):
        # In-memory storage for MVP
        self.alerts: Dict[str, AlertRule] = {}
        self._counter = 0

    def create_alert(self, symbol: str, condition: str, price: float, message: str = "") -> AlertRule:
        self._counter += 1
        alert_id = str(self._counter)
        if not message:
            message = f"{symbol} is {condition} {price}"
            
        alert = AlertRule(
            id=alert_id,
            symbol=symbol,
            condition=condition,
            price=price,
            active=True,
            triggered=False,
            message=message
        )
        self.alerts[alert_id] = alert
        return alert

    def delete_alert(self, alert_id: str) -> bool:
        if alert_id in self.alerts:
            del self.alerts[alert_id]
            return True
        return False

    def get_alerts(self) -> List[AlertRule]:
        return list(self.alerts.values())

    async def check_alerts(self) -> List[AlertRule]:
        """
        Check all active alerts against current prices.
        Returns list of newly triggered alerts.
        """
        triggered = []
        # Fetch current prices
        prices = await market_data_service.get_current_prices()
        
        for alert in self.alerts.values():
            if not alert.active:
                continue
                
            current_price_data = prices.get(alert.symbol)
            if not current_price_data:
                continue
                
            current_price = current_price_data.get('price')
            if current_price is None:
                continue
            
            is_triggered = False
            if alert.condition == 'above' and current_price > alert.price:
                is_triggered = True
            elif alert.condition == 'below' and current_price < alert.price:
                is_triggered = True
                
            if is_triggered:
                alert.triggered = True
                alert.active = False # One-time alert
                alert.triggered_at = datetime.now()
                triggered.append(alert)
                
        return triggered

alert_service = AlertService()
