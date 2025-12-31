from typing import Dict, List, Any, Optional
from pydantic import BaseModel
import pandas as pd
import numpy as np
from ..services.mt5_service import mt5_service

class KeyLevel(BaseModel):
    price: float
    type: str  # 'support', 'resistance', 'pivot', 'round'
    description: str
    strength: int # 1-5

class MarketScenario(BaseModel):
    direction: str # 'bullish', 'bearish', 'neutral'
    description: str
    active_levels: List[KeyLevel]

class ScenarioService:
    def __init__(self):
        pass

    def _calculate_pivots(self, high: float, low: float, close: float) -> List[KeyLevel]:
        p = (high + low + close) / 3
        r1 = 2 * p - low
        s1 = 2 * p - high
        r2 = p + (high - low)
        s2 = p - (high - low)
        
        return [
            KeyLevel(price=p, type='pivot', description='デイリーピボット', strength=3),
            KeyLevel(price=r1, type='resistance', description='R1', strength=2),
            KeyLevel(price=s1, type='support', description='S1', strength=2),
            KeyLevel(price=r2, type='resistance', description='R2', strength=1),
            KeyLevel(price=s2, type='support', description='S2', strength=1),
        ]

    def _get_round_numbers(self, current_price: float, range_pips: int = 100) -> List[KeyLevel]:
        """Get round numbers around the current price (e.g. 150.00, 150.50)"""
        levels = []
        base_price = int(current_price) 
        # Check X.00 and X.50 within a reasonable range
        candidates = [
            base_price - 1.0, base_price - 0.5, 
            base_price * 1.0, base_price + 0.5, 
            base_price + 1.0
        ]
        
        for price in candidates:
            # Simple distance check, if it's "close enough" (within ~1.5 yen range visually)
            if abs(current_price - price) < 1.5:
                levels.append(KeyLevel(
                    price=price, 
                    type='round', 
                    description=f'キリ番 {price:.2f}', 
                    strength=4
                ))
        return levels

    async def generate_scenarios(self, current_price: float) -> List[MarketScenario]:
        """
        Generate simple scenarios based on key levels.
        Needs historical data to calculate Pivots from yesterday's D1 bar.
        """
        # Get D1 data for Pivot calculation
        # We need yesterday's completed bar. 
        # get_historical_data returns most recent bars. Index -2 is typically the last completed D1 bar if we query small number.
        # But let's verify. MT5 logic: 0 is current (forming), 1 is last completed? 
        # Usually in array from MT5, 0 is oldest. But dataframe conversion in mt5_service might affect this.
        # Let's check mt5_service implementation implicitly or assume standard dataframe order (index 0 is oldest).
        
        df = await mt5_service.get_historical_data("D1", num_bars=5)
        
        if df.empty:
            return []

        # Assuming the last row is current (forming) day, and second to last is yesterday.
        if len(df) < 2:
            return []
            
        yesterday = df.iloc[-2]
        
        pivots = self._calculate_pivots(yesterday['high'], yesterday['low'], yesterday['close'])
        round_numbers = self._get_round_numbers(current_price)
        
        all_levels = pivots + round_numbers
        all_levels.sort(key=lambda x: x.price)
        
        # Determine current zone
        closest_resistance = None
        closest_support = None
        
        for level in all_levels:
            if level.price > current_price:
                if closest_resistance is None or level.price < closest_resistance.price:
                    closest_resistance = level
            elif level.price < current_price:
                 if closest_support is None or level.price > closest_support.price:
                    closest_support = level

        scenarios = []
        
        # Bullish Scenario
        if closest_resistance:
            dist = (closest_resistance.price - current_price) * 100 # pips approx (yen)
            scenarios.append(MarketScenario(
                direction='bullish',
                description=f"{closest_resistance.description} ({closest_resistance.price:.2f}) 上抜けで上昇余地拡大",
                active_levels=[closest_resistance]
            ))
        else:
             scenarios.append(MarketScenario(
                direction='bullish',
                description="青天井の上昇トレンド",
                active_levels=[]
            ))
            
        # Bearish Scenario
        if closest_support:
             scenarios.append(MarketScenario(
                direction='bearish',
                description=f"{closest_support.description} ({closest_support.price:.2f}) 下抜けで下落加速の可能性",
                active_levels=[closest_support]
            ))
        else:
             scenarios.append(MarketScenario(
                direction='bearish',
                description="底なしの下落トレンド",
                active_levels=[]
            ))

        # Range/Neutral Scenario (if between levels)
        if closest_resistance and closest_support:
            scenarios.append(MarketScenario(
                direction='neutral',
                description=f"{closest_support.description} ({closest_support.price:.2f}) と {closest_resistance.description} ({closest_resistance.price:.2f}) の間でのレンジ推移",
                active_levels=[closest_support, closest_resistance]
            ))

        return scenarios

scenario_service = ScenarioService()
