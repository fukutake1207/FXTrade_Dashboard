from fastapi import FastAPI
from dotenv import load_dotenv, find_dotenv
import os
import logging
from datetime import datetime
from .services.mt5_service import mt5_service

# Configure logging to see valid output
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

env_file = find_dotenv()
logger.info(f"Loading .env from: {env_file}")
load_dotenv(env_file)

# Check if key is loaded immediately
key = os.getenv("GEMINI_API_KEY")
if key:
    logger.info("GEMINI_API_KEY loaded successfully.")
else:
    logger.error("GEMINI_API_KEY NOT FOUND after loading .env!")

from fastapi.middleware.cors import CORSMiddleware
from .routers import prices, trades, correlations, sessions, narratives, scenarios, alerts, settings
from .services.data_collector import data_collector
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import asyncio

app = FastAPI(
    title="FX Discretionary Trading Cockpit API",
    description="Backend API for FX Trade Dashboard",
    version="1.0.0"
)

# CORS configuration
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(prices.router)
app.include_router(trades.router)
app.include_router(correlations.router)
app.include_router(sessions.router)
app.include_router(narratives.router)
app.include_router(scenarios.router)
app.include_router(alerts.router)
app.include_router(settings.router)

# Scheduler for background tasks
scheduler = AsyncIOScheduler()

@app.on_event("startup")
async def start_scheduler():
    logger.info("Application startup initiated.")
    try:
        # Create tables
        logger.info("Initializing database tables...")
        from .database import engine, Base
        from . import models # Ensure models are loaded
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables initialized.")

        # 起動時にデータを更新してフレッシュに保つ
        from .database import AsyncSessionLocal
        
        async def run_collection():
            logger.info("Starting initial data collection...")
            try:
                async with AsyncSessionLocal() as db:
                    await data_collector.collect_and_store_prices(db)
                logger.info("Initial data collection completed.")
            except Exception as e:
                logger.error(f"Error during initial data collection: {e}")
                
        # 即座に一度実行（バックグラウンドで）
        logger.info("Triggering background data collection.")
        asyncio.create_task(run_collection())
        
        # 15分ごとにスケジュール
        scheduler.add_job(run_collection, 'interval', minutes=15)
        scheduler.start()
        logger.info("Scheduler started.")
    except Exception as e:
        logger.critical(f"Critical error during startup: {e}")
        # We might want to re-raise or handle this, but for now log it clearly.

@app.get("/")
async def root():
    return {"message": "Welcome to FX Trade Dashboard API"}

@app.get("/health")
async def health_check():
    from .services.mt5_service import mt5_service
    from .database import engine
    
    db_status = "unknown"
    try:
        # Simple DB check
        async with engine.connect() as conn:
            # await conn.execute("SELECT 1")
            db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"

    return {
        "status": "ok",
        "mt5_connected": mt5_service.connected,
        "db_status": db_status,
        "timestamp": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="127.0.0.1", port=8000, reload=True)
