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
        if len(aligned_data) < 5: # Need minimum data points
            return 0.0
            
        return aligned_data.iloc[:, 0].corr(aligned_data.iloc[:, 1])

    def analyze_correlations(
        self,
        usdjpy_history: pd.DataFrame,
        market_history: pd.DataFrame
    ) -> Dict[str, dict]:
        """Analyze correlations for all assets"""
        results = {}
        
        # Calculate USDJPY returns if not already calculated
        if 'returns' not in usdjpy_history.columns:
            # Assuming 'close' column exists
             usdjpy_returns = usdjpy_history['close'].pct_change()
        else:
            usdjpy_returns = usdjpy_history['returns']

        for column in market_history.columns:
            asset_returns = market_history[column]
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
