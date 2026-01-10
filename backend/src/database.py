from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

# SQLite database URL
DATABASE_URL = "sqlite+aiosqlite:///./fx_dashboard.db"

# Base class for models
Base = declarative_base()

# Async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=True, # Set to False in production
    future=True
)

# Async session factory
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

# MT5接続チェック用の依存性関数
async def require_mt5():
    """MT5接続が必要なエンドポイント用の依存性関数"""
    from .services.mt5_service import mt5_service
    from fastapi import HTTPException

    if not await mt5_service.initialize():
        raise HTTPException(
            status_code=503,
            detail="MT5に接続できません。MT5が起動しているか確認してください。"
        )
    return mt5_service
