"""
Pairs Trading Strategy (Simplified)

Type: Market Neutral/Statistical Arbitrage
Complexity: ⭐⭐⭐⭐⭐

How it works:
- This is a simplified version that trades based on deviation from moving average
- Calculates spread between price and its moving average
- Long when spread is low (undervalued), short when high (overvalued)
- Note: True pairs trading requires two correlated stocks
"""

import pandas as pd
import numpy as np
from .base_strategy import BaseStrategy, Signal


class PairsTradingStrategy(BaseStrategy):
    """Simplified Pairs Trading strategy using price deviation from mean."""
    
    def __init__(
        self,
        period: int = 30,
        entry_z_score: float = 2.0,
        exit_z_score: float = 0.5,
        name: str = "Pairs Trading"
    ):
        """
        Initialize Pairs Trading strategy.
        
        Args:
            period: Period for calculating mean and std (default: 30)
            entry_z_score: Z-score threshold for entry (default: 2.0)
            exit_z_score: Z-score threshold for exit (default: 0.5)
            name: Strategy name
        """
        super().__init__(name)
        self.period = period
        self.entry_z_score = entry_z_score
        self.exit_z_score = exit_z_score
        
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate spread and z-score indicators.
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            DataFrame with spread indicators
        """
        df = data.copy()
        
        # Calculate moving average as the "pair"
        df['MA'] = df['close'].rolling(window=self.period).mean()
        
        # Spread (difference from mean)
        df['Spread'] = df['close'] - df['MA']
        
        # Spread statistics
        df['Spread_Mean'] = df['Spread'].rolling(window=self.period).mean()
        df['Spread_Std'] = df['Spread'].rolling(window=self.period).std()
        
        # Z-score of spread
        df['Spread_Z'] = (df['Spread'] - df['Spread_Mean']) / df['Spread_Std']
        
        # Normalized spread
        df['Normalized_Spread'] = df['Spread'] / df['MA']
        
        return df
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate trading signals.
        
        Long when spread is low (price below mean)
        Short when spread is high (price above mean)
        Exit when spread returns to neutral
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            Series with signals
        """
        df = self.calculate_indicators(data)
        signals = pd.Series(index=df.index, data=0)
        
        # Buy signal: spread is significantly negative (undervalued)
        buy_condition = df['Spread_Z'] < -self.entry_z_score
        
        # Sell signal: spread is significantly positive (overvalued)
        sell_condition = df['Spread_Z'] > self.entry_z_score
        
        # Exit signals when spread normalizes
        exit_long = (df['Spread_Z'] > -self.exit_z_score) & (df['Spread_Z'].shift(1) <= -self.exit_z_score)
        exit_short = (df['Spread_Z'] < self.exit_z_score) & (df['Spread_Z'].shift(1) >= self.exit_z_score)
        
        signals[buy_condition] = 1
        signals[sell_condition] = -1
        signals[exit_long | exit_short] = 0
        
        return signals
    
    def __str__(self) -> str:
        return f"Pairs Trading (Period: {self.period}, Z: ±{self.entry_z_score})"
