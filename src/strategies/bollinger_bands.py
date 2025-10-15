"""
Bollinger Bands Strategy

Type: Volatility/Mean Reversion
Complexity: ⭐⭐

How it works:
- Middle band = 20-day SMA
- Upper/Lower bands = Middle ± (2 × standard deviation)
- Buy when price touches lower band
- Sell when price touches upper band
"""

import pandas as pd
import numpy as np
from .base_strategy import BaseStrategy, Signal


class BollingerBandsStrategy(BaseStrategy):
    """Bollinger Bands trading strategy."""
    
    def __init__(
        self,
        period: int = 20,
        num_std: float = 2.0,
        name: str = "Bollinger Bands"
    ):
        """
        Initialize Bollinger Bands strategy.
        
        Args:
            period: Period for moving average (default: 20)
            num_std: Number of standard deviations (default: 2.0)
            name: Strategy name
        """
        super().__init__(name)
        self.period = period
        self.num_std = num_std
        
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate Bollinger Bands.
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            DataFrame with BB indicators
        """
        df = data.copy()
        
        # Middle band (SMA)
        df['BB_Middle'] = df['close'].rolling(window=self.period).mean()
        
        # Standard deviation
        df['BB_Std'] = df['close'].rolling(window=self.period).std()
        
        # Upper and lower bands
        df['BB_Upper'] = df['BB_Middle'] + (self.num_std * df['BB_Std'])
        df['BB_Lower'] = df['BB_Middle'] - (self.num_std * df['BB_Std'])
        
        # Calculate %B (position within bands)
        df['BB_PercentB'] = (df['close'] - df['BB_Lower']) / (df['BB_Upper'] - df['BB_Lower'])
        
        return df
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate trading signals.
        
        Buy when price touches lower band (oversold)
        Sell when price touches upper band (overbought)
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            Series with signals
        """
        df = self.calculate_indicators(data)
        signals = pd.Series(index=df.index, data=0)
        
        # Buy signal: price touches or crosses below lower band
        buy_condition = (df['close'] <= df['BB_Lower']) | (df['BB_PercentB'] <= 0.05)
        
        # Sell signal: price touches or crosses above upper band
        sell_condition = (df['close'] >= df['BB_Upper']) | (df['BB_PercentB'] >= 0.95)
        
        signals[buy_condition] = 1
        signals[sell_condition] = -1
        
        return signals
    
    def __str__(self) -> str:
        return f"Bollinger Bands (Period: {self.period}, StdDev: {self.num_std})"
