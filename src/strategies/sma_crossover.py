"""
Simple Moving Average (SMA) Crossover Strategy

A classic momentum strategy that generates signals based on the crossover
of short-term and long-term moving averages.

Strategy Rules:
- BUY: When short MA crosses above long MA (golden cross)
- SELL: When short MA crosses below long MA (death cross)
"""

import pandas as pd
import numpy as np
from .base_strategy import BaseStrategy, Signal


class SMACrossoverStrategy(BaseStrategy):
    """SMA Crossover trading strategy."""
    
    def __init__(self, short_window: int = 50, long_window: int = 200):
        """
        Initialize SMA Crossover strategy.
        
        Args:
            short_window: Period for short-term moving average
            long_window: Period for long-term moving average
        """
        super().__init__(name="SMA_Crossover")
        self.short_window = short_window
        self.long_window = long_window
        
        # Validate parameters
        if short_window >= long_window:
            raise ValueError("Short window must be less than long window")
        
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate SMA indicators.
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            DataFrame with SMA columns added
        """
        df = data.copy()
        
        # Calculate moving averages
        df['sma_short'] = df['close'].rolling(window=self.short_window).mean()
        df['sma_long'] = df['close'].rolling(window=self.long_window).mean()
        
        return df
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate trading signals based on SMA crossover.
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            Series with signals (1=BUY, -1=SELL, 0=HOLD)
        """
        # Calculate indicators
        df = self.calculate_indicators(data)
        
        # Initialize signals
        signals = pd.Series(0, index=df.index)
        
        # Generate signals based on crossover
        # BUY signal: short MA crosses above long MA
        signals[(df['sma_short'] > df['sma_long']) & 
                (df['sma_short'].shift(1) <= df['sma_long'].shift(1))] = 1
        
        # SELL signal: short MA crosses below long MA
        signals[(df['sma_short'] < df['sma_long']) & 
                (df['sma_short'].shift(1) >= df['sma_long'].shift(1))] = -1
        
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
        
        if len(df) < self.long_window:
            return {
                'status': 'insufficient_data',
                'message': f'Need at least {self.long_window} data points'
            }
        
        latest = df.iloc[-1]
        
        return {
            'status': 'active',
            'short_ma': latest['sma_short'],
            'long_ma': latest['sma_long'],
            'current_price': latest['close'],
            'trend': 'bullish' if latest['sma_short'] > latest['sma_long'] else 'bearish',
            'distance_from_short_ma': (latest['close'] - latest['sma_short']) / latest['sma_short'],
            'distance_from_long_ma': (latest['close'] - latest['sma_long']) / latest['sma_long']
        }
    
    def __str__(self) -> str:
        return f"SMA Crossover ({self.short_window}/{self.long_window})"


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
    strategy = SMACrossoverStrategy(short_window=50, long_window=200)
    
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
