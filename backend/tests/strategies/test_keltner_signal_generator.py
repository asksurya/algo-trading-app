"""
Unit tests for Keltner Channel signal generation.

Tests the _generate_keltner_signal method with comprehensive coverage:
- Breakout mode (BUY above upper, SELL below lower)
- Mean reversion mode (BUY at lower, SELL at upper)
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


class TestKeltnerBreakoutMode:
    """Test Keltner Channel signals in breakout mode."""

    def test_buy_signal_breakout_above_upper(self, signal_generator):
        """Test BUY signal when price breaks above upper band."""
        parameters = {'use_breakout': True}
        indicators = {
            'current_price': 105.0,
            'kc_upper_current': 100.0,
            'kc_middle_current': 95.0,
            'kc_lower_current': 90.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_keltner_signal(
            parameters, indicators, has_position=False
        )

        assert signal == SignalType.BUY
        assert 0.3 <= strength <= 1.0
        assert 'breakout' in reasoning.lower()
        assert 'upper' in reasoning.lower()
        assert signal_indicators['mode'] == 'breakout'
        assert signal_indicators['kc_upper'] == 100.0

    def test_buy_signal_strength_large_breakout(self, signal_generator):
        """Test BUY signal strength with large breakout distance."""
        parameters = {'use_breakout': True}
        indicators = {
            'current_price': 120.0,  # Large breakout
            'kc_upper_current': 100.0,
            'kc_middle_current': 95.0,
            'kc_lower_current': 90.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_keltner_signal(
            parameters, indicators, has_position=False
        )

        assert signal == SignalType.BUY
        # distance_pct = (120 - 100) / 100 * 100 = 20%
        # strength = min(20 * 5, 1.0) = 1.0
        assert strength >= 0.9

    def test_buy_signal_strength_small_breakout(self, signal_generator):
        """Test BUY signal strength with small breakout distance."""
        parameters = {'use_breakout': True}
        indicators = {
            'current_price': 100.5,  # Small breakout
            'kc_upper_current': 100.0,
            'kc_middle_current': 95.0,
            'kc_lower_current': 90.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_keltner_signal(
            parameters, indicators, has_position=False
        )

        assert signal == SignalType.BUY
        assert strength >= 0.3  # Minimum strength

    def test_no_buy_breakout_when_has_position(self, signal_generator):
        """Test no BUY signal in breakout mode when has position."""
        parameters = {'use_breakout': True}
        indicators = {
            'current_price': 105.0,
            'kc_upper_current': 100.0,
            'kc_middle_current': 95.0,
            'kc_lower_current': 90.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_keltner_signal(
            parameters, indicators, has_position=True
        )

        assert signal == SignalType.HOLD
        assert strength == 0.0

    def test_sell_signal_breakdown_below_lower(self, signal_generator):
        """Test SELL signal when price breaks below lower band."""
        parameters = {'use_breakout': True}
        indicators = {
            'current_price': 85.0,
            'kc_upper_current': 100.0,
            'kc_middle_current': 95.0,
            'kc_lower_current': 90.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_keltner_signal(
            parameters, indicators, has_position=True
        )

        assert signal == SignalType.SELL
        assert 0.3 <= strength <= 1.0
        assert 'breakdown' in reasoning.lower()
        assert 'lower' in reasoning.lower()

    def test_sell_signal_strength_large_breakdown(self, signal_generator):
        """Test SELL signal strength with large breakdown distance."""
        parameters = {'use_breakout': True}
        indicators = {
            'current_price': 70.0,  # Large breakdown
            'kc_upper_current': 100.0,
            'kc_middle_current': 95.0,
            'kc_lower_current': 90.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_keltner_signal(
            parameters, indicators, has_position=True
        )

        assert signal == SignalType.SELL
        # distance_pct = (90 - 70) / 90 * 100 = 22.22%
        # strength = min(22.22 * 5, 1.0) = 1.0
        assert strength >= 0.9

    def test_no_sell_breakdown_when_no_position(self, signal_generator):
        """Test no SELL signal in breakout mode when no position."""
        parameters = {'use_breakout': True}
        indicators = {
            'current_price': 85.0,
            'kc_upper_current': 100.0,
            'kc_middle_current': 95.0,
            'kc_lower_current': 90.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_keltner_signal(
            parameters, indicators, has_position=False
        )

        assert signal == SignalType.HOLD
        assert strength == 0.0


class TestKeltnerMeanReversionMode:
    """Test Keltner Channel signals in mean reversion mode."""

    def test_buy_signal_at_lower_band(self, signal_generator):
        """Test BUY signal when price at lower band (mean reversion)."""
        parameters = {'use_breakout': False}
        indicators = {
            'current_price': 89.0,  # At or below lower
            'kc_upper_current': 100.0,
            'kc_middle_current': 95.0,
            'kc_lower_current': 90.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_keltner_signal(
            parameters, indicators, has_position=False
        )

        assert signal == SignalType.BUY
        assert 0.3 <= strength <= 1.0
        assert 'mean reversion' in reasoning.lower()
        assert 'buy' in reasoning.lower()
        assert 'lower' in reasoning.lower()
        assert signal_indicators['mode'] == 'mean_reversion'

    def test_buy_signal_strength_mean_reversion(self, signal_generator):
        """Test BUY signal strength in mean reversion mode."""
        parameters = {'use_breakout': False}
        indicators = {
            'current_price': 85.0,  # Further below lower
            'kc_upper_current': 100.0,
            'kc_middle_current': 95.0,
            'kc_lower_current': 90.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_keltner_signal(
            parameters, indicators, has_position=False
        )

        assert signal == SignalType.BUY
        # distance_pct = (90 - 85) / 90 * 100 = 5.56%
        # strength = min(5.56 * 10, 1.0) = 0.556
        assert strength >= 0.5

    def test_sell_signal_at_upper_band(self, signal_generator):
        """Test SELL signal when price at upper band (mean reversion)."""
        parameters = {'use_breakout': False}
        indicators = {
            'current_price': 101.0,  # At or above upper
            'kc_upper_current': 100.0,
            'kc_middle_current': 95.0,
            'kc_lower_current': 90.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_keltner_signal(
            parameters, indicators, has_position=True
        )

        assert signal == SignalType.SELL
        assert 0.3 <= strength <= 1.0
        assert 'mean reversion' in reasoning.lower()
        assert 'sell' in reasoning.lower()
        assert 'upper' in reasoning.lower()

    def test_sell_signal_strength_mean_reversion(self, signal_generator):
        """Test SELL signal strength in mean reversion mode."""
        parameters = {'use_breakout': False}
        indicators = {
            'current_price': 110.0,  # Further above upper
            'kc_upper_current': 100.0,
            'kc_middle_current': 95.0,
            'kc_lower_current': 90.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_keltner_signal(
            parameters, indicators, has_position=True
        )

        assert signal == SignalType.SELL
        # distance_pct = (110 - 100) / 100 * 100 = 10%
        # strength = min(10 * 10, 1.0) = 1.0
        assert strength >= 0.9

    def test_no_buy_mean_reversion_when_has_position(self, signal_generator):
        """Test no BUY signal in mean reversion when has position."""
        parameters = {'use_breakout': False}
        indicators = {
            'current_price': 89.0,
            'kc_upper_current': 100.0,
            'kc_middle_current': 95.0,
            'kc_lower_current': 90.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_keltner_signal(
            parameters, indicators, has_position=True
        )

        assert signal == SignalType.HOLD
        assert strength == 0.0

    def test_no_sell_mean_reversion_when_no_position(self, signal_generator):
        """Test no SELL signal in mean reversion when no position."""
        parameters = {'use_breakout': False}
        indicators = {
            'current_price': 101.0,
            'kc_upper_current': 100.0,
            'kc_middle_current': 95.0,
            'kc_lower_current': 90.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_keltner_signal(
            parameters, indicators, has_position=False
        )

        assert signal == SignalType.HOLD
        assert strength == 0.0


class TestKeltnerHoldSignals:
    """Test HOLD signal generation for Keltner Channel."""

    def test_hold_signal_inside_channel_breakout_mode(self, signal_generator):
        """Test HOLD when price inside channel in breakout mode."""
        parameters = {'use_breakout': True}
        indicators = {
            'current_price': 95.0,  # Inside channel
            'kc_upper_current': 100.0,
            'kc_middle_current': 95.0,
            'kc_lower_current': 90.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_keltner_signal(
            parameters, indicators, has_position=False
        )

        assert signal == SignalType.HOLD
        assert strength == 0.0
        assert 'neutral' in reasoning.lower()

    def test_hold_signal_inside_channel_mean_reversion_mode(self, signal_generator):
        """Test HOLD when price inside channel in mean reversion mode."""
        parameters = {'use_breakout': False}
        indicators = {
            'current_price': 95.0,  # Inside channel
            'kc_upper_current': 100.0,
            'kc_middle_current': 95.0,
            'kc_lower_current': 90.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_keltner_signal(
            parameters, indicators, has_position=False
        )

        assert signal == SignalType.HOLD
        assert strength == 0.0

    def test_hold_signal_at_middle_band(self, signal_generator):
        """Test HOLD when price at middle band."""
        parameters = {'use_breakout': True}
        indicators = {
            'current_price': 95.0,
            'kc_upper_current': 100.0,
            'kc_middle_current': 95.0,
            'kc_lower_current': 90.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_keltner_signal(
            parameters, indicators, has_position=False
        )

        assert signal == SignalType.HOLD
        assert strength == 0.0


class TestKeltnerEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_default_use_breakout_parameter(self, signal_generator):
        """Test default mode is breakout when parameter not specified."""
        parameters = {}  # No use_breakout specified
        indicators = {
            'current_price': 105.0,
            'kc_upper_current': 100.0,
            'kc_middle_current': 95.0,
            'kc_lower_current': 90.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_keltner_signal(
            parameters, indicators, has_position=False
        )

        # Should default to breakout mode (True)
        assert signal == SignalType.BUY
        assert signal_indicators['mode'] == 'breakout'

    def test_missing_indicator_defaults(self, signal_generator):
        """Test default values when indicators are missing."""
        parameters = {'use_breakout': True}
        indicators = {
            'current_price': 100.0
            # All Keltner bands missing
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_keltner_signal(
            parameters, indicators, has_position=False
        )

        # Should use price as default for all bands
        assert signal == SignalType.HOLD  # Price = bands, no signal

    def test_exact_upper_band_boundary_breakout(self, signal_generator):
        """Test price exactly at upper band in breakout mode."""
        parameters = {'use_breakout': True}
        indicators = {
            'current_price': 100.0,  # Exactly at upper
            'kc_upper_current': 100.0,
            'kc_middle_current': 95.0,
            'kc_lower_current': 90.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_keltner_signal(
            parameters, indicators, has_position=False
        )

        # Should NOT trigger (needs to be > upper)
        assert signal == SignalType.HOLD

    def test_exact_lower_band_boundary_breakout(self, signal_generator):
        """Test price exactly at lower band in breakout mode."""
        parameters = {'use_breakout': True}
        indicators = {
            'current_price': 90.0,  # Exactly at lower
            'kc_upper_current': 100.0,
            'kc_middle_current': 95.0,
            'kc_lower_current': 90.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_keltner_signal(
            parameters, indicators, has_position=True
        )

        # Should NOT trigger (needs to be < lower)
        assert signal == SignalType.HOLD

    def test_exact_upper_band_boundary_mean_reversion(self, signal_generator):
        """Test price exactly at upper band in mean reversion mode."""
        parameters = {'use_breakout': False}
        indicators = {
            'current_price': 100.0,  # Exactly at upper
            'kc_upper_current': 100.0,
            'kc_middle_current': 95.0,
            'kc_lower_current': 90.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_keltner_signal(
            parameters, indicators, has_position=True
        )

        # Should trigger (>= upper)
        assert signal == SignalType.SELL

    def test_exact_lower_band_boundary_mean_reversion(self, signal_generator):
        """Test price exactly at lower band in mean reversion mode."""
        parameters = {'use_breakout': False}
        indicators = {
            'current_price': 90.0,  # Exactly at lower
            'kc_upper_current': 100.0,
            'kc_middle_current': 95.0,
            'kc_lower_current': 90.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_keltner_signal(
            parameters, indicators, has_position=False
        )

        # Should trigger (<= lower)
        assert signal == SignalType.BUY

    def test_zero_price(self, signal_generator):
        """Test with zero price."""
        parameters = {'use_breakout': True}
        indicators = {
            'current_price': 0.0,
            'kc_upper_current': 100.0,
            'kc_middle_current': 95.0,
            'kc_lower_current': 90.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_keltner_signal(
            parameters, indicators, has_position=True
        )

        # Price below lower should trigger SELL in breakout mode
        assert signal == SignalType.SELL

    def test_very_narrow_channel(self, signal_generator):
        """Test with very narrow Keltner Channel."""
        parameters = {'use_breakout': True}
        indicators = {
            'current_price': 100.5,
            'kc_upper_current': 100.1,
            'kc_middle_current': 100.0,
            'kc_lower_current': 99.9
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_keltner_signal(
            parameters, indicators, has_position=False
        )

        assert signal == SignalType.BUY
        assert strength >= 0.3

    def test_very_wide_channel(self, signal_generator):
        """Test with very wide Keltner Channel."""
        parameters = {'use_breakout': False}
        indicators = {
            'current_price': 100.0,
            'kc_upper_current': 200.0,
            'kc_middle_current': 100.0,
            'kc_lower_current': 0.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_keltner_signal(
            parameters, indicators, has_position=False
        )

        # Price at middle, should be HOLD
        assert signal == SignalType.HOLD

    def test_inverted_bands(self, signal_generator):
        """Test behavior with inverted bands (edge case)."""
        parameters = {'use_breakout': True}
        indicators = {
            'current_price': 95.0,
            'kc_upper_current': 90.0,  # Inverted
            'kc_middle_current': 95.0,
            'kc_lower_current': 100.0  # Inverted
        }

        # Should handle gracefully
        signal, strength, reasoning, signal_indicators = signal_generator._generate_keltner_signal(
            parameters, indicators, has_position=False
        )

        # Price > inverted upper (90), so BUY
        assert signal == SignalType.BUY

    def test_signal_indicators_completeness(self, signal_generator):
        """Test that signal_indicators dict contains all required fields."""
        parameters = {'use_breakout': True}
        indicators = {
            'current_price': 105.0,
            'kc_upper_current': 100.0,
            'kc_middle_current': 95.0,
            'kc_lower_current': 90.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_keltner_signal(
            parameters, indicators, has_position=False
        )

        assert 'kc_upper' in signal_indicators
        assert 'kc_middle' in signal_indicators
        assert 'kc_lower' in signal_indicators
        assert 'current_price' in signal_indicators
        assert 'mode' in signal_indicators

    def test_reasoning_contains_values(self, signal_generator):
        """Test that reasoning string contains actual values."""
        parameters = {'use_breakout': True}
        indicators = {
            'current_price': 105.0,
            'kc_upper_current': 100.0,
            'kc_middle_current': 95.0,
            'kc_lower_current': 90.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_keltner_signal(
            parameters, indicators, has_position=False
        )

        assert isinstance(reasoning, str)
        assert len(reasoning) > 0
        assert '105.0' in reasoning or 'price=' in reasoning
