import logging
import asyncio
from datetime import datetime
import pandas as pd
import MetaTrader5 as mt5
from concurrent.futures import ThreadPoolExecutor
import functools

logger = logging.getLogger(__name__)

# Create a dedicated single-thread executor for all MT5 operations to ensure thread affinity/serialization
_mt5_executor = ThreadPoolExecutor(max_workers=1)

async def _run_mt5(func, *args, **kwargs):
    """Helper to run blocking MT5 calls in the dedicated executor"""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(_mt5_executor, functools.partial(func, *args, **kwargs))

class MT5Service:
    def __init__(self, symbol: str = "USDJPY"):
        self.symbol = symbol
        self.connected = False

    async def initialize(self) -> bool:
        """Initialize connection to MT5 terminal"""
        logger.info("Initializing MT5 service...")
        
        # Run synchronous mt5.initialize in the dedicated thread with timeout
        try:
            # Wrap the blocking call with a timeout at the asyncio level
            # Note: The thread itself won't be killed, but we will stop waiting
            init_success = await asyncio.wait_for(
                _run_mt5(mt5.initialize),
                timeout=30.0
            )
            
            if not init_success:
                logger.error(f"MT5 initialization failed, error code = {mt5.last_error()}")
                self.connected = False
                return False
        except asyncio.TimeoutError:
            logger.error("MT5 initialization timed out (30s)")
            self.connected = False
            return False
        except Exception as e:
            logger.error(f"MT5 initialization unexpected error: {e}")
            self.connected = False
            return False
        
        # Ensure symbol is selected in Market Watch
        def ensure_symbol(sym):
            if not mt5.symbol_select(sym, True):
                print(f"WARN: Failed to select {sym}. Trying to find match...")
                # Try to find matching symbols (e.g. with suffixes)
                symbols = mt5.symbols_get()
                match = None
                if symbols:
                    for s in symbols:
                        if "USDJPY" in s.name and "JPY" in s.name:
                            match = s.name
                            print(f"DEBUG: Found similar symbol: {s.name}")
                            break
                
                if match:
                    print(f"INFO: Switching symbol from {sym} to {match}")
                    if mt5.symbol_select(match, True):
                        print(f"INFO: Successfully selected {match}")
                        return match
                    else:
                        print(f"ERROR: Failed to select {match}")
                        return sym
                else:
                     print(f"ERROR: Symbol {sym} not found in MT5.")
                     return sym
            else:
                 print(f"DEBUG: Symbol {sym} selected successfully.")
                 return sym

        try:
            self.symbol = await asyncio.wait_for(
                _run_mt5(ensure_symbol, self.symbol),
                timeout=10.0
            )
        except asyncio.TimeoutError:
             logger.error("Symbol selection timed out")
             # Don't fail completely, just use default symbol
        
        self.connected = True
        try:
            terminal_info = await asyncio.wait_for(_run_mt5(mt5.terminal_info), timeout=5.0)
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
            await self.initialize()

        tick = await _run_mt5(mt5.symbol_info_tick, self.symbol)
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
            await self.initialize()

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
        
        rates = await _run_mt5(mt5.copy_rates_from_pos, self.symbol, mt5_tf, 0, num_bars)
        if rates is None:
            logger.error(f"Failed to get rates for {self.symbol}")
            return pd.DataFrame()

        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        return df

    async def get_deals(self, from_date: datetime = None, to_date: datetime = None) -> list:
        """Get processed deals (closed trades) from history"""
        if not self.connected:
            # Attempt one last initialize if not connected
            if not await self.initialize():
                logger.error("Cannot get deals: MT5 not connected")
                return None # Or raise exception, returning None allows caller to handle

        if from_date is None:
            from_date = datetime(2024, 1, 1) # Default to some past date
        if to_date is None:
            to_date = datetime.now()

        # Ensure naive datetimes are handled if needed, MT5 expects somewhat flexible inputs but let's be safe
        deals = await _run_mt5(mt5.history_deals_get, from_date, to_date)
        
        if deals is None:
            logger.warning(f"No deals found or error getting deals: {mt5.last_error()}")
            return []

        processed_deals = []
        for deal in deals:
            # We only care about deals that are ENTRY or EXIT, but for simple log we want completed trades.
            # Usually a 'Trade' consists of an entry deal and an exit deal.
            # For simplicity, we can just return all deals and let the service layer process them, 
            # OR we can just return the raw deals mapped to dicts.
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

        positions = await _run_mt5(mt5.positions_get)
        
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

# Mock patch for development/testing without MT5
import random
class MockMT5Service:
    def __init__(self):
        self.connected = True
        
    async def initialize(self):
        logger.info("Mock MT5 initialized")
        return True
        
    async def shutdown(self):
        pass
        
    async def get_current_price(self):
        base = 150.00
        return {
            "symbol": "USDJPY",
            "time": datetime.utcnow(),
            "bid": base,
            "ask": base + 0.01,
            "last": base + 0.005,
            "volume": 100
        }
        
    async def get_historical_data(self, timeframe, num_bars=1000):
        # Generate some dummy OHLC data
        dates = pd.date_range(end=datetime.utcnow(), periods=num_bars, freq='1H')
        data = []
        base = 150.0
        for d in dates:
            o = base + random.uniform(-0.5, 0.5)
            c = base + random.uniform(-0.5, 0.5)
            h = max(o, c) + random.uniform(0, 0.2)
            l = min(o, c) - random.uniform(0, 0.2)
            data.append({
                "time": d,
                "open": o,
                "high": h,
                "low": l,
                "close": c,
                "tick_volume": 100,
                "spread": 1,
                "real_volume": 0
            })
        return pd.DataFrame(data)

    async def get_deals(self, from_date=None, to_date=None):
        logger.info("Mock MT5 returning dummy deals")
        # Generate mock deals
        dummy_deals = []
        import uuid
        base_time = datetime.now()
        for i in range(5):
             deal_time = base_time - pd.Timedelta(days=i)
             dummy_deals.append({
                 "ticket": 1000 + i,
                 "order": 2000 + i,
                 "time": deal_time,
                 "time_msc": int(deal_time.timestamp() * 1000),
                 "type": 1 if i % 2 == 0 else 0, # SELL / BUY
                 "entry": 1, # OUT
                 "magic": 0,
                 "position_id": 3000 + i,
                 "reason": 0,
                 "volume": 0.1,
                 "price": 150.0 + (i * 0.1),
                 "commission": 0.0,
                 "swap": 0.0,
                 "profit": 10.0 if i % 2 == 0 else -5.0,
                 "fee": 0.0,
                 "symbol": "USDJPY",
                 "comment": "Mock Deal"
             })
        return dummy_deals

    async def get_positions(self):
        logger.info("Mock MT5 returning dummy positions")
        # Generate one mock open position
        return [{
            "ticket": 9999,
            "time": datetime.now(),
            "time_msc": int(datetime.now().timestamp() * 1000),
            "time_update": int(datetime.now().timestamp()),
            "time_update_msc": int(datetime.now().timestamp() * 1000),
            "type": 0, # BUY
            "magic": 0,
            "identifier": 9999,
            "reason": 0,
            "volume": 0.1,
            "price_open": 151.0,
            "sl": 150.0,
            "tp": 152.0,
            "price_current": 151.2,
            "swap": 0.0,
            "profit": 20.0,
            "symbol": "USDJPY",
            "comment": "Mock Open Position",
            "external_id": ""
        }]

# Use mock if MT5 lib works but connection fails, or prompt to use mock
# For now, we enforce mock if connection fails or for verification:
# Wrapper to choose between Real and Mock based on connection success
class MT5ServiceProvider:
    def __init__(self):
        self.service = None
        self.use_mock = False

    async def get_service(self):
        if self.service:
            return self.service
        
        # Try to initialize real MT5 (connect to running instance)
        real_service = MT5Service()
        if await real_service.initialize():
            # Check if it is the correct terminal
            try:
                info = await _run_mt5(mt5.terminal_info)
                print(f"DEBUG: Connected to MT5. Path: {info.path}")
                logger.info(f"Connected to MT5 at {info.path}")
                
                # Check if we should enforce OANDA path
                target_path = r"C:\Program Files\OANDA MetaTrader 5"
                if target_path.lower() in info.path.lower():
                     print("DEBUG: Confirmed OANDA MT5 instance.")
                     self.service = real_service
                     return self.service
                else:
                     print(f"WARN: Connected MT5 is NOT OANDA ({info.path}). attempting to switch...")
                     await real_service.shutdown()
                     # Fall through to auto-launch logic
            except Exception as e:
                print(f"DEBUG: Error checking terminal info: {e}")
            
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
                print(f"DEBUG: Found MT5 at {path}. Launching...")
                logger.info(f"Found MT5 at {path}. Launching...")
                # Note: mt5.initialize(path=...) triggers the launch
                # Wrap this blocking launch call!
                if await _run_mt5(mt5.initialize, path=path):
                     print("DEBUG: MT5 Launched. Waiting for network connection...")
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

        # Fallback to Mock is DISABLED strictly.
        # logger.warning("Real MT5 connection and auto-launch failed. Falling back to MOCK Service.")
        # self.service = MockMT5Service()
        # self.use_mock = True
        # await self.service.initialize()
        # return self.service
        
        # Return the disconnected real service so the caller knows it failed
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

    async def get_historical_data(self, *args, **kwargs):
        await self._ensure_impl()
        return await self._impl.get_historical_data(*args, **kwargs)

    async def get_deals(self, *args, **kwargs):
        await self._ensure_impl()
        return await self._impl.get_deals(*args, **kwargs)

    async def get_positions(self, *args, **kwargs):
        await self._ensure_impl()
        return await self._impl.get_positions(*args, **kwargs)

mt5_service = ServiceProxy()
