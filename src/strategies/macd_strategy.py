"""
MACD Strategy

Moving Average Convergence Divergence - combines trend and momentum.
"""

import pandas as pd
import numpy as np
from src.strategies.base_strategy import BaseStrategy


class MACDStrategy(BaseStrategy):
    """
    MACD (Moving Average Convergence Divergence) Strategy.
    
    Buy when MACD line crosses above signal line (bullish crossover).
    Sell when MACD line crosses below signal line (bearish crossover).
    """
    
    def __init__(
        self,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9
    ):
        """
        Initialize MACD strategy.
        
        Args:
            fast_period: Fast EMA period (default: 12)
            slow_period: Slow EMA period (default: 26)
            signal_period: Signal line EMA period (default: 9)
        """
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period
        super().__init__(
            name=f"MACD ({fast_period}/{slow_period}/{signal_period})"
        )
    
    def calculate_ema(self, data: pd.Series, period: int) -> pd.Series:
        """Calculate Exponential Moving Average."""
        return data.ewm(span=period, adjust=False).mean()
    
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate MACD indicators.
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            DataFrame with added indicator columns
        """
        df = data.copy()
        
        # Calculate MACD components
        fast_ema = self.calculate_ema(df['close'], self.fast_period)
        slow_ema = self.calculate_ema(df['close'], self.slow_period)
        
        # MACD Line = Fast EMA - Slow EMA
        df['macd'] = fast_ema - slow_ema
        
        # Signal Line = EMA of MACD Line
        df['macd_signal'] = self.calculate_ema(df['macd'], self.signal_period)
        
        # MACD Histogram = MACD Line - Signal Line
        df['macd_histogram'] = df['macd'] - df['macd_signal']
        
        return df
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate trading signals based on MACD.
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            Series with signals: 1 (buy), -1 (sell), 0 (hold)
        """
        # Calculate MACD components
        fast_ema = self.calculate_ema(data['close'], self.fast_period)
        slow_ema = self.calculate_ema(data['close'], self.slow_period)
        
        # MACD Line = Fast EMA - Slow EMA
        macd_line = fast_ema - slow_ema
        
        # Signal Line = EMA of MACD Line
        signal_line = self.calculate_ema(macd_line, self.signal_period)
        
        # MACD Histogram = MACD Line - Signal Line
        histogram = macd_line - signal_line
        
        # Initialize signals
        signals = pd.Series(0, index=data.index)
        
        # Generate crossover signals
        for i in range(1, len(data)):
            # Bullish crossover: MACD crosses above signal line
            if macd_line.iloc[i] > signal_line.iloc[i] and \
               macd_line.iloc[i-1] <= signal_line.iloc[i-1]:
                signals.iloc[i] = 1  # Buy signal
            
            # Bearish crossover: MACD crosses below signal line
            elif macd_line.iloc[i] < signal_line.iloc[i] and \
                 macd_line.iloc[i-1] >= signal_line.iloc[i-1]:
                signals.iloc[i] = -1  # Sell signal
        
        return signals
    
    def __str__(self):
        return f"MACD ({self.fast_period}/{self.slow_period}/{self.signal_period})"


if __name__ == "__main__":
    # Example usage
    import logging
    from src.data.data_fetcher import DataFetcher
    
    logging.basicConfig(level=logging.INFO)
    
    # Fetch data
    fetcher = DataFetcher(data_provider='yahoo')
    data = fetcher.fetch_historical_data(
        symbol='AAPL',
        start_date='2023-01-01',
        end_date='2024-01-01'
    )
    
    # Create strategy
    strategy = MACDStrategy(fast_period=12, slow_period=26, signal_period=9)
    
    # Generate signals
    signals = strategy.generate_signals(data)
    
    # Print statistics
    print(f"\nStrategy: {strategy}")
    print(f"Total signals: {len(signals[signals != 0])}")
    print(f"Buy signals: {len(signals[signals == 1])}")
    print(f"Sell signals: {len(signals[signals == -1])}")
