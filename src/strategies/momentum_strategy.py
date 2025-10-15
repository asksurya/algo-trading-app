"""
Momentum Strategy

Type: Momentum
Complexity: ⭐⭐

How it works:
- Calculate rate of price change over N periods
- Buy when momentum is positive and increasing
- Sell when momentum turns negative
"""

import pandas as pd
import numpy as np
from .base_strategy import BaseStrategy, Signal


class MomentumStrategy(BaseStrategy):
    """Momentum trading strategy."""
    
    def __init__(
        self,
        period: int = 20,
        threshold: float = 0.0,
        name: str = "Momentum"
    ):
        """
        Initialize Momentum strategy.
        
        Args:
            period: Period for momentum calculation (default: 20)
            threshold: Minimum momentum threshold for signals (default: 0.0)
            name: Strategy name
        """
        super().__init__(name)
        self.period = period
        self.threshold = threshold
        
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate momentum indicators.
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            DataFrame with momentum indicators
        """
        df = data.copy()
        
        # Rate of change (ROC)
        df['Momentum'] = df['close'].pct_change(periods=self.period) * 100
        
        # Momentum direction (change in momentum)
        df['Momentum_Change'] = df['Momentum'].diff()
        
        # Moving average of momentum for smoothing
        df['Momentum_MA'] = df['Momentum'].rolling(window=5).mean()
        
        return df
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate trading signals.
        
        Buy when momentum is positive and increasing
        Sell when momentum turns negative
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            Series with signals
        """
        df = self.calculate_indicators(data)
        signals = pd.Series(index=df.index, data=0)
        
        # Buy signal: momentum is positive and increasing
        buy_condition = (
            (df['Momentum'] > self.threshold) & 
            (df['Momentum_Change'] > 0)
        )
        
        # Sell signal: momentum turns negative or decreasing significantly
        sell_condition = (
            (df['Momentum'] < -self.threshold) | 
            ((df['Momentum'] < 0) & (df['Momentum_Change'] < -1))
        )
        
        signals[buy_condition] = 1
        signals[sell_condition] = -1
        
        return signals
    
    def __str__(self) -> str:
        return f"Momentum (Period: {self.period})"
