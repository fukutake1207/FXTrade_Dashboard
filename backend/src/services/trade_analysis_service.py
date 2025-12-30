from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from ..models import TradeLog

class TradeAnalysisService:
    async def get_performance_stats(self, db: AsyncSession) -> Dict[str, Any]:
        result = await db.execute(select(TradeLog))
        trades = result.scalars().all()
        
        total_trades = len(trades)
        if total_trades == 0:
            return {
                "total_trades": 0,
                "win_rate": 0.0,
                "profit_factor": 0.0,
                "total_pnl": 0.0
            }
            
        wins = [t for t in trades if (t.profit_loss_amount or 0) > 0]
        losses = [t for t in trades if (t.profit_loss_amount or 0) < 0]
        
        win_count = len(wins)
        loss_count = len(losses)
        
        gross_profit = sum(t.profit_loss_amount or 0 for t in wins)
        gross_loss = abs(sum(t.profit_loss_amount or 0 for t in losses))
        
        win_rate = (win_count / total_trades) * 100 if total_trades > 0 else 0
        profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else 9.99 # Cap or inf
        
        return {
            "total_trades": total_trades,
            "win_rate": round(win_rate, 1),
            "profit_factor": round(profit_factor, 2),
            "total_pnl": round(gross_profit - gross_loss, 2),
            "win_count": win_count,
            "loss_count": loss_count
        }

trade_analysis_service = TradeAnalysisService()
