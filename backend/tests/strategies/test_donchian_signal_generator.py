"""
Unit tests for Donchian Channel (Turtle Trading) signal generation.

Tests the _generate_donchian_signal method with comprehensive coverage:
- BUY signals (price breaks above N-day high)
- SELL signals (price breaks below exit period low)
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


class TestDonchianBuySignals:
    """Test BUY signal generation for Donchian Channel strategy."""

    def test_buy_signal_breakout_above_entry_high(self, signal_generator):
        """Test BUY signal when price breaks above entry high."""
        parameters = {'entry_period': 20, 'exit_period': 10}
        indicators = {
            'current_price': 105.0,
            'entry_high_prev': 100.0,
            'exit_low_prev': 90.0,
            'atr_current': 2.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_donchian_signal(
            parameters, indicators, has_position=False
        )

        assert signal == SignalType.BUY
        assert 0.3 <= strength <= 1.0
        assert 'breakout' in reasoning.lower()
        assert '20-day high' in reasoning.lower()
        assert signal_indicators['entry_high'] == 100.0
        assert signal_indicators['atr'] == 2.0

    def test_buy_signal_strength_large_breakout(self, signal_generator):
        """Test BUY signal strength with large breakout distance."""
        parameters = {'entry_period': 20, 'exit_period': 10}
        indicators = {
            'current_price': 120.0,  # Large breakout
            'entry_high_prev': 100.0,
            'exit_low_prev': 90.0,
            'atr_current': 2.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_donchian_signal(
            parameters, indicators, has_position=False
        )

        assert signal == SignalType.BUY
        # breakout_pct = (120 - 100) / 100 * 100 = 20%
        # strength = min(20 * 10, 1.0) = 1.0
        assert strength >= 0.9

    def test_buy_signal_strength_small_breakout(self, signal_generator):
        """Test BUY signal strength with small breakout distance."""
        parameters = {'entry_period': 20, 'exit_period': 10}
        indicators = {
            'current_price': 100.5,  # Small breakout
            'entry_high_prev': 100.0,
            'exit_low_prev': 90.0,
            'atr_current': 2.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_donchian_signal(
            parameters, indicators, has_position=False
        )

        assert signal == SignalType.BUY
        # Minimum strength should be 0.3
        assert strength >= 0.3

    def test_buy_signal_minimal_breakout(self, signal_generator):
        """Test BUY signal with minimal breakout (just above high)."""
        parameters = {'entry_period': 20, 'exit_period': 10}
        indicators = {
            'current_price': 100.01,
            'entry_high_prev': 100.0,
            'exit_low_prev': 90.0,
            'atr_current': 2.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_donchian_signal(
            parameters, indicators, has_position=False
        )

        assert signal == SignalType.BUY
        assert strength >= 0.3

    def test_no_buy_signal_when_has_position(self, signal_generator):
        """Test no BUY signal when already has position."""
        parameters = {'entry_period': 20, 'exit_period': 10}
        indicators = {
            'current_price': 105.0,
            'entry_high_prev': 100.0,
            'exit_low_prev': 90.0,
            'atr_current': 2.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_donchian_signal(
            parameters, indicators, has_position=True  # Has position
        )

        assert signal == SignalType.HOLD
        assert strength == 0.0

    def test_no_buy_signal_price_at_high(self, signal_generator):
        """Test no BUY signal when price exactly at entry high."""
        parameters = {'entry_period': 20, 'exit_period': 10}
        indicators = {
            'current_price': 100.0,  # Exactly at high
            'entry_high_prev': 100.0,
            'exit_low_prev': 90.0,
            'atr_current': 2.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_donchian_signal(
            parameters, indicators, has_position=False
        )

        # Should NOT trigger (needs to be > entry_high)
        assert signal == SignalType.HOLD
        assert strength == 0.0

    def test_no_buy_signal_price_below_high(self, signal_generator):
        """Test no BUY signal when price below entry high."""
        parameters = {'entry_period': 20, 'exit_period': 10}
        indicators = {
            'current_price': 95.0,  # Below high
            'entry_high_prev': 100.0,
            'exit_low_prev': 90.0,
            'atr_current': 2.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_donchian_signal(
            parameters, indicators, has_position=False
        )

        assert signal == SignalType.HOLD
        assert strength == 0.0


class TestDonchianSellSignals:
    """Test SELL signal generation for Donchian Channel strategy."""

    def test_sell_signal_breakdown_below_exit_low(self, signal_generator):
        """Test SELL signal when price breaks below exit low."""
        parameters = {'entry_period': 20, 'exit_period': 10}
        indicators = {
            'current_price': 85.0,
            'entry_high_prev': 100.0,
            'exit_low_prev': 90.0,
            'atr_current': 2.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_donchian_signal(
            parameters, indicators, has_position=True
        )

        assert signal == SignalType.SELL
        assert 0.3 <= strength <= 1.0
        assert 'breakdown' in reasoning.lower()
        assert '10-day low' in reasoning.lower()
        assert signal_indicators['exit_low'] == 90.0

    def test_sell_signal_strength_large_breakdown(self, signal_generator):
        """Test SELL signal strength with large breakdown distance."""
        parameters = {'entry_period': 20, 'exit_period': 10}
        indicators = {
            'current_price': 70.0,  # Large breakdown
            'entry_high_prev': 100.0,
            'exit_low_prev': 90.0,
            'atr_current': 2.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_donchian_signal(
            parameters, indicators, has_position=True
        )

        assert signal == SignalType.SELL
        # breakdown_pct = (90 - 70) / 90 * 100 = 22.22%
        # strength = min(22.22 * 10, 1.0) = 1.0
        assert strength >= 0.9

    def test_sell_signal_strength_small_breakdown(self, signal_generator):
        """Test SELL signal strength with small breakdown distance."""
        parameters = {'entry_period': 20, 'exit_period': 10}
        indicators = {
            'current_price': 89.5,  # Small breakdown
            'entry_high_prev': 100.0,
            'exit_low_prev': 90.0,
            'atr_current': 2.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_donchian_signal(
            parameters, indicators, has_position=True
        )

        assert signal == SignalType.SELL
        assert strength >= 0.3

    def test_sell_signal_minimal_breakdown(self, signal_generator):
        """Test SELL signal with minimal breakdown (just below low)."""
        parameters = {'entry_period': 20, 'exit_period': 10}
        indicators = {
            'current_price': 89.99,
            'entry_high_prev': 100.0,
            'exit_low_prev': 90.0,
            'atr_current': 2.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_donchian_signal(
            parameters, indicators, has_position=True
        )

        assert signal == SignalType.SELL
        assert strength >= 0.3

    def test_no_sell_signal_when_no_position(self, signal_generator):
        """Test no SELL signal when no position to close."""
        parameters = {'entry_period': 20, 'exit_period': 10}
        indicators = {
            'current_price': 85.0,
            'entry_high_prev': 100.0,
            'exit_low_prev': 90.0,
            'atr_current': 2.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_donchian_signal(
            parameters, indicators, has_position=False  # No position
        )

        assert signal == SignalType.HOLD
        assert strength == 0.0

    def test_no_sell_signal_price_at_low(self, signal_generator):
        """Test no SELL signal when price exactly at exit low."""
        parameters = {'entry_period': 20, 'exit_period': 10}
        indicators = {
            'current_price': 90.0,  # Exactly at low
            'entry_high_prev': 100.0,
            'exit_low_prev': 90.0,
            'atr_current': 2.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_donchian_signal(
            parameters, indicators, has_position=True
        )

        # Should NOT trigger (needs to be < exit_low)
        assert signal == SignalType.HOLD
        assert strength == 0.0

    def test_no_sell_signal_price_above_low(self, signal_generator):
        """Test no SELL signal when price above exit low."""
        parameters = {'entry_period': 20, 'exit_period': 10}
        indicators = {
            'current_price': 95.0,  # Above low
            'entry_high_prev': 100.0,
            'exit_low_prev': 90.0,
            'atr_current': 2.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_donchian_signal(
            parameters, indicators, has_position=True
        )

        assert signal == SignalType.HOLD
        assert strength == 0.0


class TestDonchianHoldSignals:
    """Test HOLD signal generation for Donchian Channel strategy."""

    def test_hold_signal_within_channel(self, signal_generator):
        """Test HOLD signal when price within channel."""
        parameters = {'entry_period': 20, 'exit_period': 10}
        indicators = {
            'current_price': 95.0,  # Between low and high
            'entry_high_prev': 100.0,
            'exit_low_prev': 90.0,
            'atr_current': 2.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_donchian_signal(
            parameters, indicators, has_position=False
        )

        assert signal == SignalType.HOLD
        assert strength == 0.0
        assert 'neutral' in reasoning.lower()

    def test_hold_signal_neutral_with_position(self, signal_generator):
        """Test HOLD signal when has position but price within channel."""
        parameters = {'entry_period': 20, 'exit_period': 10}
        indicators = {
            'current_price': 95.0,
            'entry_high_prev': 100.0,
            'exit_low_prev': 90.0,
            'atr_current': 2.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_donchian_signal(
            parameters, indicators, has_position=True
        )

        assert signal == SignalType.HOLD
        assert strength == 0.0

    def test_hold_signal_at_midpoint(self, signal_generator):
        """Test HOLD signal when price at midpoint of channel."""
        parameters = {'entry_period': 20, 'exit_period': 10}
        indicators = {
            'current_price': 95.0,  # Midpoint
            'entry_high_prev': 100.0,
            'exit_low_prev': 90.0,
            'atr_current': 2.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_donchian_signal(
            parameters, indicators, has_position=False
        )

        assert signal == SignalType.HOLD
        assert strength == 0.0


class TestDonchianEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_missing_indicator_defaults(self, signal_generator):
        """Test default values when indicators are missing."""
        parameters = {'entry_period': 20, 'exit_period': 10}
        indicators = {
            'current_price': 100.0
            # All other indicators missing
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_donchian_signal(
            parameters, indicators, has_position=False
        )

        # Should use price as defaults, resulting in HOLD
        assert signal == SignalType.HOLD
        assert strength == 0.0

    def test_zero_atr_value(self, signal_generator):
        """Test with zero ATR value."""
        parameters = {'entry_period': 20, 'exit_period': 10}
        indicators = {
            'current_price': 105.0,
            'entry_high_prev': 100.0,
            'exit_low_prev': 90.0,
            'atr_current': 0.0  # Zero ATR
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_donchian_signal(
            parameters, indicators, has_position=False
        )

        assert signal == SignalType.BUY
        assert signal_indicators['atr'] == 0.0

    def test_very_narrow_channel(self, signal_generator):
        """Test with very narrow Donchian Channel."""
        parameters = {'entry_period': 20, 'exit_period': 10}
        indicators = {
            'current_price': 100.1,
            'entry_high_prev': 100.0,
            'exit_low_prev': 99.9,  # Narrow channel
            'atr_current': 0.05
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_donchian_signal(
            parameters, indicators, has_position=False
        )

        assert signal == SignalType.BUY
        assert strength >= 0.3

    def test_very_wide_channel(self, signal_generator):
        """Test with very wide Donchian Channel."""
        parameters = {'entry_period': 20, 'exit_period': 10}
        indicators = {
            'current_price': 95.0,
            'entry_high_prev': 200.0,
            'exit_low_prev': 10.0,  # Wide channel
            'atr_current': 10.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_donchian_signal(
            parameters, indicators, has_position=False
        )

        # Price within wide channel
        assert signal == SignalType.HOLD

    def test_custom_entry_period(self, signal_generator):
        """Test with custom entry period parameter."""
        parameters = {'entry_period': 55, 'exit_period': 20}  # Custom periods
        indicators = {
            'current_price': 105.0,
            'entry_high_prev': 100.0,
            'exit_low_prev': 90.0,
            'atr_current': 2.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_donchian_signal(
            parameters, indicators, has_position=False
        )

        assert signal == SignalType.BUY
        assert '55-day high' in reasoning.lower()

    def test_custom_exit_period(self, signal_generator):
        """Test with custom exit period parameter."""
        parameters = {'entry_period': 20, 'exit_period': 5}  # Custom periods
        indicators = {
            'current_price': 85.0,
            'entry_high_prev': 100.0,
            'exit_low_prev': 90.0,
            'atr_current': 2.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_donchian_signal(
            parameters, indicators, has_position=True
        )

        assert signal == SignalType.SELL
        assert '5-day low' in reasoning.lower()

    def test_default_period_parameters(self, signal_generator):
        """Test default period values when not specified."""
        parameters = {}  # No periods specified
        indicators = {
            'current_price': 105.0,
            'entry_high_prev': 100.0,
            'exit_low_prev': 90.0,
            'atr_current': 2.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_donchian_signal(
            parameters, indicators, has_position=False
        )

        assert signal == SignalType.BUY
        # Should mention default period (20) in reasoning
        assert 'day high' in reasoning.lower()

    def test_inverted_channel(self, signal_generator):
        """Test behavior with inverted channel (edge case)."""
        parameters = {'entry_period': 20, 'exit_period': 10}
        indicators = {
            'current_price': 95.0,
            'entry_high_prev': 80.0,  # Low value
            'exit_low_prev': 110.0,  # High value (inverted)
            'atr_current': 2.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_donchian_signal(
            parameters, indicators, has_position=False
        )

        # Price (95) > entry_high (80), so BUY
        assert signal == SignalType.BUY

    def test_zero_price(self, signal_generator):
        """Test with zero price."""
        parameters = {'entry_period': 20, 'exit_period': 10}
        indicators = {
            'current_price': 0.0,
            'entry_high_prev': 100.0,
            'exit_low_prev': 90.0,
            'atr_current': 2.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_donchian_signal(
            parameters, indicators, has_position=True
        )

        # Price (0) < exit_low (90), so SELL
        assert signal == SignalType.SELL

    def test_extreme_breakout(self, signal_generator):
        """Test with extreme breakout (price gap)."""
        parameters = {'entry_period': 20, 'exit_period': 10}
        indicators = {
            'current_price': 500.0,  # Extreme gap up
            'entry_high_prev': 100.0,
            'exit_low_prev': 90.0,
            'atr_current': 2.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_donchian_signal(
            parameters, indicators, has_position=False
        )

        assert signal == SignalType.BUY
        # Should cap at 1.0
        assert strength <= 1.0
        assert strength >= 0.9

    def test_signal_indicators_completeness(self, signal_generator):
        """Test that signal_indicators dict contains all required fields."""
        parameters = {'entry_period': 20, 'exit_period': 10}
        indicators = {
            'current_price': 105.0,
            'entry_high_prev': 100.0,
            'exit_low_prev': 90.0,
            'atr_current': 2.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_donchian_signal(
            parameters, indicators, has_position=False
        )

        assert 'entry_high' in signal_indicators
        assert 'exit_low' in signal_indicators
        assert 'atr' in signal_indicators
        assert 'current_price' in signal_indicators

    def test_reasoning_contains_values(self, signal_generator):
        """Test that reasoning string contains actual values."""
        parameters = {'entry_period': 20, 'exit_period': 10}
        indicators = {
            'current_price': 105.0,
            'entry_high_prev': 100.0,
            'exit_low_prev': 90.0,
            'atr_current': 2.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_donchian_signal(
            parameters, indicators, has_position=False
        )

        assert isinstance(reasoning, str)
        assert len(reasoning) > 0
        assert 'price=' in reasoning.lower()
        assert 'high=' in reasoning.lower()


class TestDonchianLogging:
    """Test logging behavior for Donchian signals."""

    @patch('app.strategies.signal_generator.logger')
    def test_buy_signal_logging(self, mock_logger, signal_generator):
        """Test that BUY signals are logged."""
        parameters = {'entry_period': 20, 'exit_period': 10}
        indicators = {
            'current_price': 105.0,
            'entry_high_prev': 100.0,
            'exit_low_prev': 90.0,
            'atr_current': 2.0
        }

        signal_generator._generate_donchian_signal(parameters, indicators, has_position=False)

        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args[0][0]
        assert 'DONCHIAN BUY signal' in call_args

    @patch('app.strategies.signal_generator.logger')
    def test_sell_signal_logging(self, mock_logger, signal_generator):
        """Test that SELL signals are logged."""
        parameters = {'entry_period': 20, 'exit_period': 10}
        indicators = {
            'current_price': 85.0,
            'entry_high_prev': 100.0,
            'exit_low_prev': 90.0,
            'atr_current': 2.0
        }

        signal_generator._generate_donchian_signal(parameters, indicators, has_position=True)

        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args[0][0]
        assert 'DONCHIAN SELL signal' in call_args
