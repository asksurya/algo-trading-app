"""
Comprehensive unit tests for ATR Trailing Stop Strategy.

Tests cover:
- ATR and EMA calculations
- Trailing stop calculations (Chandelier and Simple modes)
- Signal generation logic
- Strategy state management
- Edge cases and mode switching
"""

import pytest
import pandas as pd
import numpy as np
from src.strategies.atr_trailing_stop import ATRTrailingStopStrategy
from src.strategies.base_strategy import Signal


class TestATRTrailingStopInitialization:
    """Test strategy initialization and parameter validation."""

    def test_default_initialization(self):
        """Test strategy initializes with default parameters."""
        strategy = ATRTrailingStopStrategy()

        assert strategy.name == "ATR Trailing Stop"
        assert strategy.atr_period == 14
        assert strategy.atr_multiplier == 3.0
        assert strategy.trend_period == 50
        assert strategy.use_chandelier is True

    def test_custom_parameters(self):
        """Test strategy initializes with custom parameters."""
        strategy = ATRTrailingStopStrategy(
            atr_period=20,
            atr_multiplier=2.5,
            trend_period=100,
            use_chandelier=False
        )

        assert strategy.atr_period == 20
        assert strategy.atr_multiplier == 2.5
        assert strategy.trend_period == 100
        assert strategy.use_chandelier is False

    def test_string_representation_chandelier_mode(self):
        """Test string representation in Chandelier mode."""
        strategy = ATRTrailingStopStrategy(use_chandelier=True)
        str_repr = str(strategy)

        assert "ATRTrailingStop" in str_repr
        assert "mode=chandelier" in str_repr

    def test_string_representation_simple_mode(self):
        """Test string representation in simple mode."""
        strategy = ATRTrailingStopStrategy(use_chandelier=False)
        str_repr = str(strategy)

        assert "mode=simple" in str_repr


class TestATRTrailingStopIndicatorCalculations:
    """Test ATR and trailing stop indicator calculations."""

    def test_calculate_atr(self, sample_ohlcv_data):
        """Test ATR calculation produces valid values."""
        strategy = ATRTrailingStopStrategy()
        atr = strategy.calculate_atr(sample_ohlcv_data, period=14)

        assert isinstance(atr, pd.Series)
        assert len(atr) == len(sample_ohlcv_data)
        # ATR should be positive
        assert (atr.dropna() > 0).all()

    def test_calculate_ema(self, sample_ohlcv_data):
        """Test EMA calculation produces valid values."""
        strategy = ATRTrailingStopStrategy()
        ema = strategy.calculate_ema(sample_ohlcv_data['close'], period=50)

        assert isinstance(ema, pd.Series)
        assert len(ema) == len(sample_ohlcv_data)
        assert ema.notna().sum() > 0

    def test_calculate_indicators_chandelier_mode(self, sample_ohlcv_data):
        """Test indicator calculation in Chandelier mode."""
        strategy = ATRTrailingStopStrategy(use_chandelier=True)
        result = strategy.calculate_indicators(sample_ohlcv_data)

        assert 'atr' in result.columns
        assert 'trend_ema' in result.columns
        assert 'highest_high' in result.columns
        assert 'lowest_low' in result.columns
        assert 'trailing_stop_long' in result.columns
        assert 'trailing_stop_short' in result.columns
        assert 'trend_up' in result.columns

    def test_calculate_indicators_simple_mode(self, sample_ohlcv_data):
        """Test indicator calculation in simple mode."""
        strategy = ATRTrailingStopStrategy(use_chandelier=False)
        result = strategy.calculate_indicators(sample_ohlcv_data)

        assert 'atr' in result.columns
        assert 'trend_ema' in result.columns
        assert 'trailing_stop_long' in result.columns
        assert 'trailing_stop_short' in result.columns
        # Chandelier-specific columns should not exist
        assert 'highest_high' not in result.columns
        assert 'lowest_low' not in result.columns

    def test_trailing_stop_below_price(self, trending_up_data):
        """Test that long trailing stop is below price in uptrend."""
        strategy = ATRTrailingStopStrategy()
        result = strategy.calculate_indicators(trending_up_data)

        # Remove NaN values
        valid_data = result.dropna(subset=['trailing_stop_long', 'close'])

        # Trailing stop for longs should be below price
        assert (valid_data['trailing_stop_long'] < valid_data['close']).sum() > len(valid_data) * 0.7

    def test_trailing_stop_above_price(self, trending_down_data):
        """Test that short trailing stop is above price in downtrend."""
        strategy = ATRTrailingStopStrategy()
        result = strategy.calculate_indicators(trending_down_data)

        # Remove NaN values
        valid_data = result.dropna(subset=['trailing_stop_short', 'close'])

        # Trailing stop for shorts should be above price
        assert (valid_data['trailing_stop_short'] > valid_data['close']).sum() > len(valid_data) * 0.7

    def test_atr_multiplier_affects_stop_distance(self, sample_ohlcv_data):
        """Test that ATR multiplier affects stop distance."""
        strategy_tight = ATRTrailingStopStrategy(atr_multiplier=1.0)
        strategy_wide = ATRTrailingStopStrategy(atr_multiplier=5.0)

        result_tight = strategy_tight.calculate_indicators(sample_ohlcv_data)
        result_wide = strategy_wide.calculate_indicators(sample_ohlcv_data)

        # Calculate average distance from close to stop
        distance_tight = (result_tight['close'] - result_tight['trailing_stop_long']).abs().mean()
        distance_wide = (result_wide['close'] - result_wide['trailing_stop_long']).abs().mean()

        assert distance_wide > distance_tight

    def test_chandelier_uses_highest_high(self, sample_ohlcv_data):
        """Test that Chandelier mode uses highest high for stop calculation."""
        strategy = ATRTrailingStopStrategy(use_chandelier=True, atr_period=14)
        result = strategy.calculate_indicators(sample_ohlcv_data)

        valid_data = result.dropna(subset=['highest_high', 'high'])

        # Highest high should be >= current high
        assert (valid_data['highest_high'] >= valid_data['high']).all()


class TestATRTrailingStopSignalGeneration:
    """Test signal generation logic."""

    def test_buy_signal_on_trend_cross(self):
        """Test BUY signal when price crosses above trend EMA."""
        # Create data with clear upward cross
        data = pd.DataFrame({
            'open': [100] * 60,
            'high': [101] * 60,
            'low': [99] * 60,
            'close': [100] * 30 + list(range(100, 130, 1)),
            'volume': [1000000] * 60
        })

        strategy = ATRTrailingStopStrategy(trend_period=20)
        signals = strategy.generate_signals(data)

        # Should have BUY signals
        buy_signals = (signals == Signal.BUY.value).sum()
        assert buy_signals > 0

    def test_sell_signal_on_stop_cross(self):
        """Test SELL signal when price crosses below trailing stop."""
        # Create data with uptrend then breakdown
        data = pd.DataFrame({
            'open': [100] * 70,
            'high': [101] * 70,
            'low': [99] * 70,
            'close': list(range(100, 130, 1)) + [130] * 10 + list(range(130, 110, -1)),
            'volume': [1000000] * 70
        })

        strategy = ATRTrailingStopStrategy(trend_period=20, atr_multiplier=2.0)
        signals = strategy.generate_signals(data)

        # Should have SELL signals when price drops
        sell_signals = (signals == Signal.SELL.value).sum()
        assert sell_signals > 0

    def test_signals_series_length(self, sample_ohlcv_data):
        """Test that signals series has same length as input data."""
        strategy = ATRTrailingStopStrategy()
        signals = strategy.generate_signals(sample_ohlcv_data)

        assert len(signals) == len(sample_ohlcv_data)
        assert signals.index.equals(sample_ohlcv_data.index)

    def test_signals_are_valid_values(self, sample_ohlcv_data):
        """Test that all signals are valid Signal enum values."""
        strategy = ATRTrailingStopStrategy()
        signals = strategy.generate_signals(sample_ohlcv_data)

        valid_values = [Signal.BUY.value, Signal.SELL.value, Signal.HOLD.value]
        assert signals.isin(valid_values).all()

    def test_no_signals_in_ranging_market(self, ranging_data):
        """Test minimal signals in ranging/sideways market."""
        strategy = ATRTrailingStopStrategy()
        signals = strategy.generate_signals(ranging_data)

        # Should mostly be holds in ranging market
        hold_signals = (signals == Signal.HOLD.value).sum()
        assert hold_signals > len(signals) * 0.5

    @pytest.mark.parametrize("atr_period,trend_period", [
        (10, 20),
        (14, 50),
        (20, 100),
    ])
    def test_signals_with_different_periods(self, sample_ohlcv_data, atr_period, trend_period):
        """Test signal generation with different period parameters."""
        strategy = ATRTrailingStopStrategy(atr_period=atr_period, trend_period=trend_period)
        signals = strategy.generate_signals(sample_ohlcv_data)

        assert len(signals) == len(sample_ohlcv_data)
        assert isinstance(signals, pd.Series)


class TestATRTrailingStopStrategyState:
    """Test strategy state management."""

    def test_get_strategy_state_with_sufficient_data(self, sample_ohlcv_data):
        """Test strategy state returns active status with sufficient data."""
        strategy = ATRTrailingStopStrategy()
        state = strategy.get_strategy_state(sample_ohlcv_data)

        assert state['status'] == 'active'
        assert 'atr' in state
        assert 'trend_ema' in state
        assert 'trailing_stop_long' in state
        assert 'trailing_stop_short' in state
        assert 'current_price' in state
        assert 'trend' in state
        assert 'atr_multiplier' in state
        assert 'use_chandelier' in state

    def test_get_strategy_state_with_insufficient_data(self, insufficient_data):
        """Test strategy state returns insufficient_data status."""
        strategy = ATRTrailingStopStrategy(atr_period=14, trend_period=50)
        state = strategy.get_strategy_state(insufficient_data)

        assert state['status'] == 'insufficient_data'
        assert 'message' in state

    def test_strategy_state_bullish_trend(self, trending_up_data):
        """Test strategy state identifies bullish trend."""
        strategy = ATRTrailingStopStrategy(trend_period=20)
        state = strategy.get_strategy_state(trending_up_data)

        assert state['status'] == 'active'
        assert state['trend'] == 'bullish'

    def test_strategy_state_bearish_trend(self, trending_down_data):
        """Test strategy state identifies bearish trend."""
        strategy = ATRTrailingStopStrategy(trend_period=20)
        state = strategy.get_strategy_state(trending_down_data)

        assert state['status'] == 'active'
        assert state['trend'] == 'bearish'

    def test_strategy_state_chandelier_flag(self, sample_ohlcv_data):
        """Test that strategy state reports correct Chandelier mode."""
        strategy_chandelier = ATRTrailingStopStrategy(use_chandelier=True)
        strategy_simple = ATRTrailingStopStrategy(use_chandelier=False)

        state_chandelier = strategy_chandelier.get_strategy_state(sample_ohlcv_data)
        state_simple = strategy_simple.get_strategy_state(sample_ohlcv_data)

        assert state_chandelier['use_chandelier'] is True
        assert state_simple['use_chandelier'] is False

    def test_strategy_state_values_are_numeric(self, sample_ohlcv_data):
        """Test that strategy state values are numeric where expected."""
        strategy = ATRTrailingStopStrategy()
        state = strategy.get_strategy_state(sample_ohlcv_data)

        if state['status'] == 'active':
            assert isinstance(state['atr'], (int, float))
            assert isinstance(state['trend_ema'], (int, float))
            assert isinstance(state['trailing_stop_long'], (int, float))
            assert isinstance(state['trailing_stop_short'], (int, float))
            assert isinstance(state['current_price'], (int, float))
            assert isinstance(state['atr_multiplier'], (int, float))


class TestATRTrailingStopEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_dataframe(self):
        """Test strategy handles empty DataFrame gracefully."""
        strategy = ATRTrailingStopStrategy()
        empty_df = pd.DataFrame(columns=['open', 'high', 'low', 'close', 'volume'])

        state = strategy.get_strategy_state(empty_df)
        assert state['status'] == 'insufficient_data'

    def test_single_row_dataframe(self):
        """Test strategy handles single row DataFrame."""
        strategy = ATRTrailingStopStrategy()
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
        """Test strategy handles data with zero volatility."""
        data = pd.DataFrame({
            'open': [100] * 60,
            'high': [100] * 60,
            'low': [100] * 60,
            'close': [100] * 60,
            'volume': [1000000] * 60
        })

        strategy = ATRTrailingStopStrategy()
        result = strategy.calculate_indicators(data)

        # ATR should be zero or very small
        assert 'atr' in result.columns
        # Stops should still exist
        assert 'trailing_stop_long' in result.columns

    def test_extreme_atr_multiplier(self, sample_ohlcv_data):
        """Test strategy with extreme ATR multiplier values."""
        # Very tight stop
        strategy_tight = ATRTrailingStopStrategy(atr_multiplier=0.5)
        signals_tight = strategy_tight.generate_signals(sample_ohlcv_data)
        assert len(signals_tight) == len(sample_ohlcv_data)

        # Very wide stop
        strategy_wide = ATRTrailingStopStrategy(atr_multiplier=10.0)
        signals_wide = strategy_wide.generate_signals(sample_ohlcv_data)
        assert len(signals_wide) == len(sample_ohlcv_data)

    def test_very_short_periods(self, sample_ohlcv_data):
        """Test strategy with very short periods."""
        strategy = ATRTrailingStopStrategy(atr_period=3, trend_period=5)
        signals = strategy.generate_signals(sample_ohlcv_data)

        assert len(signals) == len(sample_ohlcv_data)

    def test_very_long_periods(self, sample_ohlcv_data):
        """Test strategy with very long periods."""
        strategy = ATRTrailingStopStrategy(atr_period=50, trend_period=90)

        # May not have enough data for very long periods
        state = strategy.get_strategy_state(sample_ohlcv_data)
        # Either active or insufficient data is acceptable
        assert state['status'] in ['active', 'insufficient_data']

    def test_chandelier_vs_simple_different_stops(self, sample_ohlcv_data):
        """Test that Chandelier and Simple modes produce different stops."""
        strategy_chandelier = ATRTrailingStopStrategy(use_chandelier=True)
        strategy_simple = ATRTrailingStopStrategy(use_chandelier=False)

        result_chandelier = strategy_chandelier.calculate_indicators(sample_ohlcv_data)
        result_simple = strategy_simple.calculate_indicators(sample_ohlcv_data)

        # Stops should be different between modes
        assert not result_chandelier['trailing_stop_long'].equals(result_simple['trailing_stop_long'])


class TestATRTrailingStopIntegration:
    """Integration tests for complete strategy workflow."""

    def test_full_workflow_trending_up(self, trending_up_data):
        """Test complete strategy workflow with uptrending data."""
        strategy = ATRTrailingStopStrategy()

        df_with_indicators = strategy.calculate_indicators(trending_up_data)
        signals = strategy.generate_signals(trending_up_data)
        state = strategy.get_strategy_state(trending_up_data)

        assert 'atr' in df_with_indicators.columns
        assert len(signals) == len(trending_up_data)
        assert state['status'] == 'active'
        assert state['trend'] == 'bullish'

    def test_full_workflow_trending_down(self, trending_down_data):
        """Test complete strategy workflow with downtrending data."""
        strategy = ATRTrailingStopStrategy()

        df_with_indicators = strategy.calculate_indicators(trending_down_data)
        signals = strategy.generate_signals(trending_down_data)
        state = strategy.get_strategy_state(trending_down_data)

        assert 'trailing_stop_long' in df_with_indicators.columns
        assert len(signals) == len(trending_down_data)
        assert state['status'] == 'active'
        assert state['trend'] == 'bearish'

    def test_full_workflow_volatile_market(self, volatile_data):
        """Test complete strategy workflow with volatile data."""
        strategy = ATRTrailingStopStrategy(atr_multiplier=2.5)

        df_with_indicators = strategy.calculate_indicators(volatile_data)
        signals = strategy.generate_signals(volatile_data)
        state = strategy.get_strategy_state(volatile_data)

        assert 'atr' in df_with_indicators.columns
        assert len(signals) > 0
        assert state['status'] == 'active'

    def test_strategy_produces_actionable_signals(self, volatile_data):
        """Test that strategy produces some actionable signals in volatile market."""
        strategy = ATRTrailingStopStrategy()
        signals = strategy.generate_signals(volatile_data)

        # Should have at least some BUY or SELL signals
        actionable_signals = ((signals == Signal.BUY.value) | (signals == Signal.SELL.value)).sum()
        assert actionable_signals > 0

    def test_both_modes_work_on_same_data(self, sample_ohlcv_data):
        """Test that both Chandelier and Simple modes work correctly."""
        strategy_chandelier = ATRTrailingStopStrategy(use_chandelier=True)
        strategy_simple = ATRTrailingStopStrategy(use_chandelier=False)

        # Both should complete without errors
        signals_chandelier = strategy_chandelier.generate_signals(sample_ohlcv_data)
        signals_simple = strategy_simple.generate_signals(sample_ohlcv_data)

        assert len(signals_chandelier) == len(sample_ohlcv_data)
        assert len(signals_simple) == len(sample_ohlcv_data)

        # Both should produce valid signals
        valid_values = [Signal.BUY.value, Signal.SELL.value, Signal.HOLD.value]
        assert signals_chandelier.isin(valid_values).all()
        assert signals_simple.isin(valid_values).all()
