"""
Technical indicators module.
Calculates technical indicators using pandas_ta for strategy signal generation.
"""
import logging
from typing import Dict, Any, Optional, List
import pandas as pd
import pandas_ta as ta

logger = logging.getLogger(__name__)


class TechnicalIndicators:
    """
    Technical indicators calculator using pandas_ta.
    Provides methods for calculating common technical indicators.
    """
    
    @staticmethod
    def prepare_dataframe(bars: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Convert bar data to pandas DataFrame with proper columns.
        
        Args:
            bars: List of bar dictionaries with OHLCV data
            
        Returns:
            DataFrame with columns: open, high, low, close, volume, timestamp
        """
        if not bars:
            raise ValueError("No bar data provided")
        
        df = pd.DataFrame(bars)
        
        # Ensure required columns exist
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")
        
        # Convert timestamp to datetime if it exists
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.set_index('timestamp', inplace=True)
        
        # Ensure numeric types
        for col in required_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Drop any rows with NaN values
        df = df.dropna()
        
        if len(df) == 0:
            raise ValueError("No valid data after cleaning")
        
        logger.debug(f"Prepared DataFrame with {len(df)} bars")
        return df
    
    @staticmethod
    def calculate_rsi(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """
        Calculate Relative Strength Index (RSI).
        
        Args:
            df: DataFrame with OHLCV data
            period: RSI period (default: 14)
            
        Returns:
            Series with RSI values
        """
        try:
            rsi = ta.rsi(df['close'], length=period)
            logger.debug(f"Calculated RSI with period {period}, current value: {rsi.iloc[-1]:.2f}")
            return rsi
        except Exception as e:
            logger.error(f"Error calculating RSI: {e}")
            raise
    
    @staticmethod
    def calculate_macd(
        df: pd.DataFrame,
        fast: int = 12,
        slow: int = 26,
        signal: int = 9
    ) -> Dict[str, pd.Series]:
        """
        Calculate MACD (Moving Average Convergence Divergence).
        
        Args:
            df: DataFrame with OHLCV data
            fast: Fast EMA period (default: 12)
            slow: Slow EMA period (default: 26)
            signal: Signal line period (default: 9)
            
        Returns:
            Dictionary with 'macd', 'signal', and 'histogram' Series
        """
        try:
            macd_result = ta.macd(df['close'], fast=fast, slow=slow, signal=signal)
            
            result = {
                'macd': macd_result[f'MACD_{fast}_{slow}_{signal}'],
                'signal': macd_result[f'MACDs_{fast}_{slow}_{signal}'],
                'histogram': macd_result[f'MACDh_{fast}_{slow}_{signal}']
            }
            
            logger.debug(
                f"Calculated MACD: macd={result['macd'].iloc[-1]:.4f}, "
                f"signal={result['signal'].iloc[-1]:.4f}, "
                f"histogram={result['histogram'].iloc[-1]:.4f}"
            )
            return result
        except Exception as e:
            logger.error(f"Error calculating MACD: {e}")
            raise
    
    @staticmethod
    def calculate_sma(df: pd.DataFrame, period: int = 20) -> pd.Series:
        """
        Calculate Simple Moving Average (SMA).
        
        Args:
            df: DataFrame with OHLCV data
            period: SMA period (default: 20)
            
        Returns:
            Series with SMA values
        """
        try:
            sma = ta.sma(df['close'], length=period)
            logger.debug(f"Calculated SMA with period {period}, current value: {sma.iloc[-1]:.2f}")
            return sma
        except Exception as e:
            logger.error(f"Error calculating SMA: {e}")
            raise
    
    @staticmethod
    def calculate_ema(df: pd.DataFrame, period: int = 20) -> pd.Series:
        """
        Calculate Exponential Moving Average (EMA).
        
        Args:
            df: DataFrame with OHLCV data
            period: EMA period (default: 20)
            
        Returns:
            Series with EMA values
        """
        try:
            ema = ta.ema(df['close'], length=period)
            logger.debug(f"Calculated EMA with period {period}, current value: {ema.iloc[-1]:.2f}")
            return ema
        except Exception as e:
            logger.error(f"Error calculating EMA: {e}")
            raise
    
    @staticmethod
    def calculate_bollinger_bands(
        df: pd.DataFrame,
        period: int = 20,
        std_dev: float = 2.0
    ) -> Dict[str, pd.Series]:
        """
        Calculate Bollinger Bands.
        
        Args:
            df: DataFrame with OHLCV data
            period: Moving average period (default: 20)
            std_dev: Number of standard deviations (default: 2.0)
            
        Returns:
            Dictionary with 'upper', 'middle', and 'lower' Series
        """
        try:
            bb_result = ta.bbands(df['close'], length=period, std=std_dev)
            
            result = {
                'upper': bb_result[f'BBU_{period}_{std_dev}'],
                'middle': bb_result[f'BBM_{period}_{std_dev}'],
                'lower': bb_result[f'BBL_{period}_{std_dev}']
            }
            
            logger.debug(
                f"Calculated Bollinger Bands: "
                f"upper={result['upper'].iloc[-1]:.2f}, "
                f"middle={result['middle'].iloc[-1]:.2f}, "
                f"lower={result['lower'].iloc[-1]:.2f}"
            )
            return result
        except Exception as e:
            logger.error(f"Error calculating Bollinger Bands: {e}")
            raise
    
    @staticmethod
    def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """
        Calculate Average True Range (ATR) for volatility measurement.
        
        Args:
            df: DataFrame with OHLCV data
            period: ATR period (default: 14)
            
        Returns:
            Series with ATR values
        """
        try:
            atr = ta.atr(df['high'], df['low'], df['close'], length=period)
            logger.debug(f"Calculated ATR with period {period}, current value: {atr.iloc[-1]:.2f}")
            return atr
        except Exception as e:
            logger.error(f"Error calculating ATR: {e}")
            raise
    
    @staticmethod
    def calculate_volume_sma(df: pd.DataFrame, period: int = 20) -> pd.Series:
        """
        Calculate Simple Moving Average of volume.
        
        Args:
            df: DataFrame with OHLCV data
            period: SMA period (default: 20)
            
        Returns:
            Series with volume SMA values
        """
        try:
            volume_sma = ta.sma(df['volume'], length=period)
            logger.debug(f"Calculated Volume SMA with period {period}")
            return volume_sma
        except Exception as e:
            logger.error(f"Error calculating Volume SMA: {e}")
            raise
    
    @staticmethod
    def calculate_stochastic(
        df: pd.DataFrame,
        k_period: int = 14,
        d_period: int = 3
    ) -> Dict[str, pd.Series]:
        """
        Calculate Stochastic Oscillator.
        
        Args:
            df: DataFrame with OHLCV data
            k_period: %K period (default: 14)
            d_period: %D period (default: 3)
            
        Returns:
            Dictionary with 'k' and 'd' Series
        """
        try:
            stoch_result = ta.stoch(
                df['high'],
                df['low'],
                df['close'],
                k=k_period,
                d=d_period
            )
            
            result = {
                'k': stoch_result[f'STOCHk_{k_period}_{d_period}_3'],
                'd': stoch_result[f'STOCHd_{k_period}_{d_period}_3']
            }
            
            logger.debug(
                f"Calculated Stochastic: k={result['k'].iloc[-1]:.2f}, "
                f"d={result['d'].iloc[-1]:.2f}"
            )
            return result
        except Exception as e:
            logger.error(f"Error calculating Stochastic: {e}")
            raise
    
    @staticmethod
    def calculate_adx(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """
        Calculate Average Directional Index (ADX) for trend strength.
        
        Args:
            df: DataFrame with OHLCV data
            period: ADX period (default: 14)
            
        Returns:
            Series with ADX values
        """
        try:
            adx_result = ta.adx(df['high'], df['low'], df['close'], length=period)
            adx = adx_result[f'ADX_{period}']
            logger.debug(f"Calculated ADX with period {period}, current value: {adx.iloc[-1]:.2f}")
            return adx
        except Exception as e:
            logger.error(f"Error calculating ADX: {e}")
            raise
    
    @staticmethod
    def calculate_vwap(df: pd.DataFrame) -> pd.Series:
        """
        Calculate Volume Weighted Average Price (VWAP).
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            Series with VWAP values
        """
        try:
            vwap = ta.vwap(df['high'], df['low'], df['close'], df['volume'])
            logger.debug(f"Calculated VWAP, current value: {vwap.iloc[-1]:.2f}")
            return vwap
        except Exception as e:
            logger.error(f"Error calculating VWAP: {e}")
            raise
    
    @staticmethod
    def calculate_all_for_strategy(
        df: pd.DataFrame,
        strategy_type: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate all indicators needed for a specific strategy type.
        
        Args:
            df: DataFrame with OHLCV data
            strategy_type: Type of strategy (RSI, MACD, SMA_CROSSOVER, etc.)
            parameters: Strategy-specific parameters
            
        Returns:
            Dictionary with all calculated indicators
        """
        indicators = {}
        current_price = float(df['close'].iloc[-1])
        
        try:
            if strategy_type.upper() == 'RSI':
                rsi_period = parameters.get('rsi_period', 14)
                indicators['rsi'] = TechnicalIndicators.calculate_rsi(df, rsi_period)
                indicators['rsi_current'] = float(indicators['rsi'].iloc[-1])
                
            elif strategy_type.upper() == 'MACD':
                fast = parameters.get('fast_period', 12)
                slow = parameters.get('slow_period', 26)
                signal = parameters.get('signal_period', 9)
                macd_data = TechnicalIndicators.calculate_macd(df, fast, slow, signal)
                indicators['macd'] = macd_data['macd']
                indicators['macd_signal'] = macd_data['signal']
                indicators['macd_histogram'] = macd_data['histogram']
                indicators['macd_current'] = float(macd_data['macd'].iloc[-1])
                indicators['signal_current'] = float(macd_data['signal'].iloc[-1])
                indicators['histogram_current'] = float(macd_data['histogram'].iloc[-1])
                
            elif strategy_type.upper() == 'SMA_CROSSOVER':
                fast_period = parameters.get('fast_period', 50)
                slow_period = parameters.get('slow_period', 200)
                indicators['fast_sma'] = TechnicalIndicators.calculate_sma(df, fast_period)
                indicators['slow_sma'] = TechnicalIndicators.calculate_sma(df, slow_period)
                indicators['fast_sma_current'] = float(indicators['fast_sma'].iloc[-1])
                indicators['slow_sma_current'] = float(indicators['slow_sma'].iloc[-1])
                
            elif strategy_type.upper() == 'BOLLINGER_BANDS':
                period = parameters.get('period', 20)
                std_dev = parameters.get('std_dev', 2.0)
                bb_data = TechnicalIndicators.calculate_bollinger_bands(df, period, std_dev)
                indicators['bb_upper'] = bb_data['upper']
                indicators['bb_middle'] = bb_data['middle']
                indicators['bb_lower'] = bb_data['lower']
                indicators['bb_upper_current'] = float(bb_data['upper'].iloc[-1])
                indicators['bb_middle_current'] = float(bb_data['middle'].iloc[-1])
                indicators['bb_lower_current'] = float(bb_data['lower'].iloc[-1])
                
            elif strategy_type.upper() == 'MEAN_REVERSION':
                period = parameters.get('period', 20)
                std_dev = parameters.get('std_dev', 2.0)
                indicators['sma'] = TechnicalIndicators.calculate_sma(df, period)
                indicators['sma_current'] = float(indicators['sma'].iloc[-1])
                # Calculate standard deviation
                indicators['std'] = df['close'].rolling(window=period).std()
                indicators['std_current'] = float(indicators['std'].iloc[-1])
                # Calculate z-score
                indicators['z_score'] = (df['close'] - indicators['sma']) / indicators['std']
                indicators['z_score_current'] = float(indicators['z_score'].iloc[-1])
            
            # Add common indicators
            indicators['current_price'] = current_price
            indicators['volume_current'] = float(df['volume'].iloc[-1])
            
            logger.info(f"Calculated indicators for {strategy_type}: {list(indicators.keys())}")
            return indicators
            
        except Exception as e:
            logger.error(f"Error calculating indicators for {strategy_type}: {e}")
            raise
    
    @staticmethod
    def get_crossover_signal(
        series1: pd.Series,
        series2: pd.Series,
        lookback: int = 2
    ) -> Optional[str]:
        """
        Detect crossover between two series.
        
        Args:
            series1: First series (e.g., fast MA)
            series2: Second series (e.g., slow MA)
            lookback: Number of periods to look back (default: 2)
            
        Returns:
            'bullish' for upward cross, 'bearish' for downward cross, None otherwise
        """
        if len(series1) < lookback or len(series2) < lookback:
            return None
        
        # Check if series1 crossed above series2 (bullish)
        if series1.iloc[-lookback] <= series2.iloc[-lookback] and series1.iloc[-1] > series2.iloc[-1]:
            return 'bullish'
        
        # Check if series1 crossed below series2 (bearish)
        if series1.iloc[-lookback] >= series2.iloc[-lookback] and series1.iloc[-1] < series2.iloc[-1]:
            return 'bearish'
        
        return None
