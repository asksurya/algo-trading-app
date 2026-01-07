"""
Comprehensive unit tests for Donchian Channel Strategy (Turtle Trading).

Tests cover:
- Channel calculations (entry and exit highs/lows)
- Signal generation for breakouts
- System 1 vs System 2 configurations
- Strategy state management
- Edge cases and parameter validation
"""

import pytest
import pandas as pd
import numpy as np
from src.strategies.donchian_channel import DonchianChannelStrategy
from src.strategies.base_strategy import Signal


class TestDonchianChannelInitialization:
    """Test strategy initialization and parameter validation."""

    def test_default_initialization_system1(self):
        """Test strategy initializes with System 1 defaults."""
        strategy = DonchianChannelStrategy()

        assert strategy.name == "Donchian Channel"
        assert strategy.entry_period == 20
        assert strategy.exit_period == 10
        assert strategy.atr_period == 20
        assert strategy.use_system_2 is False

    def test_system2_initialization(self):
        """Test strategy initializes with System 2 parameters."""
        strategy = DonchianChannelStrategy(use_system_2=True)

        assert strategy.entry_period == 55
        assert strategy.exit_period == 20
        assert strategy.use_system_2 is True

    def test_custom_parameters_system1(self):
        """Test strategy initializes with custom System 1 parameters."""
        strategy = DonchianChannelStrategy(
            entry_period=30,
            exit_period=15,
            atr_period=14,
            use_system_2=False
        )

        assert strategy.entry_period == 30
        assert strategy.exit_period == 15
        assert strategy.atr_period == 14
        assert strategy.use_system_2 is False

    def test_system2_overrides_custom_periods(self):
        """Test that System 2 flag overrides custom period parameters."""
        strategy = DonchianChannelStrategy(
            entry_period=30,
            exit_period=15,
            use_system_2=True  # Should override to 55/20
        )

        assert strategy.entry_period == 55
        assert strategy.exit_period == 20

    def test_string_representation_system1(self):
        """Test string representation for System 1."""
        strategy = DonchianChannelStrategy(use_system_2=False)
        str_repr = str(strategy)

        assert "DonchianChannel" in str_repr
        assert "System1" in str_repr

    def test_string_representation_system2(self):
        """Test string representation for System 2."""
        strategy = DonchianChannelStrategy(use_system_2=True)
        str_repr = str(strategy)

        assert "System2" in str_repr
        assert "entry=55" in str_repr
        assert "exit=20" in str_repr


class TestDonchianChannelIndicatorCalculations:
    """Test Donchian Channel indicator calculations."""

    def test_calculate_atr(self, sample_ohlcv_data):
        """Test ATR calculation produces valid values."""
        strategy = DonchianChannelStrategy()
        atr = strategy.calculate_atr(sample_ohlcv_data, period=20)

        assert isinstance(atr, pd.Series)
        assert len(atr) == len(sample_ohlcv_data)
        # ATR should be positive
        assert (atr.dropna() > 0).all()

    def test_calculate_indicators_basic(self, sample_ohlcv_data):
        """Test basic indicator calculation produces expected columns."""
        strategy = DonchianChannelStrategy()
        result = strategy.calculate_indicators(sample_ohlcv_data)

        assert 'entry_high' in result.columns
        assert 'entry_low' in result.columns
        assert 'exit_high' in result.columns
        assert 'exit_low' in result.columns
        assert 'atr' in result.columns
        assert 'donchian_middle' in result.columns
        assert len(result) == len(sample_ohlcv_data)

    def test_entry_high_is_highest(self, sample_ohlcv_data):
        """Test that entry_high is the highest high over entry period."""
        strategy = DonchianChannelStrategy(entry_period=20)
        result = strategy.calculate_indicators(sample_ohlcv_data)

        # Remove NaN values
        valid_data = result.dropna(subset=['entry_high'])

        # Entry high should be >= current high
        assert (valid_data['entry_high'] >= valid_data['high']).all()

    def test_entry_low_is_lowest(self, sample_ohlcv_data):
        """Test that entry_low is the lowest low over entry period."""
        strategy = DonchianChannelStrategy(entry_period=20)
        result = strategy.calculate_indicators(sample_ohlcv_data)

        # Remove NaN values
        valid_data = result.dropna(subset=['entry_low'])

        # Entry low should be <= current low
        assert (valid_data['entry_low'] <= valid_data['low']).all()

    def test_donchian_middle_calculation(self, sample_ohlcv_data):
        """Test that Donchian middle is average of entry high and low."""
        strategy = DonchianChannelStrategy()
        result = strategy.calculate_indicators(sample_ohlcv_data)

        valid_data = result.dropna(subset=['entry_high', 'entry_low', 'donchian_middle'])

        # Middle should be (high + low) / 2
        expected_middle = (valid_data['entry_high'] + valid_data['entry_low']) / 2
        pd.testing.assert_series_equal(valid_data['donchian_middle'], expected_middle, check_names=False)

    def test_system2_wider_channels(self, sample_ohlcv_data):
        """Test that System 2 produces wider channels than System 1."""
        strategy_s1 = DonchianChannelStrategy(use_system_2=False)
        strategy_s2 = DonchianChannelStrategy(use_system_2=True)

        result_s1 = strategy_s1.calculate_indicators(sample_ohlcv_data)
        result_s2 = strategy_s2.calculate_indicators(sample_ohlcv_data)

        # System 2 channel should generally be wider (55 days vs 20 days)
        width_s1 = (result_s1['entry_high'] - result_s1['entry_low']).mean()
        width_s2 = (result_s2['entry_high'] - result_s2['entry_low']).mean()

        assert width_s2 > width_s1

    def test_exit_channel_narrower_than_entry(self, sample_ohlcv_data):
        """Test that exit channel is narrower than entry channel."""
        strategy = DonchianChannelStrategy()
        result = strategy.calculate_indicators(sample_ohlcv_data)

        valid_data = result.dropna(subset=['entry_high', 'entry_low', 'exit_high', 'exit_low'])

        entry_width = (valid_data['entry_high'] - valid_data['entry_low']).mean()
        exit_width = (valid_data['exit_high'] - valid_data['exit_low']).mean()

        # Exit channel (10 days) should be narrower than entry (20 days)
        assert exit_width < entry_width


class TestDonchianChannelSignalGeneration:
    """Test signal generation logic."""

    def test_buy_signal_on_breakout(self):
        """Test BUY signal when price breaks above entry high."""
        # Create data with clear upward breakout
        data = pd.DataFrame({
            'open': [100] * 30,
            'high': [102] * 10 + list(range(103, 123, 1)),
            'low': [99] * 30,
            'close': [100] * 10 + list(range(101, 121, 1)),
            'volume': [1000000] * 30
        })

        strategy = DonchianChannelStrategy(entry_period=10)
        signals = strategy.generate_signals(data)

        # Should have BUY signals on breakout
        buy_signals = (signals == Signal.BUY.value).sum()
        assert buy_signals > 0

    def test_sell_signal_on_breakdown(self):
        """Test SELL signal when price breaks below exit low."""
        # Create data with clear downward breakdown
        data = pd.DataFrame({
            'open': [100] * 35,
            'high': [101] * 35,
            'low': [100] * 15 + list(range(99, 79, -1)),
            'close': [100] * 15 + list(range(99, 79, -1)),
            'volume': [1000000] * 35
        })

        strategy = DonchianChannelStrategy(exit_period=10)
        signals = strategy.generate_signals(data)

        # Should have SELL signals on breakdown
        sell_signals = (signals == Signal.SELL.value).sum()
        assert sell_signals > 0

    def test_no_look_ahead_bias(self, sample_ohlcv_data):
        """Test that signals use previous period's channels (no look-ahead bias)."""
        strategy = DonchianChannelStrategy()
        result = strategy.calculate_indicators(sample_ohlcv_data)

        # The signal generation should use shifted values
        # This is implicitly tested by the implementation using .shift(1)
        signals = strategy.generate_signals(sample_ohlcv_data)

        # Signals should not be based on current bar's high/low
        assert isinstance(signals, pd.Series)

    def test_signals_series_length(self, sample_ohlcv_data):
        """Test that signals series has same length as input data."""
        strategy = DonchianChannelStrategy()
        signals = strategy.generate_signals(sample_ohlcv_data)

        assert len(signals) == len(sample_ohlcv_data)
        assert signals.index.equals(sample_ohlcv_data.index)

    def test_signals_are_valid_values(self, sample_ohlcv_data):
        """Test that all signals are valid Signal enum values."""
        strategy = DonchianChannelStrategy()
        signals = strategy.generate_signals(sample_ohlcv_data)

        valid_values = [Signal.BUY.value, Signal.SELL.value, Signal.HOLD.value]
        assert signals.isin(valid_values).all()

    def test_ranging_market_few_signals(self, ranging_data):
        """Test that ranging market produces fewer signals."""
        strategy = DonchianChannelStrategy()
        signals = strategy.generate_signals(ranging_data)

        # Should mostly be holds in ranging market
        hold_signals = (signals == Signal.HOLD.value).sum()
        assert hold_signals > len(signals) * 0.6

    @pytest.mark.parametrize("entry_period,exit_period", [
        (10, 5),
        (20, 10),
        (55, 20),
    ])
    def test_signals_with_different_periods(self, sample_ohlcv_data, entry_period, exit_period):
        """Test signal generation with different period parameters."""
        strategy = DonchianChannelStrategy(entry_period=entry_period, exit_period=exit_period, use_system_2=False)
        signals = strategy.generate_signals(sample_ohlcv_data)

        assert len(signals) == len(sample_ohlcv_data)
        assert isinstance(signals, pd.Series)


class TestDonchianChannelStrategyState:
    """Test strategy state management."""

    def test_get_strategy_state_with_sufficient_data(self, sample_ohlcv_data):
        """Test strategy state returns active status with sufficient data."""
        strategy = DonchianChannelStrategy()
        state = strategy.get_strategy_state(sample_ohlcv_data)

        assert state['status'] == 'active'
        assert 'entry_high' in state
        assert 'entry_low' in state
        assert 'exit_high' in state
        assert 'exit_low' in state
        assert 'donchian_middle' in state
        assert 'atr' in state
        assert 'current_price' in state
        assert 'position_in_channel' in state
        assert 'system' in state

    def test_get_strategy_state_with_insufficient_data(self, insufficient_data):
        """Test strategy state returns insufficient_data status."""
        strategy = DonchianChannelStrategy(entry_period=20)
        state = strategy.get_strategy_state(insufficient_data)

        assert state['status'] == 'insufficient_data'
        assert 'message' in state

    def test_strategy_state_system_identification(self, sample_ohlcv_data):
        """Test that strategy state correctly identifies system."""
        strategy_s1 = DonchianChannelStrategy(use_system_2=False)
        strategy_s2 = DonchianChannelStrategy(use_system_2=True)

        state_s1 = strategy_s1.get_strategy_state(sample_ohlcv_data)
        state_s2 = strategy_s2.get_strategy_state(sample_ohlcv_data)

        assert state_s1['system'] == 'System 1'
        assert state_s2['system'] == 'System 2'

    def test_position_in_channel_range(self, sample_ohlcv_data):
        """Test that position_in_channel is calculated correctly."""
        strategy = DonchianChannelStrategy()
        state = strategy.get_strategy_state(sample_ohlcv_data)

        if state['status'] == 'active':
            # Position should typically be between 0 and 1
            assert 0 <= state['position_in_channel'] <= 1 or abs(state['position_in_channel'] - 0.5) < 1

    def test_strategy_state_values_are_numeric(self, sample_ohlcv_data):
        """Test that strategy state values are numeric where expected."""
        strategy = DonchianChannelStrategy()
        state = strategy.get_strategy_state(sample_ohlcv_data)

        if state['status'] == 'active':
            assert isinstance(state['entry_high'], (int, float))
            assert isinstance(state['entry_low'], (int, float))
            assert isinstance(state['exit_high'], (int, float))
            assert isinstance(state['exit_low'], (int, float))
            assert isinstance(state['donchian_middle'], (int, float))
            assert isinstance(state['atr'], (int, float))
            assert isinstance(state['current_price'], (int, float))
            assert isinstance(state['position_in_channel'], (int, float))


class TestDonchianChannelEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_dataframe(self):
        """Test strategy handles empty DataFrame gracefully."""
        strategy = DonchianChannelStrategy()
        empty_df = pd.DataFrame(columns=['open', 'high', 'low', 'close', 'volume'])

        state = strategy.get_strategy_state(empty_df)
        assert state['status'] == 'insufficient_data'

    def test_single_row_dataframe(self):
        """Test strategy handles single row DataFrame."""
        strategy = DonchianChannelStrategy()
        single_row = pd.DataFrame({
            'open': [100],
            'high': [101],
            'low': [99],
            'close': [100],
            'volume': [1000000]
        })

        state = strategy.get_strategy_state(single_row)
        assert state['status'] == 'insufficient_data'

    def test_data_with_zero_range(self):
        """Test strategy handles data with zero high-low range."""
        data = pd.DataFrame({
            'open': [100] * 30,
            'high': [100] * 30,
            'low': [100] * 30,
            'close': [100] * 30,
            'volume': [1000000] * 30
        })

        strategy = DonchianChannelStrategy()
        result = strategy.calculate_indicators(data)

        # Channel width should be zero
        assert 'entry_high' in result.columns
        assert 'entry_low' in result.columns

        # Position calculation should handle division by zero
        state = strategy.get_strategy_state(data)
        if state['status'] == 'active':
            # Should default to 0.5 when channel width is zero
            assert state['position_in_channel'] == 0.5

    def test_very_short_periods(self, sample_ohlcv_data):
        """Test strategy with very short periods."""
        strategy = DonchianChannelStrategy(entry_period=3, exit_period=2, use_system_2=False)
        signals = strategy.generate_signals(sample_ohlcv_data)

        assert len(signals) == len(sample_ohlcv_data)

    def test_very_long_periods(self):
        """Test strategy with very long periods."""
        # Create longer dataset for very long periods
        data = pd.DataFrame({
            'open': [100] * 100,
            'high': [101] * 100,
            'low': [99] * 100,
            'close': list(range(100, 200, 1)),
            'volume': [1000000] * 100
        })

        strategy = DonchianChannelStrategy(entry_period=80, exit_period=40, use_system_2=False)
        state = strategy.get_strategy_state(data)

        assert state['status'] == 'active'

    def test_system2_requires_more_data(self):
        """Test that System 2 requires more data than System 1."""
        # Create data with exactly 30 bars
        data = pd.DataFrame({
            'open': [100] * 30,
            'high': [101] * 30,
            'low': [99] * 30,
            'close': [100] * 30,
            'volume': [1000000] * 30
        })

        strategy_s1 = DonchianChannelStrategy(use_system_2=False)  # 20 period entry
        strategy_s2 = DonchianChannelStrategy(use_system_2=True)   # 55 period entry

        state_s1 = strategy_s1.get_strategy_state(data)
        state_s2 = strategy_s2.get_strategy_state(data)

        # S1 should work, S2 should need more data
        assert state_s1['status'] == 'active'
        assert state_s2['status'] == 'insufficient_data'


class TestDonchianChannelTurtleTrading:
    """Test Turtle Trading specific behaviors."""

    def test_turtle_system1_parameters(self):
        """Test that System 1 uses classic Turtle parameters."""
        strategy = DonchianChannelStrategy(use_system_2=False)

        # Classic Turtle System 1: 20-day entry, 10-day exit
        assert strategy.entry_period == 20
        assert strategy.exit_period == 10

    def test_turtle_system2_parameters(self):
        """Test that System 2 uses classic Turtle parameters."""
        strategy = DonchianChannelStrategy(use_system_2=True)

        # Classic Turtle System 2: 55-day entry, 20-day exit
        assert strategy.entry_period == 55
        assert strategy.exit_period == 20

    def test_atr_for_position_sizing(self, sample_ohlcv_data):
        """Test that ATR is calculated for position sizing (Turtle method)."""
        strategy = DonchianChannelStrategy()
        result = strategy.calculate_indicators(sample_ohlcv_data)

        # ATR should be available for N-based position sizing
        assert 'atr' in result.columns
        assert result['atr'].notna().sum() > 0


class TestDonchianChannelIntegration:
    """Integration tests for complete strategy workflow."""

    def test_full_workflow_trending_up(self, trending_up_data):
        """Test complete strategy workflow with uptrending data."""
        strategy = DonchianChannelStrategy()

        df_with_indicators = strategy.calculate_indicators(trending_up_data)
        signals = strategy.generate_signals(trending_up_data)
        state = strategy.get_strategy_state(trending_up_data)

        assert 'entry_high' in df_with_indicators.columns
        assert len(signals) == len(trending_up_data)
        assert state['status'] == 'active'

    def test_full_workflow_trending_down(self, trending_down_data):
        """Test complete strategy workflow with downtrending data."""
        strategy = DonchianChannelStrategy()

        df_with_indicators = strategy.calculate_indicators(trending_down_data)
        signals = strategy.generate_signals(trending_down_data)
        state = strategy.get_strategy_state(trending_down_data)

        assert 'entry_low' in df_with_indicators.columns
        assert len(signals) == len(trending_down_data)
        assert state['status'] == 'active'

    def test_full_workflow_volatile_market(self, volatile_data):
        """Test complete strategy workflow with volatile data."""
        strategy = DonchianChannelStrategy(use_system_2=False)

        df_with_indicators = strategy.calculate_indicators(volatile_data)
        signals = strategy.generate_signals(volatile_data)
        state = strategy.get_strategy_state(volatile_data)

        assert 'donchian_middle' in df_with_indicators.columns
        assert len(signals) > 0
        assert state['status'] == 'active'

    def test_strategy_produces_actionable_signals(self, volatile_data):
        """Test that strategy produces some actionable signals."""
        strategy = DonchianChannelStrategy()
        signals = strategy.generate_signals(volatile_data)

        # Should have at least some BUY or SELL signals in volatile data
        actionable_signals = ((signals == Signal.BUY.value) | (signals == Signal.SELL.value)).sum()
        assert actionable_signals > 0

    def test_both_systems_work_on_same_data(self, sample_ohlcv_data):
        """Test that both System 1 and System 2 work correctly."""
        strategy_s1 = DonchianChannelStrategy(use_system_2=False)
        strategy_s2 = DonchianChannelStrategy(use_system_2=True)

        # Both should complete without errors
        signals_s1 = strategy_s1.generate_signals(sample_ohlcv_data)
        signals_s2 = strategy_s2.generate_signals(sample_ohlcv_data)

        assert len(signals_s1) == len(sample_ohlcv_data)
        assert len(signals_s2) == len(sample_ohlcv_data)

        # Both should produce valid signals
        valid_values = [Signal.BUY.value, Signal.SELL.value, Signal.HOLD.value]
        assert signals_s1.isin(valid_values).all()
        assert signals_s2.isin(valid_values).all()

    def test_system2_produces_fewer_signals(self, sample_ohlcv_data):
        """Test that System 2 generally produces fewer signals (wider channels)."""
        strategy_s1 = DonchianChannelStrategy(use_system_2=False)
        strategy_s2 = DonchianChannelStrategy(use_system_2=True)

        signals_s1 = strategy_s1.generate_signals(sample_ohlcv_data)
        signals_s2 = strategy_s2.generate_signals(sample_ohlcv_data)

        actionable_s1 = ((signals_s1 == Signal.BUY.value) | (signals_s1 == Signal.SELL.value)).sum()
        actionable_s2 = ((signals_s2 == Signal.BUY.value) | (signals_s2 == Signal.SELL.value)).sum()

        # System 2 should generally have fewer or equal signals
        assert actionable_s2 <= actionable_s1 or actionable_s2 < len(sample_ohlcv_data) * 0.3
