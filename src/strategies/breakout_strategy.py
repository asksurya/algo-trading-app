"""
Breakout Strategy

Type: Trend Following
Complexity: ⭐⭐

How it works:
- Identify support/resistance levels (52-week high/low, pivot points)
- Buy on breakout above resistance
- Sell on breakdown below support
"""

import pandas as pd
import numpy as np
from .base_strategy import BaseStrategy, Signal


class BreakoutStrategy(BaseStrategy):
    """Breakout trading strategy."""
    
    def __init__(
        self,
        lookback_period: int = 20,
        breakout_threshold: float = 0.02,
        name: str = "Breakout"
    ):
        """
        Initialize Breakout strategy.
        
        Args:
            lookback_period: Period to identify support/resistance (default: 20)
            breakout_threshold: Minimum % move for valid breakout (default: 0.02 = 2%)
            name: Strategy name
        """
        super().__init__(name)
        self.lookback_period = lookback_period
        self.breakout_threshold = breakout_threshold
        
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate breakout levels.
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            DataFrame with breakout indicators
        """
        df = data.copy()
        
        # Rolling high and low (resistance and support)
        df['Resistance'] = df['high'].rolling(window=self.lookback_period).max()
        df['Support'] = df['low'].rolling(window=self.lookback_period).min()
        
        # Price range
        df['Range'] = df['Resistance'] - df['Support']
        
        # Breakout signals
        df['Above_Resistance'] = df['close'] > df['Resistance'].shift(1)
        df['Below_Support'] = df['close'] < df['Support'].shift(1)
        
        # Calculate percentage breakout
        df['Breakout_Pct'] = (df['close'] - df['Resistance'].shift(1)) / df['Resistance'].shift(1)
        df['Breakdown_Pct'] = (df['Support'].shift(1) - df['close']) / df['Support'].shift(1)
        
        # Volume confirmation (if available)
        if 'volume' in df.columns:
            df['Avg_Volume'] = df['volume'].rolling(window=self.lookback_period).mean()
            df['Volume_Surge'] = df['volume'] > df['Avg_Volume'] * 1.5
        else:
            df['Volume_Surge'] = True
        
        return df
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate trading signals.
        
        Buy on breakout above resistance with volume
        Sell on breakdown below support
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            Series with signals
        """
        df = self.calculate_indicators(data)
        signals = pd.Series(index=df.index, data=0)
        
        # Buy signal: price breaks above resistance with sufficient volume
        buy_condition = (
            df['Above_Resistance'] & 
            (df['Breakout_Pct'] >= self.breakout_threshold) &
            df['Volume_Surge']
        )
        
        # Sell signal: price breaks below support
        sell_condition = (
            df['Below_Support'] & 
            (df['Breakdown_Pct'] >= self.breakout_threshold)
        )
        
        signals[buy_condition] = 1
        signals[sell_condition] = -1
        
        return signals
    
    def __str__(self) -> str:
        return f"Breakout (Lookback: {self.lookback_period} days)"
