"""
Machine Learning Based Strategy (Simplified)

Type: Predictive
Complexity: ⭐⭐⭐⭐⭐

How it works:
- Uses ensemble of technical indicators as features
- Combines multiple signals (trend, momentum, volatility)
- Generates predictions based on weighted voting system
- Note: This is a simplified rule-based ML proxy; true ML would require training data
"""

import pandas as pd
import numpy as np
from .base_strategy import BaseStrategy, Signal


class MLStrategy(BaseStrategy):
    """ML-inspired strategy using ensemble of technical indicators."""
    
    def __init__(
        self,
        short_period: int = 10,
        long_period: int = 30,
        threshold: float = 0.6,
        name: str = "ML Strategy"
    ):
        """
        Initialize ML Strategy.
        
        Args:
            short_period: Short-term period for indicators (default: 10)
            long_period: Long-term period for indicators (default: 30)
            threshold: Confidence threshold for signals (default: 0.6)
            name: Strategy name
        """
        super().__init__(name)
        self.short_period = short_period
        self.long_period = long_period
        self.threshold = threshold
        
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate multiple technical indicators as ML features.
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            DataFrame with indicator features
        """
        df = data.copy()
        
        # Trend indicators
        df['SMA_Short'] = df['close'].rolling(window=self.short_period).mean()
        df['SMA_Long'] = df['close'].rolling(window=self.long_period).mean()
        df['Trend_Signal'] = np.where(df['SMA_Short'] > df['SMA_Long'], 1, -1)
        
        # Momentum indicators
        df['ROC'] = df['close'].pct_change(periods=self.short_period) * 100
        df['Momentum_Signal'] = np.where(df['ROC'] > 0, 1, -1)
        
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        df['RSI_Signal'] = np.where(
            df['RSI'] < 30, 1,
            np.where(df['RSI'] > 70, -1, 0)
        )
        
        # Volatility (Bollinger Bands)
        df['BB_Middle'] = df['close'].rolling(window=20).mean()
        df['BB_Std'] = df['close'].rolling(window=20).std()
        df['BB_Upper'] = df['BB_Middle'] + (2 * df['BB_Std'])
        df['BB_Lower'] = df['BB_Middle'] - (2 * df['BB_Std'])
        df['BB_Signal'] = np.where(
            df['close'] < df['BB_Lower'], 1,
            np.where(df['close'] > df['BB_Upper'], -1, 0)
        )
        
        # Volume indicator
        df['Volume_MA'] = df['volume'].rolling(window=self.short_period).mean()
        df['Volume_Signal'] = np.where(df['volume'] > df['Volume_MA'], 1, 0)
        
        # Price momentum
        df['Price_Change'] = df['close'].pct_change(periods=5)
        df['Price_Signal'] = np.where(df['Price_Change'] > 0, 1, -1)
        
        # Ensemble prediction (weighted average of signals)
        df['Prediction'] = (
            df['Trend_Signal'] * 0.3 +
            df['Momentum_Signal'] * 0.2 +
            df['RSI_Signal'] * 0.2 +
            df['BB_Signal'] * 0.15 +
            df['Volume_Signal'] * 0.05 +
            df['Price_Signal'] * 0.1
        )
        
        # Confidence score (normalized)
        df['Confidence'] = df['Prediction'].abs()
        
        return df
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate trading signals based on ML ensemble.
        
        Buy when ensemble predicts bullish with high confidence
        Sell when ensemble predicts bearish with high confidence
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            Series with signals
        """
        df = self.calculate_indicators(data)
        signals = pd.Series(index=df.index, data=0)
        
        # Buy signal: positive prediction with sufficient confidence
        buy_condition = (df['Prediction'] > self.threshold)
        
        # Sell signal: negative prediction with sufficient confidence
        sell_condition = (df['Prediction'] < -self.threshold)
        
        signals[buy_condition] = 1
        signals[sell_condition] = -1
        
        return signals
    
    def __str__(self) -> str:
        return f"ML Strategy (Ensemble, Threshold: {self.threshold})"
