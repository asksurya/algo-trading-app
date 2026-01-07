"""
Ichimoku Cloud Trading Strategy.

Comprehensive Japanese charting system developed in the 1940s.
Shows trend, momentum, support/resistance all in one view.
"Balance at a glance" - very popular globally, especially in Asia.
"""

import pandas as pd
import numpy as np
from .base_strategy import BaseStrategy, Signal


class IchimokuCloudStrategy(BaseStrategy):
    """
    Ichimoku Cloud strategy implementation.

    Components:
    - Tenkan-sen (Conversion Line): 9-period midpoint
    - Kijun-sen (Base Line): 26-period midpoint
    - Senkou Span A: Midpoint of Tenkan/Kijun, shifted 26 forward
    - Senkou Span B: 52-period midpoint, shifted 26 forward
    - Chikou Span: Current close shifted 26 back
    """

    def __init__(
        self,
        tenkan_period: int = 9,
        kijun_period: int = 26,
        senkou_b_period: int = 52,
        displacement: int = 26
    ):
        """
        Initialize Ichimoku Cloud strategy.

        Args:
            tenkan_period: Conversion line period (default 9)
            kijun_period: Base line period (default 26)
            senkou_b_period: Leading Span B period (default 52)
            displacement: Cloud displacement (default 26)
        """
        super().__init__(name="Ichimoku Cloud")
        self.tenkan_period = tenkan_period
        self.kijun_period = kijun_period
        self.senkou_b_period = senkou_b_period
        self.displacement = displacement

    def calculate_midpoint(self, data: pd.DataFrame, period: int) -> pd.Series:
        """Calculate midpoint (highest high + lowest low) / 2."""
        high = data['high'].rolling(window=period).max()
        low = data['low'].rolling(window=period).min()
        return (high + low) / 2

    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate all Ichimoku Cloud components."""
        df = data.copy()

        # Tenkan-sen (Conversion Line): 9-period midpoint
        df['tenkan_sen'] = self.calculate_midpoint(df, self.tenkan_period)

        # Kijun-sen (Base Line): 26-period midpoint
        df['kijun_sen'] = self.calculate_midpoint(df, self.kijun_period)

        # Senkou Span A (Leading Span A): midpoint of Tenkan/Kijun, shifted 26 forward
        df['senkou_span_a'] = ((df['tenkan_sen'] + df['kijun_sen']) / 2).shift(self.displacement)

        # Senkou Span B (Leading Span B): 52-period midpoint, shifted 26 forward
        df['senkou_span_b'] = self.calculate_midpoint(df, self.senkou_b_period).shift(self.displacement)

        # Chikou Span (Lagging Span): current close shifted 26 back
        df['chikou_span'] = df['close'].shift(-self.displacement)

        # Cloud top and bottom (for current analysis, unshifted)
        df['cloud_top'] = df[['senkou_span_a', 'senkou_span_b']].max(axis=1)
        df['cloud_bottom'] = df[['senkou_span_a', 'senkou_span_b']].min(axis=1)

        # Future cloud (current values, represent future cloud)
        df['future_senkou_a'] = (df['tenkan_sen'] + df['kijun_sen']) / 2
        df['future_senkou_b'] = self.calculate_midpoint(df, self.senkou_b_period)

        # Cloud color (1 = green/bullish, -1 = red/bearish)
        df['cloud_color'] = np.where(df['senkou_span_a'] > df['senkou_span_b'], 1, -1)

        return df

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate trading signals based on Ichimoku Cloud.

        Strong BUY conditions (all must be true):
        - Price above cloud
        - Tenkan-sen above Kijun-sen
        - Future cloud is green (bullish)

        Strong SELL conditions:
        - Price below cloud
        - Tenkan-sen below Kijun-sen
        - Future cloud is red (bearish)
        """
        df = self.calculate_indicators(data)
        signals = pd.Series(0, index=df.index)

        # TK Cross detection (Tenkan crosses Kijun)
        tk_cross_up = (df['tenkan_sen'] > df['kijun_sen']) & (df['tenkan_sen'].shift(1) <= df['kijun_sen'].shift(1))
        tk_cross_down = (df['tenkan_sen'] < df['kijun_sen']) & (df['tenkan_sen'].shift(1) >= df['kijun_sen'].shift(1))

        # Price position relative to cloud
        price_above_cloud = df['close'] > df['cloud_top']
        price_below_cloud = df['close'] < df['cloud_bottom']

        # Future cloud bullish/bearish
        future_cloud_bullish = df['future_senkou_a'] > df['future_senkou_b']
        future_cloud_bearish = df['future_senkou_a'] < df['future_senkou_b']

        # Strong BUY: TK cross up + price above cloud + bullish future cloud
        strong_buy = tk_cross_up & price_above_cloud & future_cloud_bullish

        # Strong SELL: TK cross down + price below cloud + bearish future cloud
        strong_sell = tk_cross_down & price_below_cloud & future_cloud_bearish

        # Weak BUY: TK cross up (any position)
        weak_buy = tk_cross_up & ~strong_buy

        # Weak SELL: TK cross down (any position)
        weak_sell = tk_cross_down & ~strong_sell

        # Apply signals (strong signals take precedence)
        signals[strong_buy] = Signal.BUY.value
        signals[strong_sell] = Signal.SELL.value
        signals[weak_buy & (signals == 0)] = Signal.BUY.value
        signals[weak_sell & (signals == 0)] = Signal.SELL.value

        return signals

    def get_strategy_state(self, data: pd.DataFrame) -> dict:
        """Get current strategy state."""
        df = self.calculate_indicators(data)

        required_periods = max(self.senkou_b_period, self.kijun_period + self.displacement)
        if len(df) < required_periods:
            return {
                'status': 'insufficient_data',
                'message': f'Need at least {required_periods} data points'
            }

        latest = df.iloc[-1]

        # Determine overall bias
        if latest['close'] > latest['cloud_top'] and latest['tenkan_sen'] > latest['kijun_sen']:
            bias = 'strongly_bullish'
        elif latest['close'] > latest['cloud_top']:
            bias = 'bullish'
        elif latest['close'] < latest['cloud_bottom'] and latest['tenkan_sen'] < latest['kijun_sen']:
            bias = 'strongly_bearish'
        elif latest['close'] < latest['cloud_bottom']:
            bias = 'bearish'
        else:
            bias = 'neutral'

        return {
            'status': 'active',
            'tenkan_sen': latest['tenkan_sen'],
            'kijun_sen': latest['kijun_sen'],
            'senkou_span_a': latest['senkou_span_a'],
            'senkou_span_b': latest['senkou_span_b'],
            'cloud_top': latest['cloud_top'],
            'cloud_bottom': latest['cloud_bottom'],
            'current_price': latest['close'],
            'cloud_color': 'green' if latest['cloud_color'] == 1 else 'red',
            'bias': bias
        }

    def __str__(self) -> str:
        return f"IchimokuCloud(tenkan={self.tenkan_period}, kijun={self.kijun_period}, senkou_b={self.senkou_b_period})"
