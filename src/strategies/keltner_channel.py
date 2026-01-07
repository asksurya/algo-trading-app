"""
Keltner Channel Trading Strategy.

Uses EMA-based channels with ATR for volatility measurement.
More stable than Bollinger Bands in volatile markets.
"""

import pandas as pd
import numpy as np
from .base_strategy import BaseStrategy, Signal


class KeltnerChannelStrategy(BaseStrategy):
    """
    Keltner Channel strategy implementation.

    Middle Line: EMA of close prices
    Upper Band: EMA + (ATR * multiplier)
    Lower Band: EMA - (ATR * multiplier)

    Supports both breakout and mean reversion modes.
    """

    def __init__(
        self,
        ema_period: int = 20,
        atr_period: int = 10,
        multiplier: float = 2.0,
        use_breakout: bool = True
    ):
        """
        Initialize Keltner Channel strategy.

        Args:
            ema_period: Period for EMA calculation (default 20)
            atr_period: Period for ATR calculation (default 10)
            multiplier: Band width multiplier (default 2.0)
            use_breakout: True for breakout mode, False for mean reversion
        """
        super().__init__(name="Keltner Channel")
        self.ema_period = ema_period
        self.atr_period = atr_period
        self.multiplier = multiplier
        self.use_breakout = use_breakout

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
        """Calculate Keltner Channel indicators."""
        df = data.copy()

        # Middle line (EMA)
        df['kc_middle'] = self.calculate_ema(df['close'], self.ema_period)

        # ATR for band width
        df['atr'] = self.calculate_atr(df, self.atr_period)

        # Upper and lower bands
        df['kc_upper'] = df['kc_middle'] + (self.multiplier * df['atr'])
        df['kc_lower'] = df['kc_middle'] - (self.multiplier * df['atr'])

        # Position within channel (0 = lower, 1 = upper)
        df['kc_position'] = (df['close'] - df['kc_lower']) / (df['kc_upper'] - df['kc_lower'])

        return df

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate trading signals.

        Breakout mode:
            BUY: Close breaks above upper band
            SELL: Close breaks below lower band

        Mean reversion mode:
            BUY: Close touches lower band
            SELL: Close touches upper band
        """
        df = self.calculate_indicators(data)
        signals = pd.Series(0, index=df.index)

        if self.use_breakout:
            # Breakout mode: trade with the trend
            buy_condition = df['close'] > df['kc_upper']
            sell_condition = df['close'] < df['kc_lower']
        else:
            # Mean reversion mode: fade the extremes
            buy_condition = (df['close'] <= df['kc_lower']) | (df['kc_position'] <= 0.05)
            sell_condition = (df['close'] >= df['kc_upper']) | (df['kc_position'] >= 0.95)

        signals[buy_condition] = Signal.BUY.value
        signals[sell_condition] = Signal.SELL.value

        return signals

    def get_strategy_state(self, data: pd.DataFrame) -> dict:
        """Get current strategy state."""
        df = self.calculate_indicators(data)

        if len(df) < max(self.ema_period, self.atr_period):
            return {
                'status': 'insufficient_data',
                'message': f'Need at least {max(self.ema_period, self.atr_period)} data points'
            }

        latest = df.iloc[-1]

        if latest['close'] > latest['kc_upper']:
            condition = 'above_upper'
        elif latest['close'] < latest['kc_lower']:
            condition = 'below_lower'
        else:
            condition = 'within_channel'

        return {
            'status': 'active',
            'kc_upper': latest['kc_upper'],
            'kc_middle': latest['kc_middle'],
            'kc_lower': latest['kc_lower'],
            'kc_position': latest['kc_position'],
            'atr': latest['atr'],
            'current_price': latest['close'],
            'condition': condition,
            'mode': 'breakout' if self.use_breakout else 'mean_reversion'
        }

    def __str__(self) -> str:
        mode = 'breakout' if self.use_breakout else 'mean_reversion'
        return f"KeltnerChannel(ema={self.ema_period}, atr={self.atr_period}, mult={self.multiplier}, mode={mode})"
