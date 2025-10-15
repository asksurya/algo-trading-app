"""
VWAP Strategy

Type: Intraday/Institutional
Complexity: ⭐⭐⭐

How it works:
- VWAP = Cumulative (Price × Volume) / Cumulative Volume
- Buy when price crosses above VWAP
- Sell when price crosses below VWAP
"""

import pandas as pd
import numpy as np
from .base_strategy import BaseStrategy, Signal


class VWAPStrategy(BaseStrategy):
    """VWAP (Volume-Weighted Average Price) trading strategy."""
    
    def __init__(
        self,
        period: int = 20,
        name: str = "VWAP"
    ):
        """
        Initialize VWAP strategy.
        
        Args:
            period: Rolling period for VWAP calculation (default: 20)
            name: Strategy name
        """
        super().__init__(name)
        self.period = period
        
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate VWAP indicator.
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            DataFrame with VWAP indicator
        """
        df = data.copy()
        
        # Typical price
        df['Typical_Price'] = (df['high'] + df['low'] + df['close']) / 3
        
        # Price * Volume
        df['PV'] = df['Typical_Price'] * df['volume']
        
        # Rolling VWAP calculation
        df['Cumulative_PV'] = df['PV'].rolling(window=self.period).sum()
        df['Cumulative_Volume'] = df['volume'].rolling(window=self.period).sum()
        
        # VWAP
        df['VWAP'] = df['Cumulative_PV'] / df['Cumulative_Volume']
        
        # Distance from VWAP (as percentage)
        df['Distance_from_VWAP'] = (df['close'] - df['VWAP']) / df['VWAP'] * 100
        
        return df
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate trading signals.
        
        Buy when price crosses above VWAP
        Sell when price crosses below VWAP
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            Series with signals
        """
        df = self.calculate_indicators(data)
        signals = pd.Series(index=df.index, data=0)
        
        # Buy signal: price crosses above VWAP
        buy_condition = (df['close'] > df['VWAP']) & (df['close'].shift(1) <= df['VWAP'].shift(1))
        
        # Sell signal: price crosses below VWAP
        sell_condition = (df['close'] < df['VWAP']) & (df['close'].shift(1) >= df['VWAP'].shift(1))
        
        signals[buy_condition] = 1
        signals[sell_condition] = -1
        
        return signals
    
    def __str__(self) -> str:
        return f"VWAP (Period: {self.period})"
