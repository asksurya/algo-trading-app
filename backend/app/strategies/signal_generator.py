"""
Signal generation logic for trading strategies.
Generates BUY/SELL/HOLD signals based on technical indicators and strategy rules.
"""
import logging
from typing import Dict, Any, Optional, Tuple
from enum import Enum
import pandas as pd

from app.strategies.indicators import TechnicalIndicators
from app.models.strategy_execution import SignalType

logger = logging.getLogger(__name__)


class SignalStrength(Enum):
    """Signal strength levels."""
    WEAK = 0.3
    MODERATE = 0.6
    STRONG = 0.8
    VERY_STRONG = 1.0


class SignalGenerator:
    """
    Generates trading signals based on technical indicators and strategy rules.
    """
    
    def __init__(self):
        """Initialize signal generator."""
        self.indicators = TechnicalIndicators()
    
    def generate_signal(
        self,
        strategy_type: str,
        parameters: Dict[str, Any],
        bars: list,
        has_position: bool = False
    ) -> Tuple[SignalType, float, str, Dict[str, Any]]:
        """
        Generate trading signal for a strategy.
        
        Args:
            strategy_type: Type of strategy
            parameters: Strategy parameters
            bars: Historical bar data
            has_position: Whether strategy currently has an open position
            
        Returns:
            Tuple of (signal_type, signal_strength, reasoning, indicator_values)
        """
        # Prepare data
        df = self.indicators.prepare_dataframe(bars)
        
        # Calculate indicators
        indicator_values = self.indicators.calculate_all_for_strategy(
            df, strategy_type, parameters
        )
        
        # Generate signal based on strategy type
        strategy_type_upper = strategy_type.upper()
        
        if strategy_type_upper == 'RSI':
            return self._generate_rsi_signal(parameters, indicator_values, has_position)
        elif strategy_type_upper == 'MACD':
            return self._generate_macd_signal(parameters, indicator_values, has_position)
        elif strategy_type_upper == 'SMA_CROSSOVER':
            return self._generate_sma_crossover_signal(parameters, indicator_values, has_position, df)
        elif strategy_type_upper == 'BOLLINGER_BANDS':
            return self._generate_bollinger_signal(parameters, indicator_values, has_position)
        elif strategy_type_upper == 'MEAN_REVERSION':
            return self._generate_mean_reversion_signal(parameters, indicator_values, has_position)
        else:
            raise ValueError(f"Unknown strategy type: {strategy_type}")
    
    def _generate_rsi_signal(
        self,
        parameters: Dict[str, Any],
        indicators: Dict[str, Any],
        has_position: bool
    ) -> Tuple[SignalType, float, str, Dict[str, Any]]:
        """
        Generate RSI strategy signal.
        
        RSI Strategy:
        - Buy when RSI < oversold_threshold (default 30)
        - Sell when RSI > overbought_threshold (default 70)
        """
        rsi = indicators['rsi_current']
        oversold = parameters.get('oversold_threshold', 30)
        overbought = parameters.get('overbought_threshold', 70)
        
        # Extract relevant indicators
        signal_indicators = {
            'rsi': rsi,
            'oversold_threshold': oversold,
            'overbought_threshold': overbought,
            'current_price': indicators['current_price']
        }
        
        # Buy signal
        if rsi < oversold and not has_position:
            strength = self._calculate_rsi_strength(rsi, oversold, 'buy')
            reasoning = f"RSI ({rsi:.2f}) is below oversold threshold ({oversold}), indicating potential upward reversal"
            logger.info(f"RSI BUY signal: {reasoning}")
            return SignalType.BUY, strength, reasoning, signal_indicators
        
        # Sell signal
        elif rsi > overbought and has_position:
            strength = self._calculate_rsi_strength(rsi, overbought, 'sell')
            reasoning = f"RSI ({rsi:.2f}) is above overbought threshold ({overbought}), indicating potential downward reversal"
            logger.info(f"RSI SELL signal: {reasoning}")
            return SignalType.SELL, strength, reasoning, signal_indicators
        
        # Hold signal
        else:
            reasoning = f"RSI ({rsi:.2f}) is in neutral range ({oversold}-{overbought})"
            return SignalType.HOLD, 0.0, reasoning, signal_indicators
    
    def _generate_macd_signal(
        self,
        parameters: Dict[str, Any],
        indicators: Dict[str, Any],
        has_position: bool
    ) -> Tuple[SignalType, float, str, Dict[str, Any]]:
        """
        Generate MACD strategy signal.
        
        MACD Strategy:
        - Buy when MACD crosses above signal line (bullish crossover)
        - Sell when MACD crosses below signal line (bearish crossover)
        """
        macd = indicators['macd_current']
        signal = indicators['signal_current']
        histogram = indicators['histogram_current']
        
        signal_indicators = {
            'macd': macd,
            'macd_signal': signal,
            'histogram': histogram,
            'current_price': indicators['current_price']
        }
        
        # Detect crossover (histogram changes sign)
        # Positive histogram and recently crossed = bullish
        if histogram > 0 and macd > signal and not has_position:
            strength = min(abs(histogram) * 10, 1.0)  # Normalize histogram to 0-1
            reasoning = f"MACD ({macd:.4f}) crossed above signal line ({signal:.4f}), bullish crossover detected"
            logger.info(f"MACD BUY signal: {reasoning}")
            return SignalType.BUY, strength, reasoning, signal_indicators
        
        # Negative histogram and recently crossed = bearish
        elif histogram < 0 and macd < signal and has_position:
            strength = min(abs(histogram) * 10, 1.0)
            reasoning = f"MACD ({macd:.4f}) crossed below signal line ({signal:.4f}), bearish crossover detected"
            logger.info(f"MACD SELL signal: {reasoning}")
            return SignalType.SELL, strength, reasoning, signal_indicators
        
        else:
            reasoning = f"MACD ({macd:.4f}) no crossover detected, histogram: {histogram:.4f}"
            return SignalType.HOLD, 0.0, reasoning, signal_indicators
    
    def _generate_sma_crossover_signal(
        self,
        parameters: Dict[str, Any],
        indicators: Dict[str, Any],
        has_position: bool,
        df: pd.DataFrame
    ) -> Tuple[SignalType, float, str, Dict[str, Any]]:
        """
        Generate SMA crossover strategy signal.
        
        SMA Crossover Strategy:
        - Buy when fast SMA crosses above slow SMA (golden cross)
        - Sell when fast SMA crosses below slow SMA (death cross)
        """
        fast_sma = indicators['fast_sma_current']
        slow_sma = indicators['slow_sma_current']
        
        signal_indicators = {
            'fast_sma': fast_sma,
            'slow_sma': slow_sma,
            'current_price': indicators['current_price']
        }
        
        # Detect crossover
        crossover = self.indicators.get_crossover_signal(
            indicators['fast_sma'],
            indicators['slow_sma']
        )
        
        # Golden cross (bullish)
        if crossover == 'bullish' and not has_position:
            distance_pct = ((fast_sma - slow_sma) / slow_sma) * 100
            strength = min(abs(distance_pct) * 5, 1.0)  # Normalize
            reasoning = f"Golden Cross: Fast SMA ({fast_sma:.2f}) crossed above Slow SMA ({slow_sma:.2f})"
            logger.info(f"SMA Crossover BUY signal: {reasoning}")
            return SignalType.BUY, strength, reasoning, signal_indicators
        
        # Death cross (bearish)
        elif crossover == 'bearish' and has_position:
            distance_pct = ((slow_sma - fast_sma) / slow_sma) * 100
            strength = min(abs(distance_pct) * 5, 1.0)
            reasoning = f"Death Cross: Fast SMA ({fast_sma:.2f}) crossed below Slow SMA ({slow_sma:.2f})"
            logger.info(f"SMA Crossover SELL signal: {reasoning}")
            return SignalType.SELL, strength, reasoning, signal_indicators
        
        else:
            reasoning = f"No SMA crossover detected. Fast: {fast_sma:.2f}, Slow: {slow_sma:.2f}"
            return SignalType.HOLD, 0.0, reasoning, signal_indicators
    
    def _generate_bollinger_signal(
        self,
        parameters: Dict[str, Any],
        indicators: Dict[str, Any],
        has_position: bool
    ) -> Tuple[SignalType, float, str, Dict[str, Any]]:
        """
        Generate Bollinger Bands strategy signal.
        
        Bollinger Bands Strategy:
        - Buy when price touches or goes below lower band (oversold)
        - Sell when price touches or goes above upper band (overbought)
        """
        price = indicators['current_price']
        upper = indicators['bb_upper_current']
        middle = indicators['bb_middle_current']
        lower = indicators['bb_lower_current']
        
        signal_indicators = {
            'bb_upper': upper,
            'bb_middle': middle,
            'bb_lower': lower,
            'current_price': price
        }
        
        band_width = upper - lower
        touch_threshold = parameters.get('touch_threshold', 0.01)  # 1% threshold
        
        # Buy signal - price at or below lower band
        if price <= lower * (1 + touch_threshold) and not has_position:
            distance_from_middle = abs(price - middle) / band_width
            strength = min(distance_from_middle * 2, 1.0)
            reasoning = f"Price ({price:.2f}) touched lower Bollinger Band ({lower:.2f}), potential bounce"
            logger.info(f"Bollinger Bands BUY signal: {reasoning}")
            return SignalType.BUY, strength, reasoning, signal_indicators
        
        # Sell signal - price at or above upper band
        elif price >= upper * (1 - touch_threshold) and has_position:
            distance_from_middle = abs(price - middle) / band_width
            strength = min(distance_from_middle * 2, 1.0)
            reasoning = f"Price ({price:.2f}) touched upper Bollinger Band ({upper:.2f}), potential reversal"
            logger.info(f"Bollinger Bands SELL signal: {reasoning}")
            return SignalType.SELL, strength, reasoning, signal_indicators
        
        else:
            reasoning = f"Price ({price:.2f}) within bands. Lower: {lower:.2f}, Middle: {middle:.2f}, Upper: {upper:.2f}"
            return SignalType.HOLD, 0.0, reasoning, signal_indicators
    
    def _generate_mean_reversion_signal(
        self,
        parameters: Dict[str, Any],
        indicators: Dict[str, Any],
        has_position: bool
    ) -> Tuple[SignalType, float, str, Dict[str, Any]]:
        """
        Generate Mean Reversion strategy signal.
        
        Mean Reversion Strategy:
        - Buy when price is N standard deviations below moving average (oversold)
        - Sell when price returns to moving average (mean reversion complete)
        """
        price = indicators['current_price']
        sma = indicators['sma_current']
        z_score = indicators['z_score_current']
        std_dev_threshold = parameters.get('std_dev', 2.0)
        
        signal_indicators = {
            'sma': sma,
            'z_score': z_score,
            'std_dev_threshold': std_dev_threshold,
            'current_price': price
        }
        
        # Buy signal - price is N std devs below mean (oversold)
        if z_score <= -std_dev_threshold and not has_position:
            strength = min(abs(z_score) / 3.0, 1.0)  # Normalize (3 sigma = max)
            distance_pct = ((sma - price) / sma) * 100
            reasoning = f"Price ({price:.2f}) is {abs(z_score):.2f} std devs below SMA ({sma:.2f}), {distance_pct:.2f}% below mean"
            logger.info(f"Mean Reversion BUY signal: {reasoning}")
            return SignalType.BUY, strength, reasoning, signal_indicators
        
        # Sell signal - price has reverted to mean (or above)
        elif has_position and z_score >= -0.5:  # Close to or above mean
            strength = 0.7  # Moderate strength for mean reversion exit
            reasoning = f"Price ({price:.2f}) reverted to mean (SMA: {sma:.2f}), z-score: {z_score:.2f}"
            logger.info(f"Mean Reversion SELL signal: {reasoning}")
            return SignalType.SELL, strength, reasoning, signal_indicators
        
        else:
            reasoning = f"Price ({price:.2f}) z-score ({z_score:.2f}) not at extreme. SMA: {sma:.2f}"
            return SignalType.HOLD, 0.0, reasoning, signal_indicators
    
    @staticmethod
    def _calculate_rsi_strength(rsi: float, threshold: float, signal_type: str) -> float:
        """
        Calculate signal strength based on RSI distance from threshold.
        
        Args:
            rsi: Current RSI value
            threshold: Threshold value (oversold or overbought)
            signal_type: 'buy' or 'sell'
            
        Returns:
            Signal strength (0.0-1.0)
        """
        if signal_type == 'buy':
            # Stronger signal the further below oversold threshold
            distance = threshold - rsi
            strength = min(distance / 15.0, 1.0)  # Normalize (15 points = max)
        else:  # sell
            # Stronger signal the further above overbought threshold
            distance = rsi - threshold
            strength = min(distance / 15.0, 1.0)
        
        return max(0.3, strength)  # Minimum 0.3 strength
    
    def validate_signal(
        self,
        signal_type: SignalType,
        has_position: bool,
        trades_today: int,
        max_trades_per_day: int,
        loss_today: float,
        max_loss_per_day: float,
        consecutive_losses: int,
        max_consecutive_losses: int
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate if a signal should be executed based on risk management rules.
        
        Args:
            signal_type: Type of signal (BUY/SELL/HOLD)
            has_position: Whether strategy has an open position
            trades_today: Number of trades executed today
            max_trades_per_day: Maximum allowed trades per day
            loss_today: Total loss today
            max_loss_per_day: Maximum allowed loss per day
            consecutive_losses: Number of consecutive losing trades
            max_consecutive_losses: Maximum allowed consecutive losses
            
        Returns:
            Tuple of (is_valid, rejection_reason)
        """
        # HOLD signals are always valid (no action)
        if signal_type == SignalType.HOLD:
            return True, None
        
        # Check if we can open new positions (BUY signals)
        if signal_type == SignalType.BUY:
            if has_position:
                return False, "Already have an open position"
            
            # Check circuit breakers
            if trades_today >= max_trades_per_day:
                return False, f"Max trades per day reached ({max_trades_per_day})"
            
            if loss_today >= max_loss_per_day:
                return False, f"Max loss per day reached (${loss_today:.2f}/${max_loss_per_day:.2f})"
            
            if consecutive_losses >= max_consecutive_losses:
                return False, f"Max consecutive losses reached ({consecutive_losses})"
        
        # Check if we can close positions (SELL signals)
        elif signal_type == SignalType.SELL:
            if not has_position:
                return False, "No open position to close"
        
        return True, None
    
    def should_execute_now(
        self,
        strategy_type: str,
        timeframe: str,
        last_evaluated_at: Optional[Any]
    ) -> bool:
        """
        Determine if a strategy should be evaluated based on its timeframe.
        
        Args:
            strategy_type: Type of strategy
            timeframe: Strategy timeframe (1m, 5m, 15m, 1h, etc.)
            last_evaluated_at: Last evaluation timestamp
            
        Returns:
            True if strategy should be evaluated now
        """
        # For now, evaluate all strategies (scheduler runs every minute)
        # In the future, can add logic to skip evaluations based on timeframe
        # E.g., 5m strategies only evaluate every 5 minutes
        return True