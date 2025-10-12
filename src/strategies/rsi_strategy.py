"""
Relative Strength Index (RSI) Strategy

A mean-reversion strategy based on the RSI indicator.

Strategy Rules:
- BUY: When RSI crosses below oversold threshold (e.g., 30)
- SELL: When RSI crosses above overbought threshold (e.g., 70)
"""

import pandas as pd
import numpy as np
from .base_strategy import BaseStrategy, Signal


class RSIStrategy(BaseStrategy):
    """RSI-based trading strategy."""
    
    def __init__(self, period: int = 14, oversold: int = 30, overbought: int = 70):
        """
        Initialize RSI strategy.
        
        Args:
            period: RSI calculation period
            oversold: Oversold threshold (buy signal)
            overbought: Overbought threshold (sell signal)
        """
        super().__init__(name="RSI")
        self.period = period
        self.oversold = oversold
        self.overbought = overbought
        
        # Validate parameters
        if not (0 < oversold < overbought < 100):
            raise ValueError("Invalid RSI thresholds: 0 < oversold < overbought < 100")
    
    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """
        Calculate Relative Strength Index.
        
        Args:
            prices: Series of closing prices
            period: RSI period
            
        Returns:
            Series of RSI values
        """
        # Calculate price changes
        delta = prices.diff()
        
        # Separate gains and losses
        gains = delta.where(delta > 0, 0)
        losses = -delta.where(delta < 0, 0)
        
        # Calculate average gains and losses
        avg_gains = gains.rolling(window=period).mean()
        avg_losses = losses.rolling(window=period).mean()
        
        # Calculate RS and RSI
        rs = avg_gains / avg_losses
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate RSI indicator.
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            DataFrame with RSI column added
        """
        df = data.copy()
        df['rsi'] = self.calculate_rsi(df['close'], self.period)
        return df
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate trading signals based on RSI levels.
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            Series with signals (1=BUY, -1=SELL, 0=HOLD)
        """
        # Calculate indicators
        df = self.calculate_indicators(data)
        
        # Initialize signals
        signals = pd.Series(0, index=df.index)
        
        # Generate signals
        # BUY signal: RSI crosses below oversold
        signals[(df['rsi'] < self.oversold) & 
                (df['rsi'].shift(1) >= self.oversold)] = 1
        
        # SELL signal: RSI crosses above overbought
        signals[(df['rsi'] > self.overbought) & 
                (df['rsi'].shift(1) <= self.overbought)] = -1
        
        return signals
    
    def get_strategy_state(self, data: pd.DataFrame) -> dict:
        """
        Get current strategy state and indicators.
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            Dictionary with strategy state
        """
        df = self.calculate_indicators(data)
        
        if len(df) < self.period:
            return {
                'status': 'insufficient_data',
                'message': f'Need at least {self.period} data points'
            }
        
        latest = df.iloc[-1]
        
        # Determine market condition
        if latest['rsi'] < self.oversold:
            condition = 'oversold'
        elif latest['rsi'] > self.overbought:
            condition = 'overbought'
        else:
            condition = 'neutral'
        
        return {
            'status': 'active',
            'rsi': latest['rsi'],
            'current_price': latest['close'],
            'condition': condition,
            'distance_from_oversold': latest['rsi'] - self.oversold,
            'distance_from_overbought': self.overbought - latest['rsi']
        }
    
    def __str__(self) -> str:
        return f"RSI Strategy (period={self.period}, {self.oversold}/{self.overbought})"


if __name__ == "__main__":
    # Example usage
    import sys
    sys.path.append('../..')
    
    from src.data.data_fetcher import DataFetcher
    import logging
    
    logging.basicConfig(level=logging.INFO)
    
    # Fetch data
    fetcher = DataFetcher(data_provider='yahoo')
    df = fetcher.fetch_historical_data(
        symbol='AAPL',
        start_date='2023-01-01',
        end_date='2024-01-01'
    )
    
    # Initialize strategy
    strategy = RSIStrategy(period=14, oversold=30, overbought=70)
    
    # Generate signals
    signals = strategy.generate_signals(df)
    
    # Print results
    print(f"\nStrategy: {strategy}")
    print(f"Total signals generated: {(signals != 0).sum()}")
    print(f"Buy signals: {(signals == 1).sum()}")
    print(f"Sell signals: {(signals == -1).sum()}")
    
    # Show signal dates
    signal_dates = signals[signals != 0]
    if len(signal_dates) > 0:
        print("\nSignal dates:")
        for date, signal in signal_dates.items():
            signal_type = "BUY" if signal == 1 else "SELL"
            print(f"  {date.strftime('%Y-%m-%d')}: {signal_type}")
    
    # Get current state
    state = strategy.get_strategy_state(df)
    print(f"\nCurrent strategy state:")
    for key, value in state.items():
        print(f"  {key}: {value}")
