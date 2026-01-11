import logging
import asyncio
from datetime import datetime
import pandas as pd
import MetaTrader5 as mt5
from concurrent.futures import ThreadPoolExecutor
import functools
from ..config import settings

logger = logging.getLogger(__name__)

# Create a dedicated single-thread executor for all MT5 operations to ensure thread affinity/serialization
_mt5_executor = ThreadPoolExecutor(max_workers=1)

async def _run_mt5(func, *args, timeout: float = None, **kwargs):
    """
    Helper to run blocking MT5 calls in the dedicated executor with timeout

    Args:
        func: MT5 function to call
        timeout: Timeout in seconds (defaults to settings.mt5_operation_timeout)
        *args, **kwargs: Arguments to pass to the function
    """
    loop = asyncio.get_running_loop()
    if timeout is None:
        timeout = settings.mt5_operation_timeout

    try:
        return await asyncio.wait_for(
            loop.run_in_executor(_mt5_executor, functools.partial(func, *args, **kwargs)),
            timeout=timeout
        )
    except asyncio.TimeoutError:
        logger.error(f"MT5 operation {func.__name__} timed out after {timeout}s")
        return None

class MT5Service:
    CONNECTION_RETRY_INTERVAL = 60.0  # Seconds to wait before retrying connection

    def __init__(self, symbol: str = None):
        self.symbol = symbol or settings.mt5_symbol
        self.connected = False
        self.last_connection_attempt = 0

    async def initialize(self) -> bool:
        """Initialize connection to MT5 terminal"""
        
        # Circuit breaker / Backoff
        import time
        current_time = time.time()
        if not self.connected and (current_time - self.last_connection_attempt < self.CONNECTION_RETRY_INTERVAL):
            logger.debug(f"MT5 initialize skipped (backoff active). Next retry in {int(self.CONNECTION_RETRY_INTERVAL - (current_time - self.last_connection_attempt))}s")
            return False

        logger.info("Initializing MT5 service...")
        self.last_connection_attempt = current_time

        # Run synchronous mt5.initialize in the dedicated thread with timeout
        try:
            init_success = await _run_mt5(
                mt5.initialize,
                timeout=settings.mt5_connection_timeout
            )

            if not init_success:
                logger.error(f"MT5 initialization failed, error code = {mt5.last_error()}")
                self.connected = False
                return False
        except Exception as e:
            logger.error(f"MT5 initialization unexpected error: {e}")
            self.connected = False
            return False
        
        # Ensure symbol is selected in Market Watch
        def ensure_symbol(sym):
            if not mt5.symbol_select(sym, True):
                logger.warning(f"Failed to select {sym}. Trying to find match...")
                # Try to find matching symbols (e.g. with suffixes)
                symbols = mt5.symbols_get()
                match = None
                if symbols:
                    for s in symbols:
                        if "USDJPY" in s.name and "JPY" in s.name:
                            match = s.name
                            logger.debug(f"Found similar symbol: {s.name}")
                            break

                if match:
                    logger.info(f"Switching symbol from {sym} to {match}")
                    if mt5.symbol_select(match, True):
                        logger.info(f"Successfully selected {match}")
                        return match
                    else:
                        logger.error(f"Failed to select {match}")
                        return sym
                else:
                     logger.error(f"Symbol {sym} not found in MT5.")
                     return sym
            else:
                 logger.debug(f"Symbol {sym} selected successfully.")
                 return sym

        try:
            self.symbol = await _run_mt5(ensure_symbol, self.symbol, timeout=10.0)
        except Exception as e:
            logger.error(f"Symbol selection error: {e}")
            # Don't fail completely, just use default symbol

        self.connected = True
        try:
            terminal_info = await _run_mt5(mt5.terminal_info, timeout=5.0)
            if terminal_info:
                logger.info(f"MT5 initialized successfully. Terminal: {terminal_info}")
        except Exception as e:
            logger.warning(f"Could not get terminal info: {e}")
            
        return True

    async def shutdown(self):
        """Shutdown MT5 connection"""
        await _run_mt5(mt5.shutdown)
        self.connected = False
        logger.info("MT5 connection closed")

    async def get_current_price(self) -> dict:
        """Get current bid/ask price"""
        if not self.connected:
            if not await self.initialize():
                return None

        tick = await _run_mt5(mt5.symbol_info_tick, self.symbol, timeout=5.0)

        if tick is None:
            logger.error(f"Failed to get tick for {self.symbol}")
            return None

        return {
            "symbol": self.symbol,
            "time": datetime.fromtimestamp(tick.time),
            "bid": tick.bid,
            "ask": tick.ask,
            "last": tick.last,
            "volume": tick.volume
        }

    async def get_historical_data(self, timeframe, num_bars: int = 1000) -> pd.DataFrame:
        """Get historical OHLC data"""
        if not self.connected:
            if not await self.initialize():
                return pd.DataFrame()

        # timeframe mapping (simplification)
        tf_map = {
            "M1": mt5.TIMEFRAME_M1,
            "M5": mt5.TIMEFRAME_M5,
            "M15": mt5.TIMEFRAME_M15,
            "H1": mt5.TIMEFRAME_H1,
            "H4": mt5.TIMEFRAME_H4,
            "D1": mt5.TIMEFRAME_D1,
        }

        mt5_tf = tf_map.get(timeframe, mt5.TIMEFRAME_H1)

        # タイムアウトを統一（大量データの場合は長めに）
        timeout = 15.0 if num_bars > 1000 else 10.0
        rates = await _run_mt5(
            mt5.copy_rates_from_pos,
            self.symbol,
            mt5_tf,
            0,
            num_bars,
            timeout=timeout
        )

        if rates is None:
            logger.error(f"Failed to get rates for {self.symbol}")
            return pd.DataFrame()

        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        return df

    async def is_market_open(self) -> bool:
        """Check if market is effectively open (connected and recent ticks)"""
        if not self.connected:
            if not await self.initialize():
                return False

        # check time of last quote
        tick = await _run_mt5(mt5.symbol_info_tick, self.symbol, timeout=5.0)

        if tick is None:
            logger.debug(f"is_market_open: Tick invalid (None) for {self.symbol}")
            return False

        last_tick_time = datetime.fromtimestamp(tick.time)
        now = datetime.now()

        # If the last tick is older than 5 minutes, assume market is closed
        # Note: weekends this will definitely be true
        diff = now - last_tick_time

        logger.debug(f"Market Status Check: Last tick: {last_tick_time}, Now: {now}, Diff: {diff.total_seconds()}s")

        if diff.total_seconds() > 300:  # 5 minutes
            logger.info(f"Market considered CLOSED (Tick age: {diff.total_seconds()}s > 300s)")
            return False

        return True

    async def get_deals(self, from_date: datetime = None, to_date: datetime = None) -> list:
        """Get processed deals (closed trades) from history"""
        if not self.connected:
            # Attempt one last initialize if not connected
            if not await self.initialize():
                logger.error("Cannot get deals: MT5 not connected")
                return None

        if from_date is None:
            from_date = datetime(2024, 1, 1)  # Default to some past date
        if to_date is None:
            to_date = datetime.now()

        # 履歴取得は時間がかかる可能性があるため、長めのタイムアウト
        deals = await _run_mt5(
            mt5.history_deals_get,
            from_date,
            to_date,
            timeout=15.0
        )

        if deals is None:
            logger.warning(f"No deals found or error getting deals: {mt5.last_error()}")
            return []

        processed_deals = []
        for deal in deals:
            deal_dict = deal._asdict()
            deal_dict['time'] = datetime.fromtimestamp(deal_dict['time'])
            processed_deals.append(deal_dict)

        return processed_deals

    async def get_positions(self) -> list:
        """Get current open positions"""
        if not self.connected:
            if not await self.initialize():
                logger.error("Cannot get positions: MT5 not connected")
                return None

        positions = await _run_mt5(mt5.positions_get, timeout=5.0)

        if positions is None:
            logger.warning(f"No positions found or error: {mt5.last_error()}")
            return []

        processed_positions = []
        for pos in positions:
            pos_dict = pos._asdict()
            pos_dict['time'] = datetime.fromtimestamp(pos_dict['time'])
            processed_positions.append(pos_dict)

        return processed_positions

mt5_service = MT5Service()

# Mock Service removed

# Use mock if MT5 lib works but connection fails, or prompt to use mock
# For now, we enforce mock if connection fails or for verification:
# Wrapper to choose between Real and Mock based on connection success
class MT5ServiceProvider:
    def __init__(self):
        self.service = None

    async def get_service(self):
        if self.service:
            return self.service
        
        # Try to initialize real MT5 (connect to running instance)
        real_service = MT5Service()
        if await real_service.initialize():
            # Check if it is the correct terminal
            try:
                info = await _run_mt5(mt5.terminal_info)
                logger.debug(f"Connected to MT5. Path: {info.path}")
                logger.info(f"Connected to MT5 at {info.path}")

                # Check if we should enforce OANDA path
                target_path = r"C:\Program Files\OANDA MetaTrader 5"
                if target_path.lower() in info.path.lower():
                     logger.debug("Confirmed OANDA MT5 instance.")
                     self.service = real_service
                     return self.service
                else:
                     logger.warning(f"Connected MT5 is NOT OANDA ({info.path}). attempting to switch...")
                     await real_service.shutdown()
                     # Fall through to auto-launch logic
            except Exception as e:
                logger.debug(f"Error checking terminal info: {e}")
            
            pass
        
        # Connection failed, try to auto-launch
        logger.info("MT5 not running. Attempting to auto-launch...")
        
        common_paths = [
            r"C:\Program Files\OANDA MetaTrader 5\terminal64.exe",
            r"C:\Program Files\MetaTrader 5\terminal64.exe",
            r"C:\Program Files (x86)\MetaTrader 5\terminal64.exe"
        ]
        
        import os
        import time
        for path in common_paths:
            if os.path.exists(path):
                logger.debug(f"Found MT5 at {path}. Launching...")
                logger.info(f"Found MT5 at {path}. Launching...")
                # Note: mt5.initialize(path=...) triggers the launch
                # Wrap this blocking launch call!
                try:
                    if await asyncio.wait_for(
                        _run_mt5(mt5.initialize, path=path),
                        timeout=60.0 # Launching might take longer than simple connect
                    ):
                        logger.debug("MT5 Launched. Waiting for network connection...")
                        logger.info("MT5 Launched. Waiting for network connection...")

                        # Wait up to 30 seconds for connection
                        for i in range(30):
                             info = await _run_mt5(mt5.terminal_info)
                             if info.connected:
                                 logger.info("MT5 Connected to Server")
                                 break
                             logger.info(f"Waiting for connection... {i+1}/30")
                             await asyncio.sleep(1)

                        info = await _run_mt5(mt5.terminal_info)
                        if not info.connected:
                             logger.warning("MT5 initialized but NOT connected to server. Data might be stale.")

                        self.service = real_service
                        self.service.connected = True
                        return self.service
                    else:
                        logger.error(f"Failed to launch MT5 at {path}: {mt5.last_error()}")
                except asyncio.TimeoutError:
                    logger.error(f"MT5 launch timed out at {path}")

        # Fallback to connection failure
        logger.error("Real MT5 connection and auto-launch failed. Mock fallback is disabled.")
        return real_service

    # Proxy methods to the underlying service
    def __getattr__(self, name):
        # This allows us to use mt5_service.get_current_price() directly
        # But we need to ensure service is initialized. 
        # Since __getattr__ is sync, we can't await here.
        # This requires the consumer to ensure initialization or we handle it differently.
        # For simplicity in this existing codebase, we'll return a proxy or 
        # we can instruct the main entry point to initialize the provider.
        return getattr(self.service, name)

# Singleton Instance
# Ideally, we should initialize this asynchronously. 
# But to keep changes minimal, we'll create a proxy object that delegates.

class ServiceProxy:
    def __init__(self):
        self._provider = MT5ServiceProvider()
        self._impl = None

    async def _ensure_impl(self):
        if not self._impl:
            self._impl = await self._provider.get_service()
    
    async def initialize(self):
        await self._ensure_impl()
        return await self._impl.initialize()

    async def shutdown(self):
        if self._impl:
            await self._impl.shutdown()

    async def get_current_price(self):
        await self._ensure_impl()
        return await self._impl.get_current_price()

    @property
    def connected(self):
        return self._impl.connected if self._impl else False

    async def get_historical_data(self, *args, **kwargs):
        await self._ensure_impl()
        return await self._impl.get_historical_data(*args, **kwargs)

    async def get_deals(self, *args, **kwargs):
        await self._ensure_impl()
        return await self._impl.get_deals(*args, **kwargs)

    async def get_positions(self, *args, **kwargs):
        await self._ensure_impl()
        return await self._impl.get_positions(*args, **kwargs)

    async def is_market_open(self):
        await self._ensure_impl()
        return await self._impl.is_market_open()

mt5_service = ServiceProxy()
