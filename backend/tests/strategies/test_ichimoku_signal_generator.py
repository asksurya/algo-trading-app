"""
Unit tests for Ichimoku Cloud signal generation.

Tests the _generate_ichimoku_signal method with comprehensive coverage:
- Strong BUY signals (TK cross up + price above cloud + bullish future cloud)
- Weak BUY signals (TK cross up only)
- Strong SELL signals (TK cross down + price below cloud + bearish future cloud)
- Weak SELL signals (TK cross down only)
- HOLD signals (neutral conditions)
- Signal strength calculations (0.5 for weak, 0.9 for strong)
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


class TestIchimokuStrongBuySignals:
    """Test strong BUY signal generation for Ichimoku strategy."""

    def test_strong_buy_signal_all_conditions_met(self, signal_generator):
        """Test strong BUY signal when all bullish conditions are met."""
        parameters = {}
        indicators = {
            'current_price': 110.0,
            'tenkan_sen_current': 102.0,
            'kijun_sen_current': 100.0,
            'tenkan_sen_prev': 99.0,
            'kijun_sen_prev': 100.0,
            'cloud_top_current': 105.0,
            'cloud_bottom_current': 95.0,
            'future_senkou_a_current': 108.0,
            'future_senkou_b_current': 106.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_ichimoku_signal(
            parameters, indicators, has_position=False
        )

        assert signal == SignalType.BUY
        assert strength == 0.9  # Strong signal
        assert 'strong bullish' in reasoning.lower()
        assert 'tk cross up' in reasoning.lower()
        assert 'price above cloud' in reasoning.lower()
        assert 'bullish future cloud' in reasoning.lower()

    def test_strong_buy_price_just_above_cloud(self, signal_generator):
        """Test strong BUY with price just above cloud top."""
        parameters = {}
        indicators = {
            'current_price': 105.1,  # Just above cloud
            'tenkan_sen_current': 102.0,
            'kijun_sen_current': 100.0,
            'tenkan_sen_prev': 99.0,
            'kijun_sen_prev': 100.0,
            'cloud_top_current': 105.0,
            'cloud_bottom_current': 95.0,
            'future_senkou_a_current': 108.0,
            'future_senkou_b_current': 106.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_ichimoku_signal(
            parameters, indicators, has_position=False
        )

        assert signal == SignalType.BUY
        assert strength == 0.9

    def test_strong_buy_future_cloud_barely_bullish(self, signal_generator):
        """Test strong BUY with future cloud barely bullish."""
        parameters = {}
        indicators = {
            'current_price': 110.0,
            'tenkan_sen_current': 102.0,
            'kijun_sen_current': 100.0,
            'tenkan_sen_prev': 99.0,
            'kijun_sen_prev': 100.0,
            'cloud_top_current': 105.0,
            'cloud_bottom_current': 95.0,
            'future_senkou_a_current': 106.01,  # Just above
            'future_senkou_b_current': 106.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_ichimoku_signal(
            parameters, indicators, has_position=False
        )

        assert signal == SignalType.BUY
        assert strength == 0.9

    def test_no_strong_buy_when_has_position(self, signal_generator):
        """Test no strong BUY signal when already has position."""
        parameters = {}
        indicators = {
            'current_price': 110.0,
            'tenkan_sen_current': 102.0,
            'kijun_sen_current': 100.0,
            'tenkan_sen_prev': 99.0,
            'kijun_sen_prev': 100.0,
            'cloud_top_current': 105.0,
            'cloud_bottom_current': 95.0,
            'future_senkou_a_current': 108.0,
            'future_senkou_b_current': 106.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_ichimoku_signal(
            parameters, indicators, has_position=True  # Has position
        )

        assert signal == SignalType.HOLD
        assert strength == 0.0


class TestIchimokuWeakBuySignals:
    """Test weak BUY signal generation for Ichimoku strategy."""

    def test_weak_buy_signal_tk_cross_only(self, signal_generator):
        """Test weak BUY signal with TK cross but no other conditions."""
        parameters = {}
        indicators = {
            'current_price': 98.0,  # Below cloud
            'tenkan_sen_current': 102.0,
            'kijun_sen_current': 100.0,
            'tenkan_sen_prev': 99.0,
            'kijun_sen_prev': 100.0,
            'cloud_top_current': 105.0,
            'cloud_bottom_current': 95.0,
            'future_senkou_a_current': 106.0,
            'future_senkou_b_current': 108.0  # Bearish future
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_ichimoku_signal(
            parameters, indicators, has_position=False
        )

        assert signal == SignalType.BUY
        assert strength == 0.5  # Weak signal
        assert 'weak bullish' in reasoning.lower()
        assert 'tk cross up' in reasoning.lower()
        assert signal_indicators['tenkan_sen'] == 102.0
        assert signal_indicators['kijun_sen'] == 100.0

    def test_weak_buy_price_in_cloud(self, signal_generator):
        """Test weak BUY when price is inside cloud."""
        parameters = {}
        indicators = {
            'current_price': 100.0,  # Inside cloud
            'tenkan_sen_current': 102.0,
            'kijun_sen_current': 100.0,
            'tenkan_sen_prev': 99.0,
            'kijun_sen_prev': 100.0,
            'cloud_top_current': 105.0,
            'cloud_bottom_current': 95.0,
            'future_senkou_a_current': 108.0,
            'future_senkou_b_current': 106.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_ichimoku_signal(
            parameters, indicators, has_position=False
        )

        assert signal == SignalType.BUY
        assert strength == 0.5  # Weak (not above cloud)

    def test_weak_buy_future_cloud_bearish(self, signal_generator):
        """Test weak BUY when future cloud is bearish."""
        parameters = {}
        indicators = {
            'current_price': 110.0,  # Above cloud
            'tenkan_sen_current': 102.0,
            'kijun_sen_current': 100.0,
            'tenkan_sen_prev': 99.0,
            'kijun_sen_prev': 100.0,
            'cloud_top_current': 105.0,
            'cloud_bottom_current': 95.0,
            'future_senkou_a_current': 106.0,
            'future_senkou_b_current': 108.0  # Bearish future
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_ichimoku_signal(
            parameters, indicators, has_position=False
        )

        assert signal == SignalType.BUY
        assert strength == 0.5  # Weak (bearish future cloud)


class TestIchimokuStrongSellSignals:
    """Test strong SELL signal generation for Ichimoku strategy."""

    def test_strong_sell_signal_all_conditions_met(self, signal_generator):
        """Test strong SELL signal when all bearish conditions are met."""
        parameters = {}
        indicators = {
            'current_price': 90.0,
            'tenkan_sen_current': 98.0,
            'kijun_sen_current': 100.0,
            'tenkan_sen_prev': 101.0,
            'kijun_sen_prev': 100.0,
            'cloud_top_current': 105.0,
            'cloud_bottom_current': 95.0,
            'future_senkou_a_current': 96.0,
            'future_senkou_b_current': 98.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_ichimoku_signal(
            parameters, indicators, has_position=True
        )

        assert signal == SignalType.SELL
        assert strength == 0.9  # Strong signal
        assert 'strong bearish' in reasoning.lower()
        assert 'tk cross down' in reasoning.lower()
        assert 'price below cloud' in reasoning.lower()
        assert 'bearish future cloud' in reasoning.lower()

    def test_strong_sell_price_just_below_cloud(self, signal_generator):
        """Test strong SELL with price just below cloud bottom."""
        parameters = {}
        indicators = {
            'current_price': 94.9,  # Just below cloud
            'tenkan_sen_current': 98.0,
            'kijun_sen_current': 100.0,
            'tenkan_sen_prev': 101.0,
            'kijun_sen_prev': 100.0,
            'cloud_top_current': 105.0,
            'cloud_bottom_current': 95.0,
            'future_senkou_a_current': 96.0,
            'future_senkou_b_current': 98.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_ichimoku_signal(
            parameters, indicators, has_position=True
        )

        assert signal == SignalType.SELL
        assert strength == 0.9

    def test_strong_sell_future_cloud_barely_bearish(self, signal_generator):
        """Test strong SELL with future cloud barely bearish."""
        parameters = {}
        indicators = {
            'current_price': 90.0,
            'tenkan_sen_current': 98.0,
            'kijun_sen_current': 100.0,
            'tenkan_sen_prev': 101.0,
            'kijun_sen_prev': 100.0,
            'cloud_top_current': 105.0,
            'cloud_bottom_current': 95.0,
            'future_senkou_a_current': 96.0,
            'future_senkou_b_current': 96.01  # Just above
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_ichimoku_signal(
            parameters, indicators, has_position=True
        )

        assert signal == SignalType.SELL
        assert strength == 0.9

    def test_no_strong_sell_when_no_position(self, signal_generator):
        """Test no strong SELL signal when no position."""
        parameters = {}
        indicators = {
            'current_price': 90.0,
            'tenkan_sen_current': 98.0,
            'kijun_sen_current': 100.0,
            'tenkan_sen_prev': 101.0,
            'kijun_sen_prev': 100.0,
            'cloud_top_current': 105.0,
            'cloud_bottom_current': 95.0,
            'future_senkou_a_current': 96.0,
            'future_senkou_b_current': 98.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_ichimoku_signal(
            parameters, indicators, has_position=False  # No position
        )

        assert signal == SignalType.HOLD
        assert strength == 0.0


class TestIchimokuWeakSellSignals:
    """Test weak SELL signal generation for Ichimoku strategy."""

    def test_weak_sell_signal_tk_cross_only(self, signal_generator):
        """Test weak SELL signal with TK cross but no other conditions."""
        parameters = {}
        indicators = {
            'current_price': 110.0,  # Above cloud
            'tenkan_sen_current': 98.0,
            'kijun_sen_current': 100.0,
            'tenkan_sen_prev': 101.0,
            'kijun_sen_prev': 100.0,
            'cloud_top_current': 105.0,
            'cloud_bottom_current': 95.0,
            'future_senkou_a_current': 108.0,
            'future_senkou_b_current': 106.0  # Bullish future
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_ichimoku_signal(
            parameters, indicators, has_position=True
        )

        assert signal == SignalType.SELL
        assert strength == 0.5  # Weak signal
        assert 'weak bearish' in reasoning.lower()
        assert 'tk cross down' in reasoning.lower()

    def test_weak_sell_price_in_cloud(self, signal_generator):
        """Test weak SELL when price is inside cloud."""
        parameters = {}
        indicators = {
            'current_price': 100.0,  # Inside cloud
            'tenkan_sen_current': 98.0,
            'kijun_sen_current': 100.0,
            'tenkan_sen_prev': 101.0,
            'kijun_sen_prev': 100.0,
            'cloud_top_current': 105.0,
            'cloud_bottom_current': 95.0,
            'future_senkou_a_current': 96.0,
            'future_senkou_b_current': 98.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_ichimoku_signal(
            parameters, indicators, has_position=True
        )

        assert signal == SignalType.SELL
        assert strength == 0.5  # Weak (not below cloud)

    def test_weak_sell_future_cloud_bullish(self, signal_generator):
        """Test weak SELL when future cloud is bullish."""
        parameters = {}
        indicators = {
            'current_price': 90.0,  # Below cloud
            'tenkan_sen_current': 98.0,
            'kijun_sen_current': 100.0,
            'tenkan_sen_prev': 101.0,
            'kijun_sen_prev': 100.0,
            'cloud_top_current': 105.0,
            'cloud_bottom_current': 95.0,
            'future_senkou_a_current': 108.0,
            'future_senkou_b_current': 106.0  # Bullish future
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_ichimoku_signal(
            parameters, indicators, has_position=True
        )

        assert signal == SignalType.SELL
        assert strength == 0.5  # Weak (bullish future cloud)


class TestIchimokuHoldSignals:
    """Test HOLD signal generation for Ichimoku strategy."""

    def test_hold_signal_no_tk_crossover(self, signal_generator):
        """Test HOLD signal when no TK crossover occurs."""
        parameters = {}
        indicators = {
            'current_price': 100.0,
            'tenkan_sen_current': 102.0,
            'kijun_sen_current': 100.0,
            'tenkan_sen_prev': 103.0,  # Was already above
            'kijun_sen_prev': 100.0,
            'cloud_top_current': 105.0,
            'cloud_bottom_current': 95.0,
            'future_senkou_a_current': 108.0,
            'future_senkou_b_current': 106.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_ichimoku_signal(
            parameters, indicators, has_position=False
        )

        assert signal == SignalType.HOLD
        assert strength == 0.0

    def test_hold_signal_price_above_cloud_neutral(self, signal_generator):
        """Test HOLD with price above cloud but no crossover (bullish bias)."""
        parameters = {}
        indicators = {
            'current_price': 110.0,  # Above cloud
            'tenkan_sen_current': 102.0,
            'kijun_sen_current': 100.0,
            'tenkan_sen_prev': 103.0,
            'kijun_sen_prev': 100.0,
            'cloud_top_current': 105.0,
            'cloud_bottom_current': 95.0,
            'future_senkou_a_current': 108.0,
            'future_senkou_b_current': 106.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_ichimoku_signal(
            parameters, indicators, has_position=False
        )

        assert signal == SignalType.HOLD
        assert strength == 0.0
        assert 'bullish' in reasoning.lower()  # Shows bias

    def test_hold_signal_price_below_cloud_neutral(self, signal_generator):
        """Test HOLD with price below cloud but no crossover (bearish bias)."""
        parameters = {}
        indicators = {
            'current_price': 90.0,  # Below cloud
            'tenkan_sen_current': 98.0,
            'kijun_sen_current': 100.0,
            'tenkan_sen_prev': 97.0,
            'kijun_sen_prev': 100.0,
            'cloud_top_current': 105.0,
            'cloud_bottom_current': 95.0,
            'future_senkou_a_current': 96.0,
            'future_senkou_b_current': 98.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_ichimoku_signal(
            parameters, indicators, has_position=False
        )

        assert signal == SignalType.HOLD
        assert strength == 0.0
        assert 'bearish' in reasoning.lower()  # Shows bias

    def test_hold_signal_price_in_cloud_neutral(self, signal_generator):
        """Test HOLD with price in cloud but no crossover (neutral bias)."""
        parameters = {}
        indicators = {
            'current_price': 100.0,  # In cloud
            'tenkan_sen_current': 102.0,
            'kijun_sen_current': 100.0,
            'tenkan_sen_prev': 103.0,
            'kijun_sen_prev': 100.0,
            'cloud_top_current': 105.0,
            'cloud_bottom_current': 95.0,
            'future_senkou_a_current': 108.0,
            'future_senkou_b_current': 106.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_ichimoku_signal(
            parameters, indicators, has_position=False
        )

        assert signal == SignalType.HOLD
        assert strength == 0.0
        assert 'neutral' in reasoning.lower()


class TestIchimokuTKCrossDetection:
    """Test Tenkan-Kijun crossover detection logic."""

    def test_tk_cross_up_exact(self, signal_generator):
        """Test exact TK cross up detection."""
        parameters = {}
        indicators = {
            'current_price': 100.0,
            'tenkan_sen_current': 100.01,
            'kijun_sen_current': 100.0,
            'tenkan_sen_prev': 99.99,
            'kijun_sen_prev': 100.0,
            'cloud_top_current': 105.0,
            'cloud_bottom_current': 95.0,
            'future_senkou_a_current': 108.0,
            'future_senkou_b_current': 106.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_ichimoku_signal(
            parameters, indicators, has_position=False
        )

        assert signal == SignalType.BUY
        assert strength == 0.5  # Weak (price in cloud)

    def test_tk_cross_down_exact(self, signal_generator):
        """Test exact TK cross down detection."""
        parameters = {}
        indicators = {
            'current_price': 100.0,
            'tenkan_sen_current': 99.99,
            'kijun_sen_current': 100.0,
            'tenkan_sen_prev': 100.01,
            'kijun_sen_prev': 100.0,
            'cloud_top_current': 105.0,
            'cloud_bottom_current': 95.0,
            'future_senkou_a_current': 96.0,
            'future_senkou_b_current': 98.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_ichimoku_signal(
            parameters, indicators, has_position=True
        )

        assert signal == SignalType.SELL
        assert strength == 0.5  # Weak (price in cloud)

    def test_no_cross_tenkan_equals_kijun(self, signal_generator):
        """Test no crossover when Tenkan equals Kijun."""
        parameters = {}
        indicators = {
            'current_price': 100.0,
            'tenkan_sen_current': 100.0,  # Equal
            'kijun_sen_current': 100.0,
            'tenkan_sen_prev': 100.0,
            'kijun_sen_prev': 100.0,
            'cloud_top_current': 105.0,
            'cloud_bottom_current': 95.0,
            'future_senkou_a_current': 108.0,
            'future_senkou_b_current': 106.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_ichimoku_signal(
            parameters, indicators, has_position=False
        )

        assert signal == SignalType.HOLD
        assert strength == 0.0


class TestIchimokuEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_missing_indicator_defaults(self, signal_generator):
        """Test default values when indicators are missing."""
        parameters = {}
        indicators = {
            'current_price': 100.0
            # All other indicators missing
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_ichimoku_signal(
            parameters, indicators, has_position=False
        )

        # Should use price as defaults, resulting in HOLD
        assert signal == SignalType.HOLD
        assert strength == 0.0

    def test_price_equals_cloud_top(self, signal_generator):
        """Test when price exactly equals cloud top."""
        parameters = {}
        indicators = {
            'current_price': 105.0,  # Equals cloud top
            'tenkan_sen_current': 102.0,
            'kijun_sen_current': 100.0,
            'tenkan_sen_prev': 99.0,
            'kijun_sen_prev': 100.0,
            'cloud_top_current': 105.0,
            'cloud_bottom_current': 95.0,
            'future_senkou_a_current': 108.0,
            'future_senkou_b_current': 106.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_ichimoku_signal(
            parameters, indicators, has_position=False
        )

        # Price = cloud_top, not above
        assert signal == SignalType.BUY
        assert strength == 0.5  # Weak (not above cloud)

    def test_price_equals_cloud_bottom(self, signal_generator):
        """Test when price exactly equals cloud bottom."""
        parameters = {}
        indicators = {
            'current_price': 95.0,  # Equals cloud bottom
            'tenkan_sen_current': 98.0,
            'kijun_sen_current': 100.0,
            'tenkan_sen_prev': 101.0,
            'kijun_sen_prev': 100.0,
            'cloud_top_current': 105.0,
            'cloud_bottom_current': 95.0,
            'future_senkou_a_current': 96.0,
            'future_senkou_b_current': 98.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_ichimoku_signal(
            parameters, indicators, has_position=True
        )

        # Price = cloud_bottom, not below
        assert signal == SignalType.SELL
        assert strength == 0.5  # Weak (not below cloud)

    def test_inverted_cloud(self, signal_generator):
        """Test with inverted cloud (cloud_bottom > cloud_top)."""
        parameters = {}
        indicators = {
            'current_price': 100.0,
            'tenkan_sen_current': 102.0,
            'kijun_sen_current': 100.0,
            'tenkan_sen_prev': 99.0,
            'kijun_sen_prev': 100.0,
            'cloud_top_current': 95.0,  # Inverted
            'cloud_bottom_current': 105.0,
            'future_senkou_a_current': 108.0,
            'future_senkou_b_current': 106.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_ichimoku_signal(
            parameters, indicators, has_position=False
        )

        # Price (100) > cloud_top (95), so considered above
        assert signal == SignalType.BUY
        assert strength == 0.9  # Strong (meets all conditions)

    def test_future_cloud_equal(self, signal_generator):
        """Test when future Senkou A equals Senkou B."""
        parameters = {}
        indicators = {
            'current_price': 110.0,
            'tenkan_sen_current': 102.0,
            'kijun_sen_current': 100.0,
            'tenkan_sen_prev': 99.0,
            'kijun_sen_prev': 100.0,
            'cloud_top_current': 105.0,
            'cloud_bottom_current': 95.0,
            'future_senkou_a_current': 107.0,
            'future_senkou_b_current': 107.0  # Equal
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_ichimoku_signal(
            parameters, indicators, has_position=False
        )

        # Not bullish (needs A > B)
        assert signal == SignalType.BUY
        assert strength == 0.5  # Weak (future cloud not bullish)

    def test_zero_values(self, signal_generator):
        """Test with zero indicator values."""
        parameters = {}
        indicators = {
            'current_price': 0.0,
            'tenkan_sen_current': 0.0,
            'kijun_sen_current': 0.0,
            'tenkan_sen_prev': 0.0,
            'kijun_sen_prev': 0.0,
            'cloud_top_current': 0.0,
            'cloud_bottom_current': 0.0,
            'future_senkou_a_current': 0.0,
            'future_senkou_b_current': 0.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_ichimoku_signal(
            parameters, indicators, has_position=False
        )

        # No crossover with all zeros
        assert signal == SignalType.HOLD
        assert strength == 0.0

    def test_signal_indicators_completeness(self, signal_generator):
        """Test that signal_indicators dict contains all required fields."""
        parameters = {}
        indicators = {
            'current_price': 110.0,
            'tenkan_sen_current': 102.0,
            'kijun_sen_current': 100.0,
            'tenkan_sen_prev': 99.0,
            'kijun_sen_prev': 100.0,
            'cloud_top_current': 105.0,
            'cloud_bottom_current': 95.0,
            'future_senkou_a_current': 108.0,
            'future_senkou_b_current': 106.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_ichimoku_signal(
            parameters, indicators, has_position=False
        )

        assert 'tenkan_sen' in signal_indicators
        assert 'kijun_sen' in signal_indicators
        assert 'cloud_top' in signal_indicators
        assert 'cloud_bottom' in signal_indicators
        assert 'current_price' in signal_indicators

    def test_reasoning_contains_values(self, signal_generator):
        """Test that reasoning string contains actual values."""
        parameters = {}
        indicators = {
            'current_price': 110.0,
            'tenkan_sen_current': 102.0,
            'kijun_sen_current': 100.0,
            'tenkan_sen_prev': 99.0,
            'kijun_sen_prev': 100.0,
            'cloud_top_current': 105.0,
            'cloud_bottom_current': 95.0,
            'future_senkou_a_current': 108.0,
            'future_senkou_b_current': 106.0
        }

        signal, strength, reasoning, signal_indicators = signal_generator._generate_ichimoku_signal(
            parameters, indicators, has_position=False
        )

        assert isinstance(reasoning, str)
        assert len(reasoning) > 0
        # Strong buy should mention all conditions
        assert 'tk cross' in reasoning.lower() or 'bullish' in reasoning.lower()


class TestIchimokuLogging:
    """Test logging behavior for Ichimoku signals."""

    @patch('app.strategies.signal_generator.logger')
    def test_strong_buy_signal_logging(self, mock_logger, signal_generator):
        """Test that strong BUY signals are logged."""
        parameters = {}
        indicators = {
            'current_price': 110.0,
            'tenkan_sen_current': 102.0,
            'kijun_sen_current': 100.0,
            'tenkan_sen_prev': 99.0,
            'kijun_sen_prev': 100.0,
            'cloud_top_current': 105.0,
            'cloud_bottom_current': 95.0,
            'future_senkou_a_current': 108.0,
            'future_senkou_b_current': 106.0
        }

        signal_generator._generate_ichimoku_signal(parameters, indicators, has_position=False)

        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args[0][0]
        assert 'ICHIMOKU BUY signal' in call_args

    @patch('app.strategies.signal_generator.logger')
    def test_weak_buy_signal_logging(self, mock_logger, signal_generator):
        """Test that weak BUY signals are logged."""
        parameters = {}
        indicators = {
            'current_price': 98.0,
            'tenkan_sen_current': 102.0,
            'kijun_sen_current': 100.0,
            'tenkan_sen_prev': 99.0,
            'kijun_sen_prev': 100.0,
            'cloud_top_current': 105.0,
            'cloud_bottom_current': 95.0,
            'future_senkou_a_current': 106.0,
            'future_senkou_b_current': 108.0
        }

        signal_generator._generate_ichimoku_signal(parameters, indicators, has_position=False)

        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args[0][0]
        assert 'ICHIMOKU BUY signal' in call_args

    @patch('app.strategies.signal_generator.logger')
    def test_strong_sell_signal_logging(self, mock_logger, signal_generator):
        """Test that strong SELL signals are logged."""
        parameters = {}
        indicators = {
            'current_price': 90.0,
            'tenkan_sen_current': 98.0,
            'kijun_sen_current': 100.0,
            'tenkan_sen_prev': 101.0,
            'kijun_sen_prev': 100.0,
            'cloud_top_current': 105.0,
            'cloud_bottom_current': 95.0,
            'future_senkou_a_current': 96.0,
            'future_senkou_b_current': 98.0
        }

        signal_generator._generate_ichimoku_signal(parameters, indicators, has_position=True)

        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args[0][0]
        assert 'ICHIMOKU SELL signal' in call_args

    @patch('app.strategies.signal_generator.logger')
    def test_weak_sell_signal_logging(self, mock_logger, signal_generator):
        """Test that weak SELL signals are logged."""
        parameters = {}
        indicators = {
            'current_price': 110.0,
            'tenkan_sen_current': 98.0,
            'kijun_sen_current': 100.0,
            'tenkan_sen_prev': 101.0,
            'kijun_sen_prev': 100.0,
            'cloud_top_current': 105.0,
            'cloud_bottom_current': 95.0,
            'future_senkou_a_current': 108.0,
            'future_senkou_b_current': 106.0
        }

        signal_generator._generate_ichimoku_signal(parameters, indicators, has_position=True)

        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args[0][0]
        assert 'ICHIMOKU SELL signal' in call_args
