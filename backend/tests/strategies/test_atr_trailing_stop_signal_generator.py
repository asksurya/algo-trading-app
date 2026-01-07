"""
Unit tests for ATR Trailing Stop signal generation.

Tests the _generate_atr_trailing_stop_signal method with comprehensive coverage:
- BUY signals (price crosses above trend EMA)
- SELL signals (price crosses below trailing stop)
- HOLD signals (neutral conditions)
- Signal strength calculations
- Edge cases and boundary conditions
"""
import pytest
from unittest.mock import patch
from app.strategies.signal_generator import SignalGenerator
from app.models.enums import SignalType


@pytest.fixture
def signal_generator():
    """Create a SignalGenerator instance."""
    return SignalGenerator()


class TestATRTrailingStopBuySignals:
    """Test BUY signal generation for ATR Trailing Stop strategy."""

    def test_buy_signal_price_crosses_above_ema(self, signal_generator):
        """Test BUY signal when price crosses above trend EMA."""
        parameters = {}
        indicators = {
            'current_price': 102.0,
            'prev_close': 98.0,
            'trend_ema_current': 100.0,
            'trend_ema_prev': 100.0,
            'trailing_stop_current': 95.0,
            'trailing_stop_prev': 95.0,
            'atr_current': 2.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_atr_trailing_stop_signal(
            parameters, indicators, has_position=False
        )

        assert signal == SignalType.BUY
        assert 0.3 <= strength <= 1.0
        assert 'crossed above' in reasoning.lower()
        assert 'ema' in reasoning.lower()
        assert signal_indicators['trend_ema'] == 100.0
        assert signal_indicators['atr'] == 2.0

    def test_buy_signal_strength_large_distance(self, signal_generator):
        """Test BUY signal strength with large distance from EMA."""
        parameters = {}
        indicators = {
            'current_price': 110.0,  # Large distance
            'prev_close': 98.0,
            'trend_ema_current': 100.0,
            'trend_ema_prev': 100.0,
            'trailing_stop_current': 95.0,
            'trailing_stop_prev': 95.0,
            'atr_current': 2.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_atr_trailing_stop_signal(
            parameters, indicators, has_position=False
        )

        assert signal == SignalType.BUY
        # distance_pct = (110 - 100) / 100 * 100 = 10%
        # strength = min(10 * 5, 1.0) = 1.0
        assert strength >= 0.9

    def test_buy_signal_strength_small_distance(self, signal_generator):
        """Test BUY signal strength with small distance from EMA."""
        parameters = {}
        indicators = {
            'current_price': 100.5,  # Small distance
            'prev_close': 99.5,
            'trend_ema_current': 100.0,
            'trend_ema_prev': 100.0,
            'trailing_stop_current': 95.0,
            'trailing_stop_prev': 95.0,
            'atr_current': 2.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_atr_trailing_stop_signal(
            parameters, indicators, has_position=False
        )

        assert signal == SignalType.BUY
        # Minimum strength should be 0.3
        assert strength >= 0.3

    def test_buy_signal_exact_crossover(self, signal_generator):
        """Test BUY signal at exact crossover point."""
        parameters = {}
        indicators = {
            'current_price': 100.01,
            'prev_close': 99.99,
            'trend_ema_current': 100.0,
            'trend_ema_prev': 100.0,
            'trailing_stop_current': 95.0,
            'trailing_stop_prev': 95.0,
            'atr_current': 2.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_atr_trailing_stop_signal(
            parameters, indicators, has_position=False
        )

        assert signal == SignalType.BUY
        assert strength >= 0.3

    def test_no_buy_signal_when_has_position(self, signal_generator):
        """Test no BUY signal when already has position."""
        parameters = {}
        indicators = {
            'current_price': 102.0,
            'prev_close': 98.0,
            'trend_ema_current': 100.0,
            'trend_ema_prev': 100.0,
            'trailing_stop_current': 95.0,
            'trailing_stop_prev': 95.0,
            'atr_current': 2.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_atr_trailing_stop_signal(
            parameters, indicators, has_position=True  # Has position
        )

        assert signal == SignalType.HOLD
        assert strength == 0.0

    def test_no_buy_signal_already_above_ema(self, signal_generator):
        """Test no BUY signal when price was already above EMA (no crossover)."""
        parameters = {}
        indicators = {
            'current_price': 102.0,
            'prev_close': 101.0,  # Already above
            'trend_ema_current': 100.0,
            'trend_ema_prev': 100.0,
            'trailing_stop_current': 95.0,
            'trailing_stop_prev': 95.0,
            'atr_current': 2.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_atr_trailing_stop_signal(
            parameters, indicators, has_position=False
        )

        assert signal == SignalType.HOLD
        assert strength == 0.0

    def test_no_buy_signal_price_below_ema(self, signal_generator):
        """Test no BUY signal when price still below EMA."""
        parameters = {}
        indicators = {
            'current_price': 98.0,  # Below EMA
            'prev_close': 97.0,
            'trend_ema_current': 100.0,
            'trend_ema_prev': 100.0,
            'trailing_stop_current': 95.0,
            'trailing_stop_prev': 95.0,
            'atr_current': 2.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_atr_trailing_stop_signal(
            parameters, indicators, has_position=False
        )

        assert signal == SignalType.HOLD
        assert strength == 0.0


class TestATRTrailingStopSellSignals:
    """Test SELL signal generation for ATR Trailing Stop strategy."""

    def test_sell_signal_price_crosses_below_stop(self, signal_generator):
        """Test SELL signal when price crosses below trailing stop."""
        parameters = {}
        indicators = {
            'current_price': 94.0,
            'prev_close': 96.0,
            'trend_ema_current': 100.0,
            'trend_ema_prev': 100.0,
            'trailing_stop_current': 95.0,
            'trailing_stop_prev': 95.0,
            'atr_current': 2.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_atr_trailing_stop_signal(
            parameters, indicators, has_position=True
        )

        assert signal == SignalType.SELL
        assert 0.3 <= strength <= 1.0
        assert 'crossed below' in reasoning.lower()
        assert 'stop' in reasoning.lower()
        assert signal_indicators['trailing_stop'] == 95.0

    def test_sell_signal_strength_large_distance(self, signal_generator):
        """Test SELL signal strength with large distance from stop."""
        parameters = {}
        indicators = {
            'current_price': 85.0,  # Large distance
            'prev_close': 96.0,
            'trend_ema_current': 100.0,
            'trend_ema_prev': 100.0,
            'trailing_stop_current': 95.0,
            'trailing_stop_prev': 95.0,
            'atr_current': 2.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_atr_trailing_stop_signal(
            parameters, indicators, has_position=True
        )

        assert signal == SignalType.SELL
        # distance_pct = (95 - 85) / 95 * 100 = 10.53%
        # strength = min(10.53 * 5, 1.0) = 1.0
        assert strength >= 0.9

    def test_sell_signal_strength_small_distance(self, signal_generator):
        """Test SELL signal strength with small distance from stop."""
        parameters = {}
        indicators = {
            'current_price': 94.5,  # Small distance
            'prev_close': 95.5,
            'trend_ema_current': 100.0,
            'trend_ema_prev': 100.0,
            'trailing_stop_current': 95.0,
            'trailing_stop_prev': 95.0,
            'atr_current': 2.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_atr_trailing_stop_signal(
            parameters, indicators, has_position=True
        )

        assert signal == SignalType.SELL
        assert strength >= 0.3

    def test_sell_signal_exact_crossover(self, signal_generator):
        """Test SELL signal at exact crossover point."""
        parameters = {}
        indicators = {
            'current_price': 94.99,
            'prev_close': 95.01,
            'trend_ema_current': 100.0,
            'trend_ema_prev': 100.0,
            'trailing_stop_current': 95.0,
            'trailing_stop_prev': 95.0,
            'atr_current': 2.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_atr_trailing_stop_signal(
            parameters, indicators, has_position=True
        )

        assert signal == SignalType.SELL
        assert strength >= 0.3

    def test_no_sell_signal_when_no_position(self, signal_generator):
        """Test no SELL signal when no position to close."""
        parameters = {}
        indicators = {
            'current_price': 94.0,
            'prev_close': 96.0,
            'trend_ema_current': 100.0,
            'trend_ema_prev': 100.0,
            'trailing_stop_current': 95.0,
            'trailing_stop_prev': 95.0,
            'atr_current': 2.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_atr_trailing_stop_signal(
            parameters, indicators, has_position=False  # No position
        )

        assert signal == SignalType.HOLD
        assert strength == 0.0

    def test_no_sell_signal_already_below_stop(self, signal_generator):
        """Test no SELL signal when price was already below stop (no crossover)."""
        parameters = {}
        indicators = {
            'current_price': 94.0,
            'prev_close': 93.0,  # Already below
            'trend_ema_current': 100.0,
            'trend_ema_prev': 100.0,
            'trailing_stop_current': 95.0,
            'trailing_stop_prev': 95.0,
            'atr_current': 2.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_atr_trailing_stop_signal(
            parameters, indicators, has_position=True
        )

        assert signal == SignalType.HOLD
        assert strength == 0.0

    def test_no_sell_signal_price_above_stop(self, signal_generator):
        """Test no SELL signal when price still above stop."""
        parameters = {}
        indicators = {
            'current_price': 98.0,  # Above stop
            'prev_close': 97.0,
            'trend_ema_current': 100.0,
            'trend_ema_prev': 100.0,
            'trailing_stop_current': 95.0,
            'trailing_stop_prev': 95.0,
            'atr_current': 2.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_atr_trailing_stop_signal(
            parameters, indicators, has_position=True
        )

        assert signal == SignalType.HOLD
        assert strength == 0.0


class TestATRTrailingStopHoldSignals:
    """Test HOLD signal generation for ATR Trailing Stop strategy."""

    def test_hold_signal_neutral_conditions(self, signal_generator):
        """Test HOLD signal in neutral market conditions."""
        parameters = {}
        indicators = {
            'current_price': 97.0,  # Between stop and EMA
            'prev_close': 96.5,
            'trend_ema_current': 100.0,
            'trend_ema_prev': 100.0,
            'trailing_stop_current': 95.0,
            'trailing_stop_prev': 95.0,
            'atr_current': 2.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_atr_trailing_stop_signal(
            parameters, indicators, has_position=True
        )

        assert signal == SignalType.HOLD
        assert strength == 0.0
        assert 'neutral' in reasoning.lower()

    def test_hold_signal_at_ema(self, signal_generator):
        """Test HOLD signal when price at EMA."""
        parameters = {}
        indicators = {
            'current_price': 100.0,  # At EMA
            'prev_close': 100.0,
            'trend_ema_current': 100.0,
            'trend_ema_prev': 100.0,
            'trailing_stop_current': 95.0,
            'trailing_stop_prev': 95.0,
            'atr_current': 2.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_atr_trailing_stop_signal(
            parameters, indicators, has_position=False
        )

        # Price = EMA, no crossover
        assert signal == SignalType.HOLD
        assert strength == 0.0

    def test_hold_signal_at_stop(self, signal_generator):
        """Test HOLD signal when price at trailing stop."""
        parameters = {}
        indicators = {
            'current_price': 95.0,  # At stop
            'prev_close': 95.0,
            'trend_ema_current': 100.0,
            'trend_ema_prev': 100.0,
            'trailing_stop_current': 95.0,
            'trailing_stop_prev': 95.0,
            'atr_current': 2.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_atr_trailing_stop_signal(
            parameters, indicators, has_position=True
        )

        # Price = stop, no crossover
        assert signal == SignalType.HOLD
        assert strength == 0.0


class TestATRTrailingStopEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_missing_indicator_defaults(self, signal_generator):
        """Test default values when indicators are missing."""
        parameters = {}
        indicators = {
            'current_price': 100.0
            # All other indicators missing
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_atr_trailing_stop_signal(
            parameters, indicators, has_position=False
        )

        # Should use price as defaults
        assert signal == SignalType.HOLD  # No crossover with defaults

    def test_zero_atr_value(self, signal_generator):
        """Test with zero ATR value."""
        parameters = {}
        indicators = {
            'current_price': 102.0,
            'prev_close': 98.0,
            'trend_ema_current': 100.0,
            'trend_ema_prev': 100.0,
            'trailing_stop_current': 95.0,
            'trailing_stop_prev': 95.0,
            'atr_current': 0.0  # Zero ATR
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_atr_trailing_stop_signal(
            parameters, indicators, has_position=False
        )

        assert signal == SignalType.BUY
        assert signal_indicators['atr'] == 0.0

    def test_very_high_volatility(self, signal_generator):
        """Test with very high ATR (high volatility)."""
        parameters = {}
        indicators = {
            'current_price': 102.0,
            'prev_close': 98.0,
            'trend_ema_current': 100.0,
            'trend_ema_prev': 100.0,
            'trailing_stop_current': 50.0,  # Wide stop
            'trailing_stop_prev': 50.0,
            'atr_current': 20.0  # High ATR
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_atr_trailing_stop_signal(
            parameters, indicators, has_position=False
        )

        assert signal == SignalType.BUY
        assert signal_indicators['atr'] == 20.0

    def test_moving_ema(self, signal_generator):
        """Test with moving EMA (trend changing)."""
        parameters = {}
        indicators = {
            'current_price': 101.0,
            'prev_close': 97.0,  # Was below prev EMA
            'trend_ema_current': 100.0,
            'trend_ema_prev': 98.0,  # EMA rising
            'trailing_stop_current': 95.0,
            'trailing_stop_prev': 93.0,  # Stop rising
            'atr_current': 2.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_atr_trailing_stop_signal(
            parameters, indicators, has_position=False
        )

        # Price crosses from below prev_ema (97 < 98) to above current_ema (101 > 100)
        assert signal == SignalType.BUY

    def test_moving_stop(self, signal_generator):
        """Test with moving trailing stop."""
        parameters = {}
        indicators = {
            'current_price': 94.0,
            'prev_close': 96.0,
            'trend_ema_current': 100.0,
            'trend_ema_prev': 100.0,
            'trailing_stop_current': 95.0,
            'trailing_stop_prev': 93.0,  # Stop moved up
            'atr_current': 2.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_atr_trailing_stop_signal(
            parameters, indicators, has_position=True
        )

        # Price crosses from above prev_stop to below current_stop
        assert signal == SignalType.SELL

    def test_price_equals_prev_price(self, signal_generator):
        """Test when current price equals previous price."""
        parameters = {}
        indicators = {
            'current_price': 100.0,
            'prev_close': 100.0,  # No change
            'trend_ema_current': 98.0,
            'trend_ema_prev': 98.0,
            'trailing_stop_current': 95.0,
            'trailing_stop_prev': 95.0,
            'atr_current': 2.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_atr_trailing_stop_signal(
            parameters, indicators, has_position=False
        )

        # Already above EMA, no crossover
        assert signal == SignalType.HOLD

    def test_signal_indicators_completeness(self, signal_generator):
        """Test that signal_indicators dict contains all required fields."""
        parameters = {}
        indicators = {
            'current_price': 102.0,
            'prev_close': 98.0,
            'trend_ema_current': 100.0,
            'trend_ema_prev': 100.0,
            'trailing_stop_current': 95.0,
            'trailing_stop_prev': 95.0,
            'atr_current': 2.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_atr_trailing_stop_signal(
            parameters, indicators, has_position=False
        )

        assert 'atr' in signal_indicators
        assert 'trend_ema' in signal_indicators
        assert 'trailing_stop' in signal_indicators
        assert 'current_price' in signal_indicators

    def test_reasoning_contains_values(self, signal_generator):
        """Test that reasoning string contains actual values."""
        parameters = {}
        indicators = {
            'current_price': 102.0,
            'prev_close': 98.0,
            'trend_ema_current': 100.0,
            'trend_ema_prev': 100.0,
            'trailing_stop_current': 95.0,
            'trailing_stop_prev': 95.0,
            'atr_current': 2.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_atr_trailing_stop_signal(
            parameters, indicators, has_position=False
        )

        assert isinstance(reasoning, str)
        assert len(reasoning) > 0
        assert 'price=' in reasoning.lower() or '102.0' in reasoning

    def test_extreme_price_movement(self, signal_generator):
        """Test with extreme price movement (gap)."""
        parameters = {}
        indicators = {
            'current_price': 150.0,  # Large gap up
            'prev_close': 95.0,
            'trend_ema_current': 100.0,
            'trend_ema_prev': 100.0,
            'trailing_stop_current': 95.0,
            'trailing_stop_prev': 95.0,
            'atr_current': 2.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_atr_trailing_stop_signal(
            parameters, indicators, has_position=False
        )

        assert signal == SignalType.BUY
        # Should cap at 1.0
        assert strength <= 1.0
