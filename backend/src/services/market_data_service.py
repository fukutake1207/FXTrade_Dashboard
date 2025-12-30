import yfinance as yf
import pandas as pd
import logging
import asyncio
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class MarketDataService:
    def __init__(self):
        self.tickers = {
            "Gold": "GC=F",      # Gold Futures
            "Nikkei": "^N225",   # Nikkei 225
            "S&P500": "^GSPC"    # S&P 500
        }
    
    async def get_current_prices(self):
        """Get latest prices for correlated assets"""
        prices = {}
        for name, ticker_symbol in self.tickers.items():
            try:
                ticker = yf.Ticker(ticker_symbol)
                # fast_info is often faster for current price
                # but might not be 100% realtime. Good for correlation overview.
                last_price = ticker.fast_info.last_price
                
                # Get previous close to calculate change
                prev_close = ticker.fast_info.previous_close
                change_pct = ((last_price - prev_close) / prev_close) * 100 if prev_close else 0
                
                prices[name] = {
                    "price": last_price,
                    "change_pct": change_pct
                }
            except Exception as e:
                logger.error(f"Failed to fetch price for {name}: {e}")
                prices[name] = {"price": 0, "change_pct": 0}
        
        return prices

    async def get_historical_returns(self, days: int = 20) -> pd.DataFrame:
        """Get historical daily returns for correlation calculation"""
        # Fetch slightly more data to ensure we have enough valid days
        start_date = datetime.now() - timedelta(days=days * 2)
        
        loop = asyncio.get_running_loop()
        
        async def fetch_ticker(name, symbol):
            try:
                # Run blocking download in a separate thread
                df = await loop.run_in_executor(None, lambda: yf.download(symbol, start=start_date, progress=False))
                
                if not df.empty and 'Close' in df.columns:
                    close_data = df['Close']
                    # Handle case where yf returns DataFrame for 'Close' (multi-level cols issues in some versions)
                    if isinstance(close_data, pd.DataFrame):
                         # If multiple columns, try to pick the one that matches ticker or just the first
                         close_data = close_data.iloc[:, 0]
                    
                    return name, close_data.pct_change()
            except Exception as e:
                logger.error(f"Failed to fetch history for {name}: {e}")
            return name, None

        tasks = [fetch_ticker(name, symbol) for name, symbol in self.tickers.items()]
        results = await asyncio.gather(*tasks)
        
        data = {name: series for name, series in results if series is not None}
        
        if not data:
            return pd.DataFrame()
            
        return pd.DataFrame(data)

market_data_service = MarketDataService()
