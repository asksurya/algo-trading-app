"""
ATR Trailing Stop Trading Strategy.

Uses Average True Range for volatility-adjusted stop-loss management.
Popular among professional traders for dynamic position management.
"""

import pandas as pd
import numpy as np
from .base_strategy import BaseStrategy, Signal


class ATRTrailingStopStrategy(BaseStrategy):
    """
    ATR Trailing Stop strategy implementation.

    Entry: Price above EMA (trend filter)
    Stop: ATR-based trailing stop that moves with price
    Chandelier Exit variant: Stop from highest high
    """

    def __init__(
        self,
        atr_period: int = 14,
        atr_multiplier: float = 3.0,
        trend_period: int = 50,
        use_chandelier: bool = True
    ):
        """
        Initialize ATR Trailing Stop strategy.

        Args:
            atr_period: Period for ATR calculation (default 14)
            atr_multiplier: Stop distance multiplier (default 3.0)
            trend_period: Period for trend EMA (default 50)
            use_chandelier: Use Chandelier Exit method (default True)
        """
        super().__init__(name="ATR Trailing Stop")
        self.atr_period = atr_period
        self.atr_multiplier = atr_multiplier
        self.trend_period = trend_period
        self.use_chandelier = use_chandelier

    def calculate_atr(self, data: pd.DataFrame, period: int) -> pd.Series:
        """Calculate Average True Range."""
        high = data['high']
        low = data['low']
        close = data['close']

        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))

        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = true_range.rolling(window=period).mean()

        return atr

    def calculate_ema(self, series: pd.Series, period: int) -> pd.Series:
        """Calculate Exponential Moving Average."""
        return series.ewm(span=period, adjust=False).mean()

    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate ATR trailing stop indicators."""
        df = data.copy()

        # ATR for stop calculation
        df['atr'] = self.calculate_atr(df, self.atr_period)

        # Trend filter (EMA)
        df['trend_ema'] = self.calculate_ema(df['close'], self.trend_period)

        # Trailing stop calculation
        atr_stop_distance = self.atr_multiplier * df['atr']

        if self.use_chandelier:
            # Chandelier Exit: Stop from highest high
            df['highest_high'] = df['high'].rolling(window=self.atr_period).max()
            df['trailing_stop_long'] = df['highest_high'] - atr_stop_distance
            df['lowest_low'] = df['low'].rolling(window=self.atr_period).min()
            df['trailing_stop_short'] = df['lowest_low'] + atr_stop_distance
        else:
            # Simple ATR stop from close
            df['trailing_stop_long'] = df['close'] - atr_stop_distance
            df['trailing_stop_short'] = df['close'] + atr_stop_distance

        # Trend direction
        df['trend_up'] = df['close'] > df['trend_ema']

        return df

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate trading signals.

        BUY: Price above trend EMA and not stopped out
        SELL: Price crosses below trailing stop
        """
        df = self.calculate_indicators(data)
        signals = pd.Series(0, index=df.index)

        # BUY signal: Price crosses above trend EMA
        buy_condition = (
            (df['close'] > df['trend_ema']) &
            (df['close'].shift(1) <= df['trend_ema'].shift(1))
        )

        # SELL signal: Price crosses below trailing stop
        sell_condition = (
            (df['close'] < df['trailing_stop_long']) &
            (df['close'].shift(1) >= df['trailing_stop_long'].shift(1))
        )

        signals[buy_condition] = Signal.BUY.value
        signals[sell_condition] = Signal.SELL.value

        return signals

    def get_strategy_state(self, data: pd.DataFrame) -> dict:
        """Get current strategy state."""
        df = self.calculate_indicators(data)

        required_periods = max(self.atr_period, self.trend_period)
        if len(df) < required_periods:
            return {
                'status': 'insufficient_data',
                'message': f'Need at least {required_periods} data points'
            }

        latest = df.iloc[-1]

        if latest['close'] > latest['trend_ema']:
            trend = 'bullish'
        else:
            trend = 'bearish'

        return {
            'status': 'active',
            'atr': latest['atr'],
            'trend_ema': latest['trend_ema'],
            'trailing_stop_long': latest['trailing_stop_long'],
            'trailing_stop_short': latest['trailing_stop_short'],
            'current_price': latest['close'],
            'trend': trend,
            'atr_multiplier': self.atr_multiplier,
            'use_chandelier': self.use_chandelier
        }

    def __str__(self) -> str:
        mode = 'chandelier' if self.use_chandelier else 'simple'
        return f"ATRTrailingStop(atr={self.atr_period}, mult={self.atr_multiplier}, trend={self.trend_period}, mode={mode})"
