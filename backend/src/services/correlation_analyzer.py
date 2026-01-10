import pandas as pd
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

class CorrelationAnalyzer:
    def __init__(self, lookback_days: int = 20):
        self.lookback_days = lookback_days
        self.correlation_thresholds = {
            "strong": 0.7,
            "moderate": 0.4,
            "weak": 0.2
        }
    
    def calculate_correlation(
        self,
        usdjpy_returns: pd.Series,
        asset_returns: pd.Series
    ) -> float:
        """Calculate correlation between two series"""
        # Align dates and drop NaNs
        aligned_data = pd.concat([usdjpy_returns, asset_returns], axis=1).dropna()

        logger.debug(f"Correlation calculation: {len(usdjpy_returns)} USDJPY points, {len(asset_returns)} asset points, {len(aligned_data)} aligned points")

        if len(aligned_data) < 5: # Need minimum data points
            logger.warning(f"Insufficient data for correlation: only {len(aligned_data)} aligned points (need at least 5)")
            return 0.0

        corr = aligned_data.iloc[:, 0].corr(aligned_data.iloc[:, 1])
        logger.debug(f"Calculated correlation: {corr:.4f}")
        return corr

    def analyze_correlations(
        self,
        usdjpy_history: pd.DataFrame,
        market_history: pd.DataFrame
    ) -> Dict[str, dict]:
        """Analyze correlations for all assets"""
        results = {}

        # Ensure USDJPY history has datetime index for proper alignment with market data
        if 'time' in usdjpy_history.columns:
            usdjpy_history = usdjpy_history.set_index('time')

        # Normalize USDJPY index to date-only for daily data alignment
        # MT5 returns timestamps with specific times, but we only care about the date for D1 correlation
        if not usdjpy_history.empty:
            usdjpy_history.index = pd.to_datetime(usdjpy_history.index).normalize()

        # Calculate USDJPY returns if not already calculated
        if 'returns' not in usdjpy_history.columns:
            # Assuming 'close' column exists
            usdjpy_returns = usdjpy_history['close'].pct_change()
        else:
            usdjpy_returns = usdjpy_history['returns']

        # Ensure market_history index is also normalized (yfinance should already be, but let's be sure)
        if not market_history.empty:
            market_history.index = pd.to_datetime(market_history.index).normalize()

        logger.info(f"Starting correlation analysis for {len(market_history.columns)} assets: {list(market_history.columns)}")
        logger.info(f"USDJPY returns: {len(usdjpy_returns)} points, date range: {usdjpy_returns.index.min()} to {usdjpy_returns.index.max()}")

        for column in market_history.columns:
            asset_returns = market_history[column]
            logger.info(f"{column} returns: {len(asset_returns)} points, date range: {asset_returns.index.min()} to {asset_returns.index.max()}")
            corr = self.calculate_correlation(usdjpy_returns, asset_returns)
            
            strength = "weak"
            abs_corr = abs(corr)
            if abs_corr >= self.correlation_thresholds["strong"]:
                strength = "strong"
            elif abs_corr >= self.correlation_thresholds["moderate"]:
                strength = "moderate"
            
            # Simple interpretation
            relationship = "positive" if corr > 0 else "negative"
            
            results[column] = {
                "coefficient": round(corr, 2),
                "strength": strength,
                "relationship": relationship
            }
            
        return results

    def generate_insight(self, correlations: Dict[str, dict], current_moves: Dict[str, float]) -> List[str]:
        """Generate text insights based on correlation and current moves"""
        insights = []
        for asset, data in correlations.items():
            corr = data['coefficient']
            if abs(corr) < self.correlation_thresholds["moderate"]:
                continue
                
            move = current_moves.get(asset, 0)
            # If correlation is significant
            if (corr > 0 and move > 0) or (corr < 0 and move < 0):
                direction = "円安" # Asset Up + Pos Corr => USDJPY Up (Yen Weak) OR Asset Down + Neg Corr => USDJPY Up
            else:
                direction = "円高"
            
            strength_text = "強い" if data['strength'] == "strong" else ""
            insights.append(f"{asset}の動きは{strength_text}{direction}圧力を示唆")
            
        return insights

correlation_analyzer = CorrelationAnalyzer()
