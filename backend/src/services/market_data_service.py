import yfinance as yf
import pandas as pd
import logging
import asyncio
import functools
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
        loop = asyncio.get_running_loop()

        async def fetch_ticker(name, ticker_symbol):
            try:
                def _fetch():
                    ticker = yf.Ticker(ticker_symbol)
                    last_price = ticker.fast_info.last_price
                    prev_close = ticker.fast_info.previous_close
                    return last_price, prev_close

                last_price, prev_close = await loop.run_in_executor(None, _fetch)
                change_pct = ((last_price - prev_close) / prev_close) * 100 if prev_close else 0
                return name, {"price": last_price, "change_pct": change_pct}
            except Exception as e:
                logger.error(f"Failed to fetch price for {name}: {e}")
                return name, {"price": 0, "change_pct": 0}

        tasks = [fetch_ticker(name, symbol) for name, symbol in self.tickers.items()]
        results = await asyncio.gather(*tasks)
        return {name: data for name, data in results}

    def _download_ticker_data(self, symbol_str: str, start_dt: datetime) -> pd.DataFrame:
        """Synchronous helper to download data - called from executor"""
        logger.info(f"_download_ticker_data called with symbol={symbol_str}")
        return yf.download(symbol_str, start=start_dt, progress=False)

    async def get_historical_returns(self, days: int = 20) -> pd.DataFrame:
        """Get historical daily returns for correlation calculation"""
        # Fetch slightly more data to ensure we have enough valid days
        start_date = datetime.now() - timedelta(days=days * 2)

        loop = asyncio.get_running_loop()

        # Fetch data for each ticker sequentially to avoid any closure/concurrency issues
        results = []

        for name, symbol in self.tickers.items():
            try:
                logger.info(f"FETCH_START: {name} with symbol={symbol}")

                # Download data
                df = await loop.run_in_executor(
                    None,
                    self._download_ticker_data,
                    symbol,  # Pass as positional arg
                    start_date  # Pass as positional arg
                )

                logger.info(f"{name}: Downloaded {len(df)} rows")

                if not df.empty and 'Close' in df.columns:
                    close_data = df['Close'].copy()
                    if isinstance(close_data, pd.DataFrame):
                         logger.warning(f"{name}: Close is DataFrame with {len(close_data.columns)} columns, using first")
                         close_data = close_data.iloc[:, 0].copy()

                    returns = close_data.pct_change().copy()
                    logger.info(f"{name}: Calculated {len(returns.dropna())} valid return points, mean={returns.mean():.6f}, std={returns.std():.6f}")

                    # Log first few values to verify data is different
                    first_values = returns.dropna().head(5).values
                    logger.info(f"{name}: First 5 returns: {first_values}")

                    results.append((name, returns))
                else:
                    logger.error(f"{name}: Empty dataframe or no Close column")
                    results.append((name, None))
            except Exception as e:
                logger.error(f"Failed to fetch history for {name}: {e}")
                results.append((name, None))

        data = {name: series for name, series in results if series is not None}

        logger.info(f"Successfully fetched data for {len(data)} assets: {list(data.keys())}")

        # Log the series IDs to verify they're different objects
        for name, series in data.items():
            logger.info(f"Before DataFrame - {name}: Series ID={id(series)}, len={len(series)}, first_val={series.dropna().iloc[0] if len(series.dropna()) > 0 else 'N/A'}")

        if not data:
            logger.error("No historical data fetched for any asset")
            return pd.DataFrame()

        df = pd.DataFrame(data)
        logger.info(f"Market history DataFrame shape: {df.shape}, columns: {list(df.columns)}")
        logger.info(f"Market history date range: {df.index.min()} to {df.index.max()}")

        # Verify each column in DataFrame has different data
        for col in df.columns:
            logger.info(f"After DataFrame - {col}: mean={df[col].mean():.6f}, std={df[col].std():.6f}, first_val={df[col].dropna().iloc[0] if len(df[col].dropna()) > 0 else 'N/A'}")

        return df

market_data_service = MarketDataService()
