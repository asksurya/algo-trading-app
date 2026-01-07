"""
Stochastic Oscillator Trading Strategy.

Uses %K and %D crossovers in overbought/oversold zones to generate signals.
Developed by George Lane in the 1950s.
"""

import pandas as pd
from .base_strategy import BaseStrategy, Signal


class StochasticStrategy(BaseStrategy):
    """
    Stochastic Oscillator strategy implementation.

    Generates BUY signals when %K crosses above %D in oversold zone.
    Generates SELL signals when %K crosses below %D in overbought zone.
    """

    def __init__(
        self,
        k_period: int = 14,
        d_period: int = 3,
        smooth_k: int = 3,
        oversold: int = 20,
        overbought: int = 80
    ):
        """
        Initialize Stochastic strategy.

        Args:
            k_period: Lookback period for %K (default 14)
            d_period: Smoothing period for %D (default 3)
            smooth_k: Smoothing period for slow %K (default 3)
            oversold: Oversold threshold (default 20)
            overbought: Overbought threshold (default 80)
        """
        super().__init__(name="Stochastic")
        self.k_period = k_period
        self.d_period = d_period
        self.smooth_k = smooth_k
        self.oversold = oversold
        self.overbought = overbought

        if not (0 < oversold < overbought < 100):
            raise ValueError("Invalid thresholds: 0 < oversold < overbought < 100")

    def calculate_stochastic(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate Stochastic %K and %D.

        %K = 100 * (Close - Low_N) / (High_N - Low_N)
        %D = SMA of %K
        """
        df = data.copy()

        # Calculate highest high and lowest low over k_period
        low_min = df['low'].rolling(window=self.k_period).min()
        high_max = df['high'].rolling(window=self.k_period).max()

        # Fast %K
        fast_k = 100 * (df['close'] - low_min) / (high_max - low_min)

        # Slow %K (smoothed)
        df['stoch_k'] = fast_k.rolling(window=self.smooth_k).mean()

        # %D (signal line)
        df['stoch_d'] = df['stoch_k'].rolling(window=self.d_period).mean()

        return df

    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate all stochastic indicators."""
        return self.calculate_stochastic(data)

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate trading signals based on Stochastic crossovers.

        BUY: %K crosses above %D below oversold threshold
        SELL: %K crosses below %D above overbought threshold
        """
        df = self.calculate_indicators(data)
        signals = pd.Series(0, index=df.index)

        # Previous values for crossover detection
        prev_k = df['stoch_k'].shift(1)
        prev_d = df['stoch_d'].shift(1)

        # BUY: %K crosses above %D in oversold zone
        buy_condition = (
            (df['stoch_k'] > df['stoch_d']) &  # %K above %D now
            (prev_k <= prev_d) &                # %K was below/equal %D before
            (df['stoch_k'] < self.oversold)     # In oversold zone
        )

        # SELL: %K crosses below %D in overbought zone
        sell_condition = (
            (df['stoch_k'] < df['stoch_d']) &   # %K below %D now
            (prev_k >= prev_d) &                 # %K was above/equal %D before
            (df['stoch_k'] > self.overbought)   # In overbought zone
        )

        signals[buy_condition] = Signal.BUY.value
        signals[sell_condition] = Signal.SELL.value

        return signals

    def get_strategy_state(self, data: pd.DataFrame) -> dict:
        """Get current strategy state for monitoring."""
        df = self.calculate_indicators(data)

        if len(df) < self.k_period + self.d_period:
            return {
                'status': 'insufficient_data',
                'message': f'Need at least {self.k_period + self.d_period} data points'
            }

        latest = df.iloc[-1]

        if latest['stoch_k'] < self.oversold:
            condition = 'oversold'
        elif latest['stoch_k'] > self.overbought:
            condition = 'overbought'
        else:
            condition = 'neutral'

        return {
            'status': 'active',
            'stoch_k': latest['stoch_k'],
            'stoch_d': latest['stoch_d'],
            'current_price': latest['close'],
            'condition': condition,
            'k_period': self.k_period,
            'd_period': self.d_period
        }

    def __str__(self) -> str:
        return f"Stochastic(k={self.k_period}, d={self.d_period}, oversold={self.oversold}, overbought={self.overbought})"
