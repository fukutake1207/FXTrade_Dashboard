import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..models import PriceStatistic
from .mt5_service import mt5_service
import logging

logger = logging.getLogger(__name__)

class DataCollectorService:
    @staticmethod
    async def collect_and_store_prices(db: AsyncSession):
        """Collect current prices and update statistics"""
        # Ensure MT5 is connected
        logger.info("Starting Price Statistics Collection...")
        logger.debug("Initializing MT5... Path search active.")
        if not await mt5_service.initialize():
            logger.error("Could not connect to MT5 - Skipping collection")
            return False

        # Get historical data for statistics calculation (last 4 weeks)
        # Using H1 data for general stats
        logger.debug("Fetching historical data (H1)...")
        df_h1 = await mt5_service.get_historical_data("H1", num_bars=24*5*4) # approx 4 weeks
        
        if df_h1.empty:
            logger.warning("No historical data received")
            # return  <-- Allow proceeding to get_current_price even if history fails

        # Calculate current day statistics
        current_date = datetime.utcnow().date()
        
        stat = None
        has_full_stats = False
        
        if df_h1.empty:
            logger.warning("No historical data received - attempting fallback to current tick")
            # Fallback to current tick only
            tick = await mt5_service.get_current_price()
            if tick:
                stat = PriceStatistic(
                    date=current_date,
                    session="tokyo", 
                    open_price=tick['bid'], 
                    high_price=tick['bid'],
                    low_price=tick['bid'],
                    close_price=tick['bid'],
                    range_pips=0,
                    volatility=0,
                    last_updated=datetime.utcnow()
                )
        else:
            # Filter for today (UTC)
            if 'time' in df_h1.columns:
                df_today = df_h1[df_h1['time'].dt.date == current_date].copy()
            else:
                df_today = pd.DataFrame() # Handle case where DF is not empty but time missing? Should not happen if get_historical returns correct DF structure
            
            if df_today.empty:
                # Fallback if no full H1 bars for today
                tick = await mt5_service.get_current_price()
                if tick:
                    stat = PriceStatistic(
                        date=current_date,
                        session="tokyo",
                        open_price=tick['bid'],
                        high_price=tick['bid'],
                        low_price=tick['bid'],
                        close_price=tick['bid'],
                        range_pips=0,
                        volatility=0,
                        last_updated=datetime.utcnow()
                    )
            else:
                 # Calculate detailed stats
                high = df_today['high'].max()
                low = df_today['low'].min()
                open_p = df_today['open'].iloc[0]
                close_p = df_today['close'].iloc[-1]
                range_pips = (high - low) * 100
                
                df_today['range'] = df_today['high'] - df_today['low']
                volatility = df_today['range'].mean() * 100

                stat = PriceStatistic(
                    stat_id=f"stat_{current_date}",
                    date=current_date,
                    session="tokyo",
                    open_price=open_p,
                    high_price=high,
                    low_price=low,
                    close_price=close_p,
                    range_pips=range_pips,
                    volatility=volatility,
                    last_updated=datetime.utcnow()
                )
                has_full_stats = True

        if not stat:
            logger.warning("Failed to calculate statistics - no data available")
            return False

        # Upsert logic (check if exists, update or insert)
        query = select(PriceStatistic).where(PriceStatistic.date == current_date)
        result = await db.execute(query)
        existing_stat = result.scalars().first()

        if existing_stat:
            if existing_stat.high_price is None:
                existing_stat.high_price = stat.high_price
            else:
                existing_stat.high_price = max(existing_stat.high_price, stat.high_price)
            if existing_stat.low_price is None:
                existing_stat.low_price = stat.low_price
            else:
                existing_stat.low_price = min(existing_stat.low_price, stat.low_price)
            existing_stat.close_price = stat.close_price
            if has_full_stats:
                existing_stat.range_pips = stat.range_pips
                existing_stat.volatility = stat.volatility
            
            existing_stat.last_updated = stat.last_updated
        else:
             # Since stat_id is primary key, handle generation if not in basic stat
            if not stat.stat_id:
                import uuid
                stat.stat_id = str(uuid.uuid4())
            db.add(stat)
        
        await db.commit()
        logger.info(f"Price statistics updated for {current_date}")
        return True

data_collector = DataCollectorService()
