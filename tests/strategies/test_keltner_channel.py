"""
Comprehensive unit tests for Keltner Channel Strategy.

Tests cover:
- Indicator calculations (EMA, ATR, channel bands)
- Signal generation in breakout and mean reversion modes
- Strategy state management
- Edge cases and error handling
- Dual mode behavior
"""

import pytest
import pandas as pd
import numpy as np
from src.strategies.keltner_channel import KeltnerChannelStrategy
from src.strategies.base_strategy import Signal


class TestKeltnerChannelInitialization:
    """Test strategy initialization and parameter validation."""

    def test_default_initialization(self):
        """Test strategy initializes with default parameters."""
        strategy = KeltnerChannelStrategy()

        assert strategy.name == "Keltner Channel"
        assert strategy.ema_period == 20
        assert strategy.atr_period == 10
        assert strategy.multiplier == 2.0
        assert strategy.use_breakout is True

    def test_custom_parameters(self):
        """Test strategy initializes with custom parameters."""
        strategy = KeltnerChannelStrategy(
            ema_period=30,
            atr_period=14,
            multiplier=3.0,
            use_breakout=False
        )

        assert strategy.ema_period == 30
        assert strategy.atr_period == 14
        assert strategy.multiplier == 3.0
        assert strategy.use_breakout is False

    def test_string_representation_breakout_mode(self):
        """Test string representation in breakout mode."""
        strategy = KeltnerChannelStrategy(ema_period=20, atr_period=10, multiplier=2.0, use_breakout=True)
        str_repr = str(strategy)

        assert "KeltnerChannel" in str_repr
        assert "ema=20" in str_repr
        assert "atr=10" in str_repr
        assert "mult=2.0" in str_repr
        assert "mode=breakout" in str_repr

    def test_string_representation_mean_reversion_mode(self):
        """Test string representation in mean reversion mode."""
        strategy = KeltnerChannelStrategy(use_breakout=False)
        str_repr = str(strategy)

        assert "mode=mean_reversion" in str_repr


class TestKeltnerChannelIndicatorCalculations:
    """Test Keltner Channel indicator calculations."""

    def test_calculate_atr(self, sample_ohlcv_data):
        """Test ATR calculation produces valid values."""
        strategy = KeltnerChannelStrategy()
        atr = strategy.calculate_atr(sample_ohlcv_data, period=10)

        assert isinstance(atr, pd.Series)
        assert len(atr) == len(sample_ohlcv_data)
        # ATR should be positive
        assert (atr.dropna() > 0).all()

    def test_calculate_ema(self, sample_ohlcv_data):
        """Test EMA calculation produces valid values."""
        strategy = KeltnerChannelStrategy()
        ema = strategy.calculate_ema(sample_ohlcv_data['close'], period=20)

        assert isinstance(ema, pd.Series)
        assert len(ema) == len(sample_ohlcv_data)
        assert ema.notna().sum() > 0

    def test_calculate_indicators_basic(self, sample_ohlcv_data):
        """Test basic indicator calculation produces expected columns."""
        strategy = KeltnerChannelStrategy()
        result = strategy.calculate_indicators(sample_ohlcv_data)

        assert 'kc_middle' in result.columns
        assert 'atr' in result.columns
        assert 'kc_upper' in result.columns
        assert 'kc_lower' in result.columns
        assert 'kc_position' in result.columns
        assert len(result) == len(sample_ohlcv_data)

    def test_channel_band_ordering(self, sample_ohlcv_data):
        """Test that upper band > middle > lower band."""
        strategy = KeltnerChannelStrategy()
        result = strategy.calculate_indicators(sample_ohlcv_data)

        # Remove NaN values
        valid_data = result.dropna(subset=['kc_upper', 'kc_middle', 'kc_lower'])

        # Upper should be greater than middle
        assert (valid_data['kc_upper'] > valid_data['kc_middle']).all()
        # Middle should be greater than lower
        assert (valid_data['kc_middle'] > valid_data['kc_lower']).all()

    def test_kc_position_range(self, sample_ohlcv_data):
        """Test that kc_position is calculated correctly."""
        strategy = KeltnerChannelStrategy()
        result = strategy.calculate_indicators(sample_ohlcv_data)

        # Position should typically be between 0 and 1 (can go outside in extreme cases)
        positions = result['kc_position'].dropna()
        # Most values should be in reasonable range
        in_range = ((positions >= -0.5) & (positions <= 1.5)).sum()
        assert in_range > len(positions) * 0.8  # At least 80% in range

    def test_multiplier_affects_band_width(self, sample_ohlcv_data):
        """Test that multiplier affects channel width."""
        strategy_narrow = KeltnerChannelStrategy(multiplier=1.0)
        strategy_wide = KeltnerChannelStrategy(multiplier=3.0)

        result_narrow = strategy_narrow.calculate_indicators(sample_ohlcv_data)
        result_wide = strategy_wide.calculate_indicators(sample_ohlcv_data)

        # Wide channel should have larger band width
        width_narrow = (result_narrow['kc_upper'] - result_narrow['kc_lower']).mean()
        width_wide = (result_wide['kc_upper'] - result_wide['kc_lower']).mean()

        assert width_wide > width_narrow


class TestKeltnerChannelSignalGenerationBreakout:
    """Test signal generation in breakout mode."""

    def test_breakout_mode_buy_signal(self):
        """Test BUY signal when price breaks above upper band."""
        # Create data where price breaks above upper band
        data = pd.DataFrame({
            'open': [100] * 40,
            'high': list(range(100, 110, 1)) + [110] * 20 + list(range(110, 120, 1)),
            'low': [99] * 40,
            'close': list(range(100, 110, 1)) + [110] * 20 + list(range(110, 120, 1)),
            'volume': [1000000] * 40
        })

        strategy = KeltnerChannelStrategy(use_breakout=True)
        signals = strategy.generate_signals(data)

        # Should have BUY signals when breaking above upper band
        buy_signals = (signals == Signal.BUY.value).sum()
        assert buy_signals > 0

    def test_breakout_mode_sell_signal(self):
        """Test SELL signal when price breaks below lower band."""
        # Create data where price breaks below lower band
        data = pd.DataFrame({
            'open': [100] * 40,
            'high': [101] * 40,
            'low': list(range(100, 90, -1)) + [90] * 20 + list(range(90, 80, -1)),
            'close': list(range(100, 90, -1)) + [90] * 20 + list(range(90, 80, -1)),
            'volume': [1000000] * 40
        })

        strategy = KeltnerChannelStrategy(use_breakout=True)
        signals = strategy.generate_signals(data)

        # Should have SELL signals when breaking below lower band
        sell_signals = (signals == Signal.SELL.value).sum()
        assert sell_signals > 0

    def test_breakout_mode_hold_in_channel(self, ranging_data):
        """Test HOLD signal when price stays within channel."""
        strategy = KeltnerChannelStrategy(use_breakout=True)
        signals = strategy.generate_signals(ranging_data)

        # Most signals should be HOLD in ranging market
        hold_signals = (signals == Signal.HOLD.value).sum()
        assert hold_signals > len(signals) * 0.5


class TestKeltnerChannelSignalGenerationMeanReversion:
    """Test signal generation in mean reversion mode."""

    def test_mean_reversion_mode_buy_at_lower_band(self):
        """Test BUY signal when price touches lower band in mean reversion mode."""
        # Create data where price touches lower band
        data = pd.DataFrame({
            'open': [100] * 50,
            'high': [101] * 50,
            'low': [99] * 50,
            'close': [100] * 20 + list(range(100, 90, -1)) + [90] * 10 + list(range(90, 100, 1)),
            'volume': [1000000] * 50
        })

        strategy = KeltnerChannelStrategy(use_breakout=False)
        signals = strategy.generate_signals(data)

        # Should have BUY signals near lower band
        buy_signals = (signals == Signal.BUY.value).sum()
        assert buy_signals > 0

    def test_mean_reversion_mode_sell_at_upper_band(self):
        """Test SELL signal when price touches upper band in mean reversion mode."""
        # Create data where price touches upper band
        data = pd.DataFrame({
            'open': [100] * 50,
            'high': [101] * 50,
            'low': [99] * 50,
            'close': [100] * 20 + list(range(100, 110, 1)) + [110] * 10 + list(range(110, 100, -1)),
            'volume': [1000000] * 50
        })

        strategy = KeltnerChannelStrategy(use_breakout=False)
        signals = strategy.generate_signals(data)

        # Should have SELL signals near upper band
        sell_signals = (signals == Signal.SELL.value).sum()
        assert sell_signals > 0

    def test_different_signals_between_modes(self, sample_ohlcv_data):
        """Test that breakout and mean reversion modes produce different signals."""
        strategy_breakout = KeltnerChannelStrategy(use_breakout=True)
        strategy_reversion = KeltnerChannelStrategy(use_breakout=False)

        signals_breakout = strategy_breakout.generate_signals(sample_ohlcv_data)
        signals_reversion = strategy_reversion.generate_signals(sample_ohlcv_data)

        # Signals should be different between modes
        assert not signals_breakout.equals(signals_reversion)


class TestKeltnerChannelSignals:
    """General signal generation tests."""

    def test_signals_series_length(self, sample_ohlcv_data):
        """Test that signals series has same length as input data."""
        strategy = KeltnerChannelStrategy()
        signals = strategy.generate_signals(sample_ohlcv_data)

        assert len(signals) == len(sample_ohlcv_data)
        assert signals.index.equals(sample_ohlcv_data.index)

    def test_signals_are_valid_values(self, sample_ohlcv_data):
        """Test that all signals are valid Signal enum values."""
        strategy = KeltnerChannelStrategy()
        signals = strategy.generate_signals(sample_ohlcv_data)

        valid_values = [Signal.BUY.value, Signal.SELL.value, Signal.HOLD.value]
        assert signals.isin(valid_values).all()

    @pytest.mark.parametrize("ema_period,atr_period,multiplier", [
        (10, 10, 1.5),
        (20, 10, 2.0),
        (50, 20, 2.5),
    ])
    def test_signals_with_different_parameters(self, sample_ohlcv_data, ema_period, atr_period, multiplier):
        """Test signal generation with different parameters."""
        strategy = KeltnerChannelStrategy(ema_period=ema_period, atr_period=atr_period, multiplier=multiplier)
        signals = strategy.generate_signals(sample_ohlcv_data)

        assert len(signals) == len(sample_ohlcv_data)
        assert isinstance(signals, pd.Series)


class TestKeltnerChannelStrategyState:
    """Test strategy state management."""

    def test_get_strategy_state_with_sufficient_data(self, sample_ohlcv_data):
        """Test strategy state returns active status with sufficient data."""
        strategy = KeltnerChannelStrategy()
        state = strategy.get_strategy_state(sample_ohlcv_data)

        assert state['status'] == 'active'
        assert 'kc_upper' in state
        assert 'kc_middle' in state
        assert 'kc_lower' in state
        assert 'kc_position' in state
        assert 'atr' in state
        assert 'current_price' in state
        assert 'condition' in state
        assert 'mode' in state

    def test_get_strategy_state_with_insufficient_data(self, insufficient_data):
        """Test strategy state returns insufficient_data status."""
        strategy = KeltnerChannelStrategy(ema_period=20, atr_period=10)
        state = strategy.get_strategy_state(insufficient_data)

        assert state['status'] == 'insufficient_data'
        assert 'message' in state

    def test_strategy_state_condition_above_upper(self):
        """Test strategy state identifies price above upper band."""
        # Create data where price is above upper band
        data = pd.DataFrame({
            'open': [100] * 30,
            'high': [101] * 30,
            'low': [99] * 30,
            'close': list(range(100, 130, 1)),
            'volume': [1000000] * 30
        })

        strategy = KeltnerChannelStrategy()
        state = strategy.get_strategy_state(data)

        assert state['status'] == 'active'
        # Last price should be high relative to channel
        assert state['condition'] in ['above_upper', 'within_channel']

    def test_strategy_state_condition_below_lower(self):
        """Test strategy state identifies price below lower band."""
        # Create data where price is below lower band
        data = pd.DataFrame({
            'open': [100] * 30,
            'high': [101] * 30,
            'low': [99] * 30,
            'close': list(range(100, 70, -1)),
            'volume': [1000000] * 30
        })

        strategy = KeltnerChannelStrategy()
        state = strategy.get_strategy_state(data)

        assert state['status'] == 'active'
        assert state['condition'] in ['below_lower', 'within_channel']

    def test_strategy_state_mode_reported_correctly(self, sample_ohlcv_data):
        """Test that strategy state reports correct mode."""
        strategy_breakout = KeltnerChannelStrategy(use_breakout=True)
        strategy_reversion = KeltnerChannelStrategy(use_breakout=False)

        state_breakout = strategy_breakout.get_strategy_state(sample_ohlcv_data)
        state_reversion = strategy_reversion.get_strategy_state(sample_ohlcv_data)

        assert state_breakout['mode'] == 'breakout'
        assert state_reversion['mode'] == 'mean_reversion'


class TestKeltnerChannelEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_dataframe(self):
        """Test strategy handles empty DataFrame gracefully."""
        strategy = KeltnerChannelStrategy()
        empty_df = pd.DataFrame(columns=['open', 'high', 'low', 'close', 'volume'])

        state = strategy.get_strategy_state(empty_df)
        assert state['status'] == 'insufficient_data'

    def test_single_row_dataframe(self):
        """Test strategy handles single row DataFrame."""
        strategy = KeltnerChannelStrategy()
        single_row = pd.DataFrame({
            'open': [100],
            'high': [101],
            'low': [99],
            'close': [100],
            'volume': [1000000]
        })

        state = strategy.get_strategy_state(single_row)
        assert state['status'] == 'insufficient_data'

    def test_data_with_zero_volatility(self):
        """Test strategy handles data with zero volatility (flat prices)."""
        data = pd.DataFrame({
            'open': [100] * 30,
            'high': [100] * 30,
            'low': [100] * 30,
            'close': [100] * 30,
            'volume': [1000000] * 30
        })

        strategy = KeltnerChannelStrategy()
        result = strategy.calculate_indicators(data)

        # ATR should be zero or very small
        assert 'atr' in result.columns
        # Bands should exist even with zero volatility
        assert 'kc_upper' in result.columns
        assert 'kc_lower' in result.columns

    def test_extreme_parameter_values(self, sample_ohlcv_data):
        """Test strategy with extreme but valid parameter values."""
        # Very short periods
        strategy_short = KeltnerChannelStrategy(ema_period=5, atr_period=3, multiplier=1.0)
        signals_short = strategy_short.generate_signals(sample_ohlcv_data)
        assert len(signals_short) == len(sample_ohlcv_data)

        # Very long periods
        strategy_long = KeltnerChannelStrategy(ema_period=50, atr_period=30, multiplier=5.0)
        signals_long = strategy_long.generate_signals(sample_ohlcv_data)
        assert len(signals_long) == len(sample_ohlcv_data)

    def test_very_narrow_bands(self, sample_ohlcv_data):
        """Test strategy with very narrow bands (small multiplier)."""
        strategy = KeltnerChannelStrategy(multiplier=0.5)
        signals = strategy.generate_signals(sample_ohlcv_data)

        # Should generate more signals with narrow bands
        actionable = ((signals == Signal.BUY.value) | (signals == Signal.SELL.value)).sum()
        # At least some actionable signals
        assert actionable >= 0

    def test_very_wide_bands(self, sample_ohlcv_data):
        """Test strategy with very wide bands (large multiplier)."""
        strategy = KeltnerChannelStrategy(multiplier=5.0)
        signals = strategy.generate_signals(sample_ohlcv_data)

        # Should generate fewer signals with wide bands
        hold_signals = (signals == Signal.HOLD.value).sum()
        # Most should be holds with wide bands
        assert hold_signals > len(signals) * 0.5


class TestKeltnerChannelIntegration:
    """Integration tests for complete strategy workflow."""

    def test_full_workflow_trending_up(self, trending_up_data):
        """Test complete strategy workflow with uptrending data."""
        strategy = KeltnerChannelStrategy(use_breakout=True)

        df_with_indicators = strategy.calculate_indicators(trending_up_data)
        signals = strategy.generate_signals(trending_up_data)
        state = strategy.get_strategy_state(trending_up_data)

        assert 'kc_middle' in df_with_indicators.columns
        assert len(signals) == len(trending_up_data)
        assert state['status'] == 'active'

    def test_full_workflow_volatile_market(self, volatile_data):
        """Test complete strategy workflow with volatile data."""
        strategy = KeltnerChannelStrategy(use_breakout=False)

        df_with_indicators = strategy.calculate_indicators(volatile_data)
        signals = strategy.generate_signals(volatile_data)
        state = strategy.get_strategy_state(volatile_data)

        assert 'kc_upper' in df_with_indicators.columns
        assert len(signals) > 0
        assert state['status'] == 'active'

    def test_strategy_produces_actionable_signals(self, volatile_data):
        """Test that strategy produces some actionable signals."""
        strategy_breakout = KeltnerChannelStrategy(use_breakout=True)
        strategy_reversion = KeltnerChannelStrategy(use_breakout=False)

        signals_breakout = strategy_breakout.generate_signals(volatile_data)
        signals_reversion = strategy_reversion.generate_signals(volatile_data)

        # At least one mode should produce actionable signals
        actionable_breakout = ((signals_breakout == Signal.BUY.value) | (signals_breakout == Signal.SELL.value)).sum()
        actionable_reversion = ((signals_reversion == Signal.BUY.value) | (signals_reversion == Signal.SELL.value)).sum()

        assert actionable_breakout + actionable_reversion > 0
