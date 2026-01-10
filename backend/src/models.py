from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey, Text, Date
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from .database import Base
import json

# タイムゾーンポリシー: すべてのタイムスタンプはUTCで統一
# datetime.now(timezone.utc) を使用してタイムゾーン情報を保持

class TradeLog(Base):
    __tablename__ = "trade_logs"

    trade_id = Column(String, primary_key=True, index=True)
    position_id = Column(String, nullable=True, index=True)
    entry_ticket = Column(String, nullable=True, index=True)
    exit_ticket = Column(String, nullable=True, index=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    symbol = Column(String, default="USDJPY")
    direction = Column(String, nullable=False) # LONG or SHORT
    entry_price = Column(Float, nullable=False)
    exit_price = Column(Float, nullable=True)
    position_size = Column(Float, nullable=False)
    profit_loss_pips = Column(Float, nullable=True)
    profit_loss_amount = Column(Float, nullable=True)
    trade_duration_minutes = Column(Integer, nullable=True)
    pre_trade_confidence = Column(Integer, nullable=True)
    post_trade_evaluation = Column(Text, nullable=True)
    lessons_learned = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    contexts = relationship("TradeContext", back_populates="trade")

class TradeContext(Base):
    __tablename__ = "trade_contexts"

    context_id = Column(String, primary_key=True, index=True)
    trade_id = Column(String, ForeignKey("trade_logs.trade_id"))
    context_type = Column(String) # 'entry' or 'exit'
    session = Column(String, index=True)
    market_condition = Column(String)
    ai_narrative_summary = Column(Text)
    active_scenarios = Column(Text) # JSON string
    key_levels_nearby = Column(Text) # JSON string
    correlation_status = Column(Text) # JSON string
    economic_events_upcoming = Column(Text) # JSON string

    trade = relationship("TradeLog", back_populates="contexts")

    def set_active_scenarios(self, data: list):
        self.active_scenarios = json.dumps(data)

    def get_active_scenarios(self):
        return json.loads(self.active_scenarios) if self.active_scenarios else []

class HistoricalNarrative(Base):
    __tablename__ = "historical_narratives"

    narrative_id = Column(String, primary_key=True, index=True)
    generated_at = Column(DateTime, nullable=False, index=True)
    session = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    market_data_snapshot = Column(Text) # JSON string

class PriceStatistic(Base):
    __tablename__ = "price_statistics"

    stat_id = Column(String, primary_key=True, index=True)
    date = Column(Date, nullable=False, index=True)
    session = Column(String)
    open_price = Column(Float)
    high_price = Column(Float)
    low_price = Column(Float)
    close_price = Column(Float)
    range_pips = Column(Float)
    volatility = Column(Float)
    last_updated = Column(DateTime)
