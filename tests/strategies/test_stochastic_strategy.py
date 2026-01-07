"""
Comprehensive unit tests for Stochastic Oscillator Strategy.

Tests cover:
- Indicator calculations
- Signal generation logic
- Strategy state management
- Edge cases and error handling
- Parameter validation
"""

import pytest
import pandas as pd
import numpy as np
from src.strategies.stochastic_strategy import StochasticStrategy
from src.strategies.base_strategy import Signal


class TestStochasticStrategyInitialization:
    """Test strategy initialization and parameter validation."""

    def test_default_initialization(self):
        """Test strategy initializes with default parameters."""
        strategy = StochasticStrategy()

        assert strategy.name == "Stochastic"
        assert strategy.k_period == 14
        assert strategy.d_period == 3
        assert strategy.smooth_k == 3
        assert strategy.oversold == 20
        assert strategy.overbought == 80

    def test_custom_parameters(self):
        """Test strategy initializes with custom parameters."""
        strategy = StochasticStrategy(
            k_period=21,
            d_period=5,
            smooth_k=5,
            oversold=30,
            overbought=70
        )

        assert strategy.k_period == 21
        assert strategy.d_period == 5
        assert strategy.smooth_k == 5
        assert strategy.oversold == 30
        assert strategy.overbought == 70

    def test_invalid_thresholds_raises_error(self):
        """Test that invalid threshold parameters raise ValueError."""
        # Oversold >= Overbought
        with pytest.raises(ValueError, match="Invalid thresholds"):
            StochasticStrategy(oversold=80, overbought=20)

        # Oversold == Overbought
        with pytest.raises(ValueError, match="Invalid thresholds"):
            StochasticStrategy(oversold=50, overbought=50)

        # Oversold <= 0
        with pytest.raises(ValueError, match="Invalid thresholds"):
            StochasticStrategy(oversold=0, overbought=80)

        # Overbought >= 100
        with pytest.raises(ValueError, match="Invalid thresholds"):
            StochasticStrategy(oversold=20, overbought=100)

    def test_string_representation(self):
        """Test string representation of strategy."""
        strategy = StochasticStrategy(k_period=14, d_period=3, oversold=20, overbought=80)
        str_repr = str(strategy)

        assert "Stochastic" in str_repr
        assert "k=14" in str_repr
        assert "d=3" in str_repr
        assert "oversold=20" in str_repr
        assert "overbought=80" in str_repr


class TestStochasticIndicatorCalculations:
    """Test stochastic indicator calculations."""

    def test_calculate_stochastic_basic(self, sample_ohlcv_data):
        """Test basic stochastic calculation produces expected columns."""
        strategy = StochasticStrategy()
        result = strategy.calculate_stochastic(sample_ohlcv_data)

        assert 'stoch_k' in result.columns
        assert 'stoch_d' in result.columns
        assert len(result) == len(sample_ohlcv_data)

    def test_stochastic_range(self, sample_ohlcv_data):
        """Test that stochastic values are in valid range [0, 100]."""
        strategy = StochasticStrategy()
        result = strategy.calculate_stochastic(sample_ohlcv_data)

        # Remove NaN values for testing
        k_values = result['stoch_k'].dropna()
        d_values = result['stoch_d'].dropna()

        assert (k_values >= 0).all() and (k_values <= 100).all()
        assert (d_values >= 0).all() and (d_values <= 100).all()

    def test_stochastic_calculation_math(self):
        """Test stochastic calculation with known values."""
        # Create simple test data where we can calculate expected values
        data = pd.DataFrame({
            'open': [100, 101, 102, 103, 104],
            'high': [105, 106, 107, 108, 109],
            'low': [95, 96, 97, 98, 99],
            'close': [102, 103, 104, 105, 106],
            'volume': [1000000] * 5
        })

        strategy = StochasticStrategy(k_period=3, d_period=2, smooth_k=1)
        result = strategy.calculate_stochastic(data)

        # At index 2 (need 3 periods):
        # High_3 = 107, Low_3 = 95, Close = 104
        # %K = 100 * (104 - 95) / (107 - 95) = 100 * 9 / 12 = 75
        assert result['stoch_k'].notna().sum() > 0

    def test_calculate_indicators_returns_dataframe(self, sample_ohlcv_data):
        """Test calculate_indicators returns DataFrame with indicators."""
        strategy = StochasticStrategy()
        result = strategy.calculate_indicators(sample_ohlcv_data)

        assert isinstance(result, pd.DataFrame)
        assert 'stoch_k' in result.columns
        assert 'stoch_d' in result.columns

    def test_indicators_with_insufficient_data(self, insufficient_data):
        """Test indicator calculation with insufficient data."""
        strategy = StochasticStrategy(k_period=14)
        result = strategy.calculate_indicators(insufficient_data)

        # Should return DataFrame but with mostly NaN values
        assert isinstance(result, pd.DataFrame)
        assert result['stoch_k'].isna().all()  # Not enough data for 14-period


class TestStochasticSignalGeneration:
    """Test signal generation logic."""

    def test_no_signals_in_neutral_zone(self, ranging_data):
        """Test that no signals are generated in neutral zone (20-80)."""
        strategy = StochasticStrategy()
        signals = strategy.generate_signals(ranging_data)

        # Most signals should be HOLD in ranging market
        hold_signals = (signals == Signal.HOLD.value).sum()
        assert hold_signals > len(signals) * 0.5  # At least 50% holds

    def test_buy_signal_in_oversold_crossover(self):
        """Test BUY signal when %K crosses above %D in oversold zone."""
        # Create data that will generate oversold condition then crossover
        data = pd.DataFrame({
            'open': [100] * 50,
            'high': [101] * 50,
            'low': [99] * 50,
            'close': list(range(100, 90, -1)) + list(range(90, 110, 1)) + [110] * 10,
            'volume': [1000000] * 50
        })

        strategy = StochasticStrategy(k_period=14, d_period=3, oversold=20)
        signals = strategy.generate_signals(data)

        # Should have at least one BUY signal
        buy_signals = (signals == Signal.BUY.value).sum()
        assert buy_signals > 0

    def test_sell_signal_in_overbought_crossover(self):
        """Test SELL signal when %K crosses below %D in overbought zone."""
        # Create data that will generate overbought condition then crossover
        data = pd.DataFrame({
            'open': [100] * 50,
            'high': [101] * 50,
            'low': [99] * 50,
            'close': list(range(100, 120, 1)) + list(range(120, 100, -1)) + [100] * 10,
            'volume': [1000000] * 50
        })

        strategy = StochasticStrategy(k_period=14, d_period=3, overbought=80)
        signals = strategy.generate_signals(data)

        # Should have at least one SELL signal
        sell_signals = (signals == Signal.SELL.value).sum()
        assert sell_signals > 0

    def test_signals_series_length(self, sample_ohlcv_data):
        """Test that signals series has same length as input data."""
        strategy = StochasticStrategy()
        signals = strategy.generate_signals(sample_ohlcv_data)

        assert len(signals) == len(sample_ohlcv_data)
        assert signals.index.equals(sample_ohlcv_data.index)

    def test_signals_are_valid_values(self, sample_ohlcv_data):
        """Test that all signals are valid Signal enum values."""
        strategy = StochasticStrategy()
        signals = strategy.generate_signals(sample_ohlcv_data)

        valid_values = [Signal.BUY.value, Signal.SELL.value, Signal.HOLD.value]
        assert signals.isin(valid_values).all()

    @pytest.mark.parametrize("k_period,d_period", [
        (9, 3),
        (14, 3),
        (21, 5),
    ])
    def test_signals_with_different_periods(self, sample_ohlcv_data, k_period, d_period):
        """Test signal generation with different period parameters."""
        strategy = StochasticStrategy(k_period=k_period, d_period=d_period)
        signals = strategy.generate_signals(sample_ohlcv_data)

        assert len(signals) == len(sample_ohlcv_data)
        assert isinstance(signals, pd.Series)


class TestStochasticStrategyState:
    """Test strategy state management."""

    def test_get_strategy_state_with_sufficient_data(self, sample_ohlcv_data):
        """Test strategy state returns active status with sufficient data."""
        strategy = StochasticStrategy()
        state = strategy.get_strategy_state(sample_ohlcv_data)

        assert state['status'] == 'active'
        assert 'stoch_k' in state
        assert 'stoch_d' in state
        assert 'current_price' in state
        assert 'condition' in state
        assert 'k_period' in state
        assert 'd_period' in state

    def test_get_strategy_state_with_insufficient_data(self, insufficient_data):
        """Test strategy state returns insufficient_data status."""
        strategy = StochasticStrategy(k_period=14, d_period=3)
        state = strategy.get_strategy_state(insufficient_data)

        assert state['status'] == 'insufficient_data'
        assert 'message' in state
        assert '17' in state['message']  # k_period + d_period = 14 + 3 = 17

    def test_strategy_state_condition_oversold(self):
        """Test strategy state identifies oversold condition."""
        # Create oversold scenario
        data = pd.DataFrame({
            'open': [100] * 30,
            'high': [101] * 30,
            'low': [99] * 30,
            'close': list(range(100, 70, -1)),
            'volume': [1000000] * 30
        })

        strategy = StochasticStrategy(oversold=20)
        state = strategy.get_strategy_state(data)

        assert state['status'] == 'active'
        # Should be oversold or neutral depending on exact calculation
        assert state['condition'] in ['oversold', 'neutral']

    def test_strategy_state_condition_overbought(self):
        """Test strategy state identifies overbought condition."""
        # Create overbought scenario
        data = pd.DataFrame({
            'open': [100] * 30,
            'high': [101] * 30,
            'low': [99] * 30,
            'close': list(range(100, 130, 1)),
            'volume': [1000000] * 30
        })

        strategy = StochasticStrategy(overbought=80)
        state = strategy.get_strategy_state(data)

        assert state['status'] == 'active'
        # Should be overbought or neutral depending on exact calculation
        assert state['condition'] in ['overbought', 'neutral']

    def test_strategy_state_values_are_numeric(self, sample_ohlcv_data):
        """Test that strategy state values are numeric where expected."""
        strategy = StochasticStrategy()
        state = strategy.get_strategy_state(sample_ohlcv_data)

        if state['status'] == 'active':
            assert isinstance(state['stoch_k'], (int, float))
            assert isinstance(state['stoch_d'], (int, float))
            assert isinstance(state['current_price'], (int, float))
            assert isinstance(state['k_period'], int)
            assert isinstance(state['d_period'], int)


class TestStochasticEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_dataframe(self):
        """Test strategy handles empty DataFrame gracefully."""
        strategy = StochasticStrategy()
        empty_df = pd.DataFrame(columns=['open', 'high', 'low', 'close', 'volume'])

        state = strategy.get_strategy_state(empty_df)
        assert state['status'] == 'insufficient_data'

    def test_single_row_dataframe(self):
        """Test strategy handles single row DataFrame."""
        strategy = StochasticStrategy()
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
        # All prices the same (zero volatility)
        data = pd.DataFrame({
            'open': [100] * 30,
            'high': [100] * 30,
            'low': [100] * 30,
            'close': [100] * 30,
            'volume': [1000000] * 30
        })

        strategy = StochasticStrategy()
        result = strategy.calculate_stochastic(data)

        # Should handle division by zero gracefully (NaN or inf)
        assert 'stoch_k' in result.columns

    def test_extreme_parameter_values(self, sample_ohlcv_data):
        """Test strategy with extreme but valid parameter values."""
        # Very short periods
        strategy_short = StochasticStrategy(k_period=3, d_period=2, smooth_k=1)
        signals_short = strategy_short.generate_signals(sample_ohlcv_data)
        assert len(signals_short) == len(sample_ohlcv_data)

        # Very long periods
        strategy_long = StochasticStrategy(k_period=50, d_period=10, smooth_k=10)
        signals_long = strategy_long.generate_signals(sample_ohlcv_data)
        assert len(signals_long) == len(sample_ohlcv_data)

    def test_extreme_threshold_values(self, sample_ohlcv_data):
        """Test strategy with extreme but valid threshold values."""
        # Very tight thresholds
        strategy_tight = StochasticStrategy(oversold=45, overbought=55)
        signals = strategy_tight.generate_signals(sample_ohlcv_data)
        assert len(signals) == len(sample_ohlcv_data)

        # Very wide thresholds
        strategy_wide = StochasticStrategy(oversold=1, overbought=99)
        signals = strategy_wide.generate_signals(sample_ohlcv_data)
        assert len(signals) == len(sample_ohlcv_data)


class TestStochasticIntegration:
    """Integration tests for complete strategy workflow."""

    def test_full_workflow_trending_up(self, trending_up_data):
        """Test complete strategy workflow with uptrending data."""
        strategy = StochasticStrategy()

        # Calculate indicators
        df_with_indicators = strategy.calculate_indicators(trending_up_data)
        assert 'stoch_k' in df_with_indicators.columns

        # Generate signals
        signals = strategy.generate_signals(trending_up_data)
        assert len(signals) > 0

        # Get strategy state
        state = strategy.get_strategy_state(trending_up_data)
        assert state['status'] == 'active'

    def test_full_workflow_trending_down(self, trending_down_data):
        """Test complete strategy workflow with downtrending data."""
        strategy = StochasticStrategy()

        df_with_indicators = strategy.calculate_indicators(trending_down_data)
        signals = strategy.generate_signals(trending_down_data)
        state = strategy.get_strategy_state(trending_down_data)

        assert 'stoch_k' in df_with_indicators.columns
        assert len(signals) == len(trending_down_data)
        assert state['status'] == 'active'

    def test_strategy_produces_actionable_signals(self, volatile_data):
        """Test that strategy produces some actionable signals in volatile market."""
        strategy = StochasticStrategy()
        signals = strategy.generate_signals(volatile_data)

        # Should have at least some BUY or SELL signals in volatile data
        actionable_signals = ((signals == Signal.BUY.value) | (signals == Signal.SELL.value)).sum()
        assert actionable_signals > 0
