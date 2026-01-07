"""
Donchian Channel (Turtle Trading) Strategy.

The most famous trading experiment in history.
Richard Dennis's Turtles made $175 million in 5 years using this system.
"""

import pandas as pd
import numpy as np
from .base_strategy import BaseStrategy, Signal


class DonchianChannelStrategy(BaseStrategy):
    """
    Donchian Channel (Turtle Trading) strategy implementation.

    System 1: 20-day breakout entry, 10-day exit
    System 2: 55-day breakout entry, 20-day exit

    Uses ATR for stop-loss and position sizing.
    """

    def __init__(
        self,
        entry_period: int = 20,
        exit_period: int = 10,
        atr_period: int = 20,
        use_system_2: bool = False
    ):
        """
        Initialize Donchian Channel strategy.

        Args:
            entry_period: Period for entry breakout (default 20, or 55 for System 2)
            exit_period: Period for exit (default 10, or 20 for System 2)
            atr_period: Period for ATR calculation (default 20)
            use_system_2: Use System 2 (55/20) instead of System 1 (20/10)
        """
        super().__init__(name="Donchian Channel")

        if use_system_2:
            self.entry_period = 55
            self.exit_period = 20
        else:
            self.entry_period = entry_period
            self.exit_period = exit_period

        self.atr_period = atr_period
        self.use_system_2 = use_system_2

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

    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate Donchian Channel indicators."""
        df = data.copy()

        # Entry channel (e.g., 20-day or 55-day)
        df['entry_high'] = df['high'].rolling(window=self.entry_period).max()
        df['entry_low'] = df['low'].rolling(window=self.entry_period).min()

        # Exit channel (e.g., 10-day or 20-day)
        df['exit_high'] = df['high'].rolling(window=self.exit_period).max()
        df['exit_low'] = df['low'].rolling(window=self.exit_period).min()

        # ATR for stops
        df['atr'] = self.calculate_atr(df, self.atr_period)

        # Middle line (for reference)
        df['donchian_middle'] = (df['entry_high'] + df['entry_low']) / 2

        return df

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate trading signals based on Donchian Channel breakouts.

        BUY: Price breaks above entry_period high
        SELL: Price breaks below exit_period low (or entry_period low for shorts)
        """
        df = self.calculate_indicators(data)
        signals = pd.Series(0, index=df.index)

        # Use previous period's channel to avoid look-ahead bias
        prev_entry_high = df['entry_high'].shift(1)
        prev_exit_low = df['exit_low'].shift(1)

        # BUY: Close breaks above previous N-day high
        buy_condition = df['close'] > prev_entry_high

        # SELL: Close breaks below previous exit period low
        sell_condition = df['close'] < prev_exit_low

        signals[buy_condition] = Signal.BUY.value
        signals[sell_condition] = Signal.SELL.value

        return signals

    def get_strategy_state(self, data: pd.DataFrame) -> dict:
        """Get current strategy state."""
        df = self.calculate_indicators(data)

        required_periods = max(self.entry_period, self.exit_period)
        if len(df) < required_periods:
            return {
                'status': 'insufficient_data',
                'message': f'Need at least {required_periods} data points'
            }

        latest = df.iloc[-1]

        # Determine position in channel
        channel_width = latest['entry_high'] - latest['entry_low']
        if channel_width > 0:
            position_pct = (latest['close'] - latest['entry_low']) / channel_width
        else:
            position_pct = 0.5

        return {
            'status': 'active',
            'entry_high': latest['entry_high'],
            'entry_low': latest['entry_low'],
            'exit_high': latest['exit_high'],
            'exit_low': latest['exit_low'],
            'donchian_middle': latest['donchian_middle'],
            'atr': latest['atr'],
            'current_price': latest['close'],
            'position_in_channel': position_pct,
            'system': 'System 2' if self.use_system_2 else 'System 1'
        }

    def __str__(self) -> str:
        system = 'System2' if self.use_system_2 else 'System1'
        return f"DonchianChannel({system}, entry={self.entry_period}, exit={self.exit_period})"
