from fastapi import FastAPI
from dotenv import load_dotenv
import logging
from datetime import datetime
from .services.mt5_service import mt5_service
from .config import settings

# Configure logging from settings
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# 設定の検証（起動時に必須チェック）
try:
    settings.validate_required_keys()
    logger.info("Configuration validated successfully")
except ValueError as e:
    logger.critical(f"Configuration Error: {e}")
    if settings.is_production:
        raise RuntimeError(f"Cannot start application: {e}")
    else:
        logger.warning("Starting in development mode despite configuration issues")

from fastapi.middleware.cors import CORSMiddleware
from .routers import prices, trades, correlations, sessions, narratives, scenarios, alerts, settings as settings_router
from .services.data_collector import data_collector
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import asyncio

app = FastAPI(
    title="FX Discretionary Trading Cockpit API",
    description="Backend API for FX Trade Dashboard",
    version="1.0.0"
)

# CORS configuration from settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers (重複を削除)
app.include_router(prices.router)
app.include_router(trades.router)
app.include_router(correlations.router)
app.include_router(sessions.router)
app.include_router(narratives.router)
app.include_router(scenarios.router)
app.include_router(alerts.router)
app.include_router(settings_router.router)

# Mount frontend static files
from fastapi.staticfiles import StaticFiles
frontend_dist = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend", "dist")
if os.path.exists(frontend_dist):
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="static")
else:
    logger.warning(f"Frontend dist not found at {frontend_dist}")

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
                    success = await data_collector.collect_and_store_prices(db)
                if success:
                    logger.info("Initial data collection completed.")
                else:
                    logger.warning("Initial data collection did not complete successfully.")
            except Exception as e:
                logger.error(f"Error during data collection: {e}", exc_info=True)

        def handle_task_exception(task):
            """バックグラウンドタスクの例外処理"""
            try:
                task.result()
            except Exception as e:
                logger.error(f"Background task failed: {e}", exc_info=True)

        # 即座に一度実行（バックグラウンドで）
        logger.info("Triggering background data collection.")
        task = asyncio.create_task(run_collection())
        task.add_done_callback(handle_task_exception)

        # 設定ファイルで指定された間隔でスケジュール（デフォルト10分）
        scheduler.add_job(
            run_collection,
            'interval',
            minutes=settings.data_collection_interval_minutes
        )
        scheduler.start()
        logger.info(f"Scheduler started (interval: {settings.data_collection_interval_minutes} minutes)")
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
    from sqlalchemy import text

    db_status = "unknown"
    db_healthy = False

    try:
        # 実際にSQLを実行してDBの応答を確認
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            row = result.fetchone()
            if row and row[0] == 1:
                db_status = "connected"
                db_healthy = True
            else:
                db_status = "unexpected_result"
    except Exception as e:
        db_status = f"error: {str(e)}"
        logger.error(f"Health check DB error: {e}")

    # 全体の健全性判定
    overall_healthy = db_healthy and mt5_service.connected

    return {
        "status": "healthy" if overall_healthy else "unhealthy",
        "mt5_connected": mt5_service.connected,
        "db_status": db_status,
        "timestamp": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="127.0.0.1", port=8000, reload=True)
