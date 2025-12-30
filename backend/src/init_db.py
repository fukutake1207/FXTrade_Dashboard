import asyncio
from .database import engine, Base
from .models import TradeLog, TradeContext, HistoricalNarrative, PriceStatistic

async def init_models():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    print("Database tables created successfully.")

if __name__ == "__main__":
    asyncio.run(init_models())
