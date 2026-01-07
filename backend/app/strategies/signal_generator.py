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
        elif strategy_type_upper == 'STOCHASTIC':
            return self._generate_stochastic_signal(parameters, indicator_values, has_position)
        elif strategy_type_upper == 'KELTNER_CHANNEL':
            return self._generate_keltner_signal(parameters, indicator_values, has_position)
        elif strategy_type_upper == 'ATR_TRAILING_STOP':
            return self._generate_atr_trailing_stop_signal(parameters, indicator_values, has_position)
        elif strategy_type_upper == 'DONCHIAN_CHANNEL':
            return self._generate_donchian_signal(parameters, indicator_values, has_position)
        elif strategy_type_upper == 'ICHIMOKU_CLOUD':
            return self._generate_ichimoku_signal(parameters, indicator_values, has_position)
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

    def _generate_stochastic_signal(
        self,
        parameters: Dict[str, Any],
        indicators: Dict[str, Any],
        has_position: bool
    ) -> Tuple[SignalType, float, str, Dict[str, Any]]:
        """
        Generate Stochastic Oscillator strategy signal.

        BUY: %K crosses above %D in oversold zone
        SELL: %K crosses below %D in overbought zone
        """
        stoch_k = indicators.get('stoch_k_current', 50)
        stoch_d = indicators.get('stoch_d_current', 50)
        prev_k = indicators.get('stoch_k_prev', 50)
        prev_d = indicators.get('stoch_d_prev', 50)

        oversold = parameters.get('oversold', 20)
        overbought = parameters.get('overbought', 80)

        signal_indicators = {
            'stoch_k': stoch_k,
            'stoch_d': stoch_d,
            'oversold': oversold,
            'overbought': overbought,
            'current_price': indicators.get('current_price', 0)
        }

        # BUY: %K crosses above %D in oversold zone
        if stoch_k > stoch_d and prev_k <= prev_d and stoch_k < oversold and not has_position:
            strength = min((oversold - stoch_k) / oversold, 1.0)
            reasoning = f"Stochastic bullish crossover in oversold zone (%K={stoch_k:.1f}, %D={stoch_d:.1f})"
            logger.info(f"STOCHASTIC BUY signal: {reasoning}")
            return SignalType.BUY, max(strength, 0.3), reasoning, signal_indicators

        # SELL: %K crosses below %D in overbought zone
        elif stoch_k < stoch_d and prev_k >= prev_d and stoch_k > overbought and has_position:
            strength = min((stoch_k - overbought) / (100 - overbought), 1.0)
            reasoning = f"Stochastic bearish crossover in overbought zone (%K={stoch_k:.1f}, %D={stoch_d:.1f})"
            logger.info(f"STOCHASTIC SELL signal: {reasoning}")
            return SignalType.SELL, max(strength, 0.3), reasoning, signal_indicators

        else:
            reasoning = f"Stochastic neutral (%K={stoch_k:.1f}, %D={stoch_d:.1f})"
            return SignalType.HOLD, 0.0, reasoning, signal_indicators

    def _generate_keltner_signal(
        self,
        parameters: Dict[str, Any],
        indicators: Dict[str, Any],
        has_position: bool
    ) -> Tuple[SignalType, float, str, Dict[str, Any]]:
        """
        Generate Keltner Channel strategy signal.

        Breakout: BUY above upper, SELL below lower
        Mean Reversion: BUY at lower, SELL at upper
        """
        price = indicators.get('current_price', 0)
        kc_upper = indicators.get('kc_upper_current', price)
        kc_middle = indicators.get('kc_middle_current', price)
        kc_lower = indicators.get('kc_lower_current', price)

        use_breakout = parameters.get('use_breakout', True)

        signal_indicators = {
            'kc_upper': kc_upper,
            'kc_middle': kc_middle,
            'kc_lower': kc_lower,
            'current_price': price,
            'mode': 'breakout' if use_breakout else 'mean_reversion'
        }

        if use_breakout:
            # Breakout mode
            if price > kc_upper and not has_position:
                distance_pct = ((price - kc_upper) / kc_upper) * 100
                strength = min(distance_pct * 5, 1.0)
                reasoning = f"Keltner breakout above upper band (price={price:.2f}, upper={kc_upper:.2f})"
                return SignalType.BUY, max(strength, 0.3), reasoning, signal_indicators
            elif price < kc_lower and has_position:
                distance_pct = ((kc_lower - price) / kc_lower) * 100
                strength = min(distance_pct * 5, 1.0)
                reasoning = f"Keltner breakdown below lower band (price={price:.2f}, lower={kc_lower:.2f})"
                return SignalType.SELL, max(strength, 0.3), reasoning, signal_indicators
        else:
            # Mean reversion mode
            if price <= kc_lower and not has_position:
                distance_pct = ((kc_lower - price) / kc_lower) * 100
                strength = min(distance_pct * 10, 1.0)
                reasoning = f"Keltner mean reversion buy at lower band (price={price:.2f}, lower={kc_lower:.2f})"
                return SignalType.BUY, max(strength, 0.3), reasoning, signal_indicators
            elif price >= kc_upper and has_position:
                distance_pct = ((price - kc_upper) / kc_upper) * 100
                strength = min(distance_pct * 10, 1.0)
                reasoning = f"Keltner mean reversion sell at upper band (price={price:.2f}, upper={kc_upper:.2f})"
                return SignalType.SELL, max(strength, 0.3), reasoning, signal_indicators

        reasoning = f"Keltner neutral (price={price:.2f}, middle={kc_middle:.2f})"
        return SignalType.HOLD, 0.0, reasoning, signal_indicators

    def _generate_donchian_signal(
        self,
        parameters: Dict[str, Any],
        indicators: Dict[str, Any],
        has_position: bool
    ) -> Tuple[SignalType, float, str, Dict[str, Any]]:
        """
        Generate Donchian Channel (Turtle Trading) strategy signal.

        BUY: Price breaks above N-day high
        SELL: Price breaks below exit period low
        """
        price = indicators.get('current_price', 0)
        entry_high = indicators.get('entry_high_prev', price)
        exit_low = indicators.get('exit_low_prev', price)
        atr = indicators.get('atr_current', 0)

        signal_indicators = {
            'entry_high': entry_high,
            'exit_low': exit_low,
            'atr': atr,
            'current_price': price
        }

        # BUY: Price breaks above entry high
        if price > entry_high and not has_position:
            breakout_pct = ((price - entry_high) / entry_high) * 100
            strength = min(breakout_pct * 10, 1.0)
            reasoning = f"Donchian breakout above {parameters.get('entry_period', 20)}-day high (price={price:.2f}, high={entry_high:.2f})"
            logger.info(f"DONCHIAN BUY signal: {reasoning}")
            return SignalType.BUY, max(strength, 0.3), reasoning, signal_indicators

        # SELL: Price breaks below exit low
        elif price < exit_low and has_position:
            breakdown_pct = ((exit_low - price) / exit_low) * 100
            strength = min(breakdown_pct * 10, 1.0)
            reasoning = f"Donchian breakdown below {parameters.get('exit_period', 10)}-day low (price={price:.2f}, low={exit_low:.2f})"
            logger.info(f"DONCHIAN SELL signal: {reasoning}")
            return SignalType.SELL, max(strength, 0.3), reasoning, signal_indicators

        else:
            reasoning = f"Donchian neutral (price={price:.2f}, high={entry_high:.2f}, low={exit_low:.2f})"
            return SignalType.HOLD, 0.0, reasoning, signal_indicators


    def _generate_atr_trailing_stop_signal(
        self,
        parameters: Dict[str, Any],
        indicators: Dict[str, Any],
        has_position: bool
    ) -> Tuple[SignalType, float, str, Dict[str, Any]]:
        """
        Generate ATR Trailing Stop strategy signal.

        BUY: Price crosses above trend EMA
        SELL: Price crosses below trailing stop
        """
        price = indicators.get('current_price', 0)
        prev_price = indicators.get('prev_close', price)
        trend_ema = indicators.get('trend_ema_current', price)
        prev_trend_ema = indicators.get('trend_ema_prev', trend_ema)
        trailing_stop = indicators.get('trailing_stop_current', 0)
        prev_trailing_stop = indicators.get('trailing_stop_prev', trailing_stop)
        atr = indicators.get('atr_current', 0)

        signal_indicators = {
            'atr': atr,
            'trend_ema': trend_ema,
            'trailing_stop': trailing_stop,
            'current_price': price
        }

        # BUY: Price crosses above trend EMA
        if price > trend_ema and prev_price <= prev_trend_ema and not has_position:
            distance_pct = ((price - trend_ema) / trend_ema) * 100
            strength = min(distance_pct * 5, 1.0)
            reasoning = f"ATR Trailing Stop: Price crossed above trend EMA (price={price:.2f}, ema={trend_ema:.2f})"
            return SignalType.BUY, max(strength, 0.3), reasoning, signal_indicators

        # SELL: Price crosses below trailing stop
        elif price < trailing_stop and prev_price >= prev_trailing_stop and has_position:
            distance_pct = ((trailing_stop - price) / trailing_stop) * 100
            strength = min(distance_pct * 5, 1.0)
            reasoning = f"ATR Trailing Stop: Price crossed below stop (price={price:.2f}, stop={trailing_stop:.2f})"
            return SignalType.SELL, max(strength, 0.3), reasoning, signal_indicators

        else:
            reasoning = f"ATR Trailing Stop neutral (price={price:.2f}, stop={trailing_stop:.2f})"
            return SignalType.HOLD, 0.0, reasoning, signal_indicators

    def _generate_ichimoku_signal(
        self,
        parameters: Dict[str, Any],
        indicators: Dict[str, Any],
        has_position: bool
    ) -> Tuple[SignalType, float, str, Dict[str, Any]]:
        """
        Generate Ichimoku Cloud strategy signal.

        BUY: TK cross up + price above cloud + bullish cloud
        SELL: TK cross down + price below cloud + bearish cloud
        """
        price = indicators.get('current_price', 0)
        tenkan = indicators.get('tenkan_sen_current', price)
        kijun = indicators.get('kijun_sen_current', price)
        prev_tenkan = indicators.get('tenkan_sen_prev', tenkan)
        prev_kijun = indicators.get('kijun_sen_prev', kijun)
        cloud_top = indicators.get('cloud_top_current', price)
        cloud_bottom = indicators.get('cloud_bottom_current', price)
        future_senkou_a = indicators.get('future_senkou_a_current', price)
        future_senkou_b = indicators.get('future_senkou_b_current', price)

        signal_indicators = {
            'tenkan_sen': tenkan,
            'kijun_sen': kijun,
            'cloud_top': cloud_top,
            'cloud_bottom': cloud_bottom,
            'current_price': price
        }

        # TK Cross detection
        tk_cross_up = tenkan > kijun and prev_tenkan <= prev_kijun
        tk_cross_down = tenkan < kijun and prev_tenkan >= prev_kijun

        # Position relative to cloud
        price_above_cloud = price > cloud_top
        price_below_cloud = price < cloud_bottom

        # Future cloud direction
        future_cloud_bullish = future_senkou_a > future_senkou_b
        future_cloud_bearish = future_senkou_a < future_senkou_b

        # Strong BUY signal
        if tk_cross_up and price_above_cloud and future_cloud_bullish and not has_position:
            strength = 0.9  # Strong signal
            reasoning = f"Ichimoku strong bullish: TK cross up, price above cloud, bullish future cloud"
            logger.info(f"ICHIMOKU BUY signal: {reasoning}")
            return SignalType.BUY, strength, reasoning, signal_indicators

        # Weak BUY signal
        elif tk_cross_up and not has_position:
            strength = 0.5  # Weak signal
            reasoning = f"Ichimoku weak bullish: TK cross up (price={price:.2f}, tenkan={tenkan:.2f}, kijun={kijun:.2f})"
            logger.info(f"ICHIMOKU BUY signal: {reasoning}")
            return SignalType.BUY, strength, reasoning, signal_indicators

        # Strong SELL signal
        elif tk_cross_down and price_below_cloud and future_cloud_bearish and has_position:
            strength = 0.9  # Strong signal
            reasoning = f"Ichimoku strong bearish: TK cross down, price below cloud, bearish future cloud"
            logger.info(f"ICHIMOKU SELL signal: {reasoning}")
            return SignalType.SELL, strength, reasoning, signal_indicators

        # Weak SELL signal
        elif tk_cross_down and has_position:
            strength = 0.5  # Weak signal
            reasoning = f"Ichimoku weak bearish: TK cross down (price={price:.2f}, tenkan={tenkan:.2f}, kijun={kijun:.2f})"
            logger.info(f"ICHIMOKU SELL signal: {reasoning}")
            return SignalType.SELL, strength, reasoning, signal_indicators

        else:
            if price > cloud_top:
                bias = "bullish"
            elif price < cloud_bottom:
                bias = "bearish"
            else:
                bias = "neutral"
            reasoning = f"Ichimoku {bias} (price={price:.2f}, cloud_top={cloud_top:.2f}, cloud_bottom={cloud_bottom:.2f})"
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