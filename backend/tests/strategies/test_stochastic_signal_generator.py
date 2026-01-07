"""
Unit tests for Stochastic Oscillator signal generation.

Tests the _generate_stochastic_signal method with comprehensive coverage:
- BUY signals (bullish crossover in oversold zone)
- SELL signals (bearish crossover in overbought zone)
- HOLD signals (neutral conditions)
- Signal strength calculations
- Edge cases and boundary conditions
"""
import pytest
from unittest.mock import MagicMock, patch
from app.strategies.signal_generator import SignalGenerator
from app.models.enums import SignalType


@pytest.fixture
def signal_generator():
    """Create a SignalGenerator instance."""
    return SignalGenerator()


class TestStochasticBuySignals:
    """Test BUY signal generation for Stochastic strategy."""

    def test_buy_signal_bullish_crossover_oversold(self, signal_generator):
        """Test BUY signal when %K crosses above %D in oversold zone."""
        parameters = {'oversold': 20, 'overbought': 80}
        indicators = {
            'stoch_k_current': 15.0,
            'stoch_d_current': 14.0,
            'stoch_k_prev': 13.0,
            'stoch_d_prev': 14.5,
            'current_price': 100.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_stochastic_signal(
            parameters, indicators, has_position=False
        )

        assert signal == SignalType.BUY
        assert 0.3 <= strength <= 1.0
        assert 'bullish crossover' in reasoning.lower()
        assert 'oversold' in reasoning.lower()
        assert signal_indicators['stoch_k'] == 15.0
        assert signal_indicators['stoch_d'] == 14.0

    def test_buy_signal_strength_calculation_deep_oversold(self, signal_generator):
        """Test BUY signal strength when deeply oversold."""
        parameters = {'oversold': 20, 'overbought': 80}
        indicators = {
            'stoch_k_current': 5.0,  # Very oversold
            'stoch_d_current': 4.0,
            'stoch_k_prev': 3.0,
            'stoch_d_prev': 5.0,
            'current_price': 100.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_stochastic_signal(
            parameters, indicators, has_position=False
        )

        assert signal == SignalType.BUY
        # Deeper oversold should give higher strength
        # strength = min((20 - 5) / 20, 1.0) = 0.75
        assert strength >= 0.7
        assert strength <= 1.0

    def test_buy_signal_strength_minimum(self, signal_generator):
        """Test BUY signal has minimum strength of 0.3."""
        parameters = {'oversold': 20, 'overbought': 80}
        indicators = {
            'stoch_k_current': 19.0,  # Just below oversold
            'stoch_d_current': 18.0,
            'stoch_k_prev': 17.0,
            'stoch_d_prev': 19.0,
            'current_price': 100.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_stochastic_signal(
            parameters, indicators, has_position=False
        )

        assert signal == SignalType.BUY
        assert strength >= 0.3

    def test_no_buy_signal_when_has_position(self, signal_generator):
        """Test no BUY signal generated when already has position."""
        parameters = {'oversold': 20, 'overbought': 80}
        indicators = {
            'stoch_k_current': 15.0,
            'stoch_d_current': 14.0,
            'stoch_k_prev': 13.0,
            'stoch_d_prev': 14.5,
            'current_price': 100.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_stochastic_signal(
            parameters, indicators, has_position=True  # Already has position
        )

        assert signal == SignalType.HOLD
        assert strength == 0.0

    def test_no_buy_signal_without_crossover(self, signal_generator):
        """Test no BUY signal when %K doesn't cross above %D."""
        parameters = {'oversold': 20, 'overbought': 80}
        indicators = {
            'stoch_k_current': 15.0,
            'stoch_d_current': 14.0,
            'stoch_k_prev': 16.0,  # Was already above
            'stoch_d_prev': 14.5,
            'current_price': 100.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_stochastic_signal(
            parameters, indicators, has_position=False
        )

        assert signal == SignalType.HOLD
        assert strength == 0.0

    def test_no_buy_signal_not_in_oversold_zone(self, signal_generator):
        """Test no BUY signal when crossover occurs outside oversold zone."""
        parameters = {'oversold': 20, 'overbought': 80}
        indicators = {
            'stoch_k_current': 50.0,  # Not oversold
            'stoch_d_current': 49.0,
            'stoch_k_prev': 48.0,
            'stoch_d_prev': 50.0,
            'current_price': 100.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_stochastic_signal(
            parameters, indicators, has_position=False
        )

        assert signal == SignalType.HOLD
        assert strength == 0.0


class TestStochasticSellSignals:
    """Test SELL signal generation for Stochastic strategy."""

    def test_sell_signal_bearish_crossover_overbought(self, signal_generator):
        """Test SELL signal when %K crosses below %D in overbought zone."""
        parameters = {'oversold': 20, 'overbought': 80}
        indicators = {
            'stoch_k_current': 85.0,
            'stoch_d_current': 86.0,
            'stoch_k_prev': 87.0,
            'stoch_d_prev': 85.0,
            'current_price': 100.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_stochastic_signal(
            parameters, indicators, has_position=True
        )

        assert signal == SignalType.SELL
        assert 0.3 <= strength <= 1.0
        assert 'bearish crossover' in reasoning.lower()
        assert 'overbought' in reasoning.lower()
        assert signal_indicators['stoch_k'] == 85.0
        assert signal_indicators['stoch_d'] == 86.0

    def test_sell_signal_strength_calculation_deep_overbought(self, signal_generator):
        """Test SELL signal strength when deeply overbought."""
        parameters = {'oversold': 20, 'overbought': 80}
        indicators = {
            'stoch_k_current': 95.0,  # Very overbought
            'stoch_d_current': 96.0,
            'stoch_k_prev': 97.0,
            'stoch_d_prev': 95.0,
            'current_price': 100.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_stochastic_signal(
            parameters, indicators, has_position=True
        )

        assert signal == SignalType.SELL
        # Deeper overbought should give higher strength
        # strength = min((95 - 80) / (100 - 80), 1.0) = 0.75
        assert strength >= 0.7
        assert strength <= 1.0

    def test_sell_signal_strength_minimum(self, signal_generator):
        """Test SELL signal has minimum strength of 0.3."""
        parameters = {'oversold': 20, 'overbought': 80}
        indicators = {
            'stoch_k_current': 81.0,  # Just above overbought
            'stoch_d_current': 82.0,
            'stoch_k_prev': 83.0,
            'stoch_d_prev': 81.0,
            'current_price': 100.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_stochastic_signal(
            parameters, indicators, has_position=True
        )

        assert signal == SignalType.SELL
        assert strength >= 0.3

    def test_no_sell_signal_when_no_position(self, signal_generator):
        """Test no SELL signal generated when no position to close."""
        parameters = {'oversold': 20, 'overbought': 80}
        indicators = {
            'stoch_k_current': 85.0,
            'stoch_d_current': 86.0,
            'stoch_k_prev': 87.0,
            'stoch_d_prev': 85.0,
            'current_price': 100.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_stochastic_signal(
            parameters, indicators, has_position=False  # No position
        )

        assert signal == SignalType.HOLD
        assert strength == 0.0

    def test_no_sell_signal_without_crossover(self, signal_generator):
        """Test no SELL signal when %K doesn't cross below %D."""
        parameters = {'oversold': 20, 'overbought': 80}
        indicators = {
            'stoch_k_current': 85.0,
            'stoch_d_current': 86.0,
            'stoch_k_prev': 84.0,  # Was already below
            'stoch_d_prev': 85.0,
            'current_price': 100.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_stochastic_signal(
            parameters, indicators, has_position=True
        )

        assert signal == SignalType.HOLD
        assert strength == 0.0

    def test_no_sell_signal_not_in_overbought_zone(self, signal_generator):
        """Test no SELL signal when crossover occurs outside overbought zone."""
        parameters = {'oversold': 20, 'overbought': 80}
        indicators = {
            'stoch_k_current': 50.0,  # Not overbought
            'stoch_d_current': 51.0,
            'stoch_k_prev': 52.0,
            'stoch_d_prev': 50.0,
            'current_price': 100.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_stochastic_signal(
            parameters, indicators, has_position=True
        )

        assert signal == SignalType.HOLD
        assert strength == 0.0


class TestStochasticHoldSignals:
    """Test HOLD signal generation for Stochastic strategy."""

    def test_hold_signal_neutral_zone(self, signal_generator):
        """Test HOLD signal in neutral zone (no crossover)."""
        parameters = {'oversold': 20, 'overbought': 80}
        indicators = {
            'stoch_k_current': 50.0,
            'stoch_d_current': 50.0,
            'stoch_k_prev': 49.0,
            'stoch_d_prev': 49.0,
            'current_price': 100.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_stochastic_signal(
            parameters, indicators, has_position=False
        )

        assert signal == SignalType.HOLD
        assert strength == 0.0
        assert 'neutral' in reasoning.lower()

    def test_hold_signal_no_crossover_oversold(self, signal_generator):
        """Test HOLD signal when in oversold but no crossover."""
        parameters = {'oversold': 20, 'overbought': 80}
        indicators = {
            'stoch_k_current': 15.0,
            'stoch_d_current': 20.0,
            'stoch_k_prev': 14.0,
            'stoch_d_prev': 21.0,
            'current_price': 100.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_stochastic_signal(
            parameters, indicators, has_position=False
        )

        assert signal == SignalType.HOLD
        assert strength == 0.0

    def test_hold_signal_no_crossover_overbought(self, signal_generator):
        """Test HOLD signal when in overbought but no crossover."""
        parameters = {'oversold': 20, 'overbought': 80}
        indicators = {
            'stoch_k_current': 85.0,
            'stoch_d_current': 90.0,
            'stoch_k_prev': 84.0,
            'stoch_d_prev': 91.0,
            'current_price': 100.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_stochastic_signal(
            parameters, indicators, has_position=True
        )

        assert signal == SignalType.HOLD
        assert strength == 0.0


class TestStochasticEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_default_indicator_values(self, signal_generator):
        """Test default values are used when indicators missing."""
        parameters = {'oversold': 20, 'overbought': 80}
        indicators = {
            'current_price': 100.0
            # All stochastic values missing
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_stochastic_signal(
            parameters, indicators, has_position=False
        )

        # Should default to 50 and result in HOLD
        assert signal == SignalType.HOLD
        assert strength == 0.0

    def test_custom_oversold_overbought_levels(self, signal_generator):
        """Test with custom oversold/overbought levels."""
        parameters = {'oversold': 30, 'overbought': 70}
        indicators = {
            'stoch_k_current': 25.0,
            'stoch_d_current': 24.0,
            'stoch_k_prev': 23.0,
            'stoch_d_prev': 25.0,
            'current_price': 100.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_stochastic_signal(
            parameters, indicators, has_position=False
        )

        assert signal == SignalType.BUY
        assert signal_indicators['oversold'] == 30
        assert signal_indicators['overbought'] == 70

    def test_exact_oversold_boundary(self, signal_generator):
        """Test behavior at exact oversold boundary."""
        parameters = {'oversold': 20, 'overbought': 80}
        indicators = {
            'stoch_k_current': 20.0,  # Exactly at boundary
            'stoch_d_current': 19.0,
            'stoch_k_prev': 18.0,
            'stoch_d_prev': 20.0,
            'current_price': 100.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_stochastic_signal(
            parameters, indicators, has_position=False
        )

        # Should NOT trigger (needs to be < oversold)
        assert signal == SignalType.HOLD

    def test_exact_overbought_boundary(self, signal_generator):
        """Test behavior at exact overbought boundary."""
        parameters = {'oversold': 20, 'overbought': 80}
        indicators = {
            'stoch_k_current': 80.0,  # Exactly at boundary
            'stoch_d_current': 81.0,
            'stoch_k_prev': 82.0,
            'stoch_d_prev': 80.0,
            'current_price': 100.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_stochastic_signal(
            parameters, indicators, has_position=True
        )

        # Should NOT trigger (needs to be > overbought)
        assert signal == SignalType.HOLD

    def test_zero_stochastic_values(self, signal_generator):
        """Test with zero stochastic values."""
        parameters = {'oversold': 20, 'overbought': 80}
        indicators = {
            'stoch_k_current': 0.0,
            'stoch_d_current': 0.0,
            'stoch_k_prev': 0.0,
            'stoch_d_prev': 0.0,
            'current_price': 100.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_stochastic_signal(
            parameters, indicators, has_position=False
        )

        # No crossover at 0, so HOLD
        assert signal == SignalType.HOLD
        assert strength == 0.0

    def test_max_stochastic_values(self, signal_generator):
        """Test with maximum stochastic values (100)."""
        parameters = {'oversold': 20, 'overbought': 80}
        indicators = {
            'stoch_k_current': 100.0,
            'stoch_d_current': 100.0,
            'stoch_k_prev': 100.0,
            'stoch_d_prev': 100.0,
            'current_price': 100.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_stochastic_signal(
            parameters, indicators, has_position=True
        )

        # No crossover at 100, so HOLD
        assert signal == SignalType.HOLD
        assert strength == 0.0

    def test_signal_indicators_completeness(self, signal_generator):
        """Test that signal_indicators dict contains all required fields."""
        parameters = {'oversold': 20, 'overbought': 80}
        indicators = {
            'stoch_k_current': 15.0,
            'stoch_d_current': 14.0,
            'stoch_k_prev': 13.0,
            'stoch_d_prev': 14.5,
            'current_price': 100.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_stochastic_signal(
            parameters, indicators, has_position=False
        )

        assert 'stoch_k' in signal_indicators
        assert 'stoch_d' in signal_indicators
        assert 'oversold' in signal_indicators
        assert 'overbought' in signal_indicators
        assert 'current_price' in signal_indicators

    def test_reasoning_string_format(self, signal_generator):
        """Test that reasoning string is properly formatted."""
        parameters = {'oversold': 20, 'overbought': 80}
        indicators = {
            'stoch_k_current': 15.0,
            'stoch_d_current': 14.0,
            'stoch_k_prev': 13.0,
            'stoch_d_prev': 14.5,
            'current_price': 100.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_stochastic_signal(
            parameters, indicators, has_position=False
        )

        assert isinstance(reasoning, str)
        assert len(reasoning) > 0
        assert '%K=' in reasoning
        assert '%D=' in reasoning


class TestStochasticLogging:
    """Test logging behavior for Stochastic signals."""

    @patch('app.strategies.signal_generator.logger')
    def test_buy_signal_logging(self, mock_logger, signal_generator):
        """Test that BUY signals are logged."""
        parameters = {'oversold': 20, 'overbought': 80}
        indicators = {
            'stoch_k_current': 15.0,
            'stoch_d_current': 14.0,
            'stoch_k_prev': 13.0,
            'stoch_d_prev': 14.5,
            'current_price': 100.0
        }

        signal_generator._generate_stochastic_signal(parameters, indicators, has_position=False)

        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args[0][0]
        assert 'STOCHASTIC BUY signal' in call_args

    @patch('app.strategies.signal_generator.logger')
    def test_sell_signal_logging(self, mock_logger, signal_generator):
        """Test that SELL signals are logged."""
        parameters = {'oversold': 20, 'overbought': 80}
        indicators = {
            'stoch_k_current': 85.0,
            'stoch_d_current': 86.0,
            'stoch_k_prev': 87.0,
            'stoch_d_prev': 85.0,
            'current_price': 100.0
        }

        signal_generator._generate_stochastic_signal(parameters, indicators, has_position=True)

        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args[0][0]
        assert 'STOCHASTIC SELL signal' in call_args
