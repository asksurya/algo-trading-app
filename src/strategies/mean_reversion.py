"""
Mean Reversion Strategy

Type: Mean Reversion / Statistical Arbitrage
Complexity: ⭐⭐⭐⭐

How it works:
- Calculate z-score: (Price - Mean) / Std Dev
- Buy when z-score < -2 (oversold)
- Sell when z-score > 2 (overbought)
"""

import pandas as pd
import numpy as np
from .base_strategy import BaseStrategy, Signal


class MeanReversionStrategy(BaseStrategy):
    """Mean Reversion trading strategy using z-scores."""
    
    def __init__(
        self,
        period: int = 20,
        entry_threshold: float = 2.0,
        exit_threshold: float = 0.5,
        name: str = "Mean Reversion"
    ):
        """
        Initialize Mean Reversion strategy.
        
        Args:
            period: Period for mean and std dev calculation (default: 20)
            entry_threshold: Z-score threshold for entry (default: 2.0)
            exit_threshold: Z-score threshold for exit (default: 0.5)
            name: Strategy name
        """
        super().__init__(name)
        self.period = period
        self.entry_threshold = entry_threshold
        self.exit_threshold = exit_threshold
        
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate mean reversion indicators.
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            DataFrame with z-score indicators
        """
        df = data.copy()
        
        # Rolling mean and standard deviation
        df['Mean'] = df['close'].rolling(window=self.period).mean()
        df['Std'] = df['close'].rolling(window=self.period).std()
        
        # Z-score calculation
        df['Z_Score'] = (df['close'] - df['Mean']) / df['Std']
        
        # Upper and lower bands (similar to Bollinger Bands)
        df['Upper_Band'] = df['Mean'] + (self.entry_threshold * df['Std'])
        df['Lower_Band'] = df['Mean'] - (self.entry_threshold * df['Std'])
        
        return df
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate trading signals.
        
        Buy when z-score < -entry_threshold (oversold)
        Sell when z-score > entry_threshold (overbought)
        Exit when z-score returns to ±exit_threshold
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            Series with signals
        """
        df = self.calculate_indicators(data)
        signals = pd.Series(index=df.index, data=0)
        
        # Buy signal: z-score indicates oversold condition
        buy_condition = df['Z_Score'] < -self.entry_threshold
        
        # Sell signal: z-score indicates overbought condition
        sell_condition = df['Z_Score'] > self.entry_threshold
        
        # Exit long positions when price reverts to mean
        exit_long_condition = (df['Z_Score'] > -self.exit_threshold) & (df['Z_Score'].shift(1) < -self.exit_threshold)
        
        # Exit short positions when price reverts to mean
        exit_short_condition = (df['Z_Score'] < self.exit_threshold) & (df['Z_Score'].shift(1) > self.exit_threshold)
        
        signals[buy_condition] = 1
        signals[sell_condition] = -1
        
        # Mark exits (these will be handled by the backtest engine)
        signals[exit_long_condition | exit_short_condition] = 0
        
        return signals
    
    def __str__(self) -> str:
        return f"Mean Reversion (Period: {self.period}, Z-Score: ±{self.entry_threshold})"
