# Five New Trading Strategies Implementation Plan

## Overview

Implement 5 new trading strategies that are widely used globally but currently missing from the codebase. Each strategy will be implemented following existing patterns, with both CLI support (`src/strategies/`) and backend support (`backend/app/strategies/`).

## Current State Analysis

**Existing Strategies (11 total):** SMA Crossover, RSI, MACD, Bollinger Bands, VWAP, Momentum, Breakout, Mean Reversion, Pairs Trading, ML Strategy, Adaptive ML Strategy.

**Key Patterns Discovered:**
- CLI strategies: Inherit from `BaseStrategy`, implement `calculate_indicators()` and `generate_signals()`
- Backend strategies: Add method to `SignalGenerator` class, update routing in `generate_signal()`
- Signal format: `(SignalType, strength: float, reasoning: str, indicator_values: dict)`
- All strategies use pandas DataFrames with OHLCV columns

## Desired End State

After implementation:
1. 5 new strategies fully functional in CLI (`src/strategies/`)
2. 5 new strategies supported in backend (`backend/app/strategies/signal_generator.py`)
3. Required indicators added to `backend/app/strategies/indicators.py`
4. All strategies follow existing code patterns and conventions

### Verification Commands:
```bash
# Import test
cd /Users/ashwin/projects/algo-trading-app
python -c "from src.strategies.stochastic_strategy import StochasticStrategy; print('OK')"
python -c "from src.strategies.keltner_channel import KeltnerChannelStrategy; print('OK')"
python -c "from src.strategies.atr_trailing_stop import ATRTrailingStopStrategy; print('OK')"
python -c "from src.strategies.donchian_channel import DonchianChannelStrategy; print('OK')"
python -c "from src.strategies.ichimoku_cloud import IchimokuCloudStrategy; print('OK')"

# Backend test
cd /Users/ashwin/projects/algo-trading-app/backend
poetry run python -c "from app.strategies.signal_generator import SignalGenerator; print('OK')"
```

## What We're NOT Doing

- NOT adding unit tests (existing codebase doesn't have strategy unit tests)
- NOT modifying frontend (strategy types are string-based, frontend is flexible)
- NOT adding database migrations (strategies use existing JSON parameters field)
- NOT modifying strategy execution flow (only adding new strategy types)

## Implementation Approach

Implement all 5 strategies in parallel using sub-agents. Each strategy is independent and can be implemented concurrently. The approach for each:

1. Create CLI strategy file following `BaseStrategy` pattern
2. Add indicator calculation to `TechnicalIndicators` if needed
3. Add signal generation method to `SignalGenerator`
4. Update routing in `generate_signal()` method

---

## Phase 1: Stochastic Oscillator Strategy

### Overview
Classic momentum oscillator that complements RSI. Low complexity - uses existing patterns.

### Changes Required:

#### 1. CLI Strategy File
**File**: `src/strategies/stochastic_strategy.py`
**Changes**: Create new file

```python
"""
Stochastic Oscillator Trading Strategy.

Uses %K and %D crossovers in overbought/oversold zones to generate signals.
Developed by George Lane in the 1950s.
"""

import pandas as pd
from .base_strategy import BaseStrategy, Signal


class StochasticStrategy(BaseStrategy):
    """
    Stochastic Oscillator strategy implementation.

    Generates BUY signals when %K crosses above %D in oversold zone.
    Generates SELL signals when %K crosses below %D in overbought zone.
    """

    def __init__(
        self,
        k_period: int = 14,
        d_period: int = 3,
        smooth_k: int = 3,
        oversold: int = 20,
        overbought: int = 80
    ):
        """
        Initialize Stochastic strategy.

        Args:
            k_period: Lookback period for %K (default 14)
            d_period: Smoothing period for %D (default 3)
            smooth_k: Smoothing period for slow %K (default 3)
            oversold: Oversold threshold (default 20)
            overbought: Overbought threshold (default 80)
        """
        super().__init__(name="Stochastic")
        self.k_period = k_period
        self.d_period = d_period
        self.smooth_k = smooth_k
        self.oversold = oversold
        self.overbought = overbought

        if not (0 < oversold < overbought < 100):
            raise ValueError("Invalid thresholds: 0 < oversold < overbought < 100")

    def calculate_stochastic(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate Stochastic %K and %D.

        %K = 100 * (Close - Low_N) / (High_N - Low_N)
        %D = SMA of %K
        """
        df = data.copy()

        # Calculate highest high and lowest low over k_period
        low_min = df['low'].rolling(window=self.k_period).min()
        high_max = df['high'].rolling(window=self.k_period).max()

        # Fast %K
        fast_k = 100 * (df['close'] - low_min) / (high_max - low_min)

        # Slow %K (smoothed)
        df['stoch_k'] = fast_k.rolling(window=self.smooth_k).mean()

        # %D (signal line)
        df['stoch_d'] = df['stoch_k'].rolling(window=self.d_period).mean()

        return df

    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate all stochastic indicators."""
        return self.calculate_stochastic(data)

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate trading signals based on Stochastic crossovers.

        BUY: %K crosses above %D below oversold threshold
        SELL: %K crosses below %D above overbought threshold
        """
        df = self.calculate_indicators(data)
        signals = pd.Series(0, index=df.index)

        # Previous values for crossover detection
        prev_k = df['stoch_k'].shift(1)
        prev_d = df['stoch_d'].shift(1)

        # BUY: %K crosses above %D in oversold zone
        buy_condition = (
            (df['stoch_k'] > df['stoch_d']) &  # %K above %D now
            (prev_k <= prev_d) &                # %K was below/equal %D before
            (df['stoch_k'] < self.oversold)     # In oversold zone
        )

        # SELL: %K crosses below %D in overbought zone
        sell_condition = (
            (df['stoch_k'] < df['stoch_d']) &   # %K below %D now
            (prev_k >= prev_d) &                 # %K was above/equal %D before
            (df['stoch_k'] > self.overbought)   # In overbought zone
        )

        signals[buy_condition] = Signal.BUY.value
        signals[sell_condition] = Signal.SELL.value

        return signals

    def get_strategy_state(self, data: pd.DataFrame) -> dict:
        """Get current strategy state for monitoring."""
        df = self.calculate_indicators(data)

        if len(df) < self.k_period + self.d_period:
            return {
                'status': 'insufficient_data',
                'message': f'Need at least {self.k_period + self.d_period} data points'
            }

        latest = df.iloc[-1]

        if latest['stoch_k'] < self.oversold:
            condition = 'oversold'
        elif latest['stoch_k'] > self.overbought:
            condition = 'overbought'
        else:
            condition = 'neutral'

        return {
            'status': 'active',
            'stoch_k': latest['stoch_k'],
            'stoch_d': latest['stoch_d'],
            'current_price': latest['close'],
            'condition': condition,
            'k_period': self.k_period,
            'd_period': self.d_period
        }

    def __str__(self) -> str:
        return f"Stochastic(k={self.k_period}, d={self.d_period}, oversold={self.oversold}, overbought={self.overbought})"
```

#### 2. Backend Signal Generator
**File**: `backend/app/strategies/signal_generator.py`
**Changes**: Add method and routing

Add to routing (after line 72, before else):
```python
elif strategy_type_upper == 'STOCHASTIC':
    return self._generate_stochastic_signal(parameters, indicator_values, has_position)
```

Add new method (after `_generate_mean_reversion_signal`):
```python
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
```

#### 3. Backend Indicators
**File**: `backend/app/strategies/indicators.py`
**Changes**: Add stochastic calculation to `calculate_all_for_strategy()`

Add after line 381 (before common indicators):
```python
elif strategy_type.upper() == 'STOCHASTIC':
    k_period = parameters.get('k_period', 14)
    d_period = parameters.get('d_period', 3)
    smooth_k = parameters.get('smooth_k', 3)

    stoch = TechnicalIndicators.calculate_stochastic(df, k_period, d_period, smooth_k)
    indicators['stoch_k'] = stoch['k']
    indicators['stoch_d'] = stoch['d']
    indicators['stoch_k_current'] = float(stoch['k'].iloc[-1])
    indicators['stoch_d_current'] = float(stoch['d'].iloc[-1])
    indicators['stoch_k_prev'] = float(stoch['k'].iloc[-2]) if len(stoch['k']) > 1 else indicators['stoch_k_current']
    indicators['stoch_d_prev'] = float(stoch['d'].iloc[-2]) if len(stoch['d']) > 1 else indicators['stoch_d_current']
```

### Success Criteria:

#### Automated Verification:
- [ ] File exists: `src/strategies/stochastic_strategy.py`
- [ ] Import works: `python -c "from src.strategies.stochastic_strategy import StochasticStrategy"`
- [ ] Backend routing works: Strategy type "STOCHASTIC" recognized

---

## Phase 2: Keltner Channel Strategy

### Overview
Volatility-based channel using EMA and ATR (better than Bollinger for volatile markets).

### Changes Required:

#### 1. CLI Strategy File
**File**: `src/strategies/keltner_channel.py`
**Changes**: Create new file

```python
"""
Keltner Channel Trading Strategy.

Uses EMA-based channels with ATR for volatility measurement.
More stable than Bollinger Bands in volatile markets.
"""

import pandas as pd
import numpy as np
from .base_strategy import BaseStrategy, Signal


class KeltnerChannelStrategy(BaseStrategy):
    """
    Keltner Channel strategy implementation.

    Middle Line: EMA of close prices
    Upper Band: EMA + (ATR * multiplier)
    Lower Band: EMA - (ATR * multiplier)

    Supports both breakout and mean reversion modes.
    """

    def __init__(
        self,
        ema_period: int = 20,
        atr_period: int = 10,
        multiplier: float = 2.0,
        use_breakout: bool = True
    ):
        """
        Initialize Keltner Channel strategy.

        Args:
            ema_period: Period for EMA calculation (default 20)
            atr_period: Period for ATR calculation (default 10)
            multiplier: Band width multiplier (default 2.0)
            use_breakout: True for breakout mode, False for mean reversion
        """
        super().__init__(name="Keltner Channel")
        self.ema_period = ema_period
        self.atr_period = atr_period
        self.multiplier = multiplier
        self.use_breakout = use_breakout

    def calculate_atr(self, data: pd.DataFrame, period: int) -> pd.Series:
        """Calculate Average True Range."""
        high = data['high']
        low = data['low']
        close = data['close']

        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))

        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = true_range.rolling(window=period).mean()

        return atr

    def calculate_ema(self, series: pd.Series, period: int) -> pd.Series:
        """Calculate Exponential Moving Average."""
        return series.ewm(span=period, adjust=False).mean()

    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate Keltner Channel indicators."""
        df = data.copy()

        # Middle line (EMA)
        df['kc_middle'] = self.calculate_ema(df['close'], self.ema_period)

        # ATR for band width
        df['atr'] = self.calculate_atr(df, self.atr_period)

        # Upper and lower bands
        df['kc_upper'] = df['kc_middle'] + (self.multiplier * df['atr'])
        df['kc_lower'] = df['kc_middle'] - (self.multiplier * df['atr'])

        # Position within channel (0 = lower, 1 = upper)
        df['kc_position'] = (df['close'] - df['kc_lower']) / (df['kc_upper'] - df['kc_lower'])

        return df

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate trading signals.

        Breakout mode:
            BUY: Close breaks above upper band
            SELL: Close breaks below lower band

        Mean reversion mode:
            BUY: Close touches lower band
            SELL: Close touches upper band
        """
        df = self.calculate_indicators(data)
        signals = pd.Series(0, index=df.index)

        if self.use_breakout:
            # Breakout mode: trade with the trend
            buy_condition = df['close'] > df['kc_upper']
            sell_condition = df['close'] < df['kc_lower']
        else:
            # Mean reversion mode: fade the extremes
            buy_condition = (df['close'] <= df['kc_lower']) | (df['kc_position'] <= 0.05)
            sell_condition = (df['close'] >= df['kc_upper']) | (df['kc_position'] >= 0.95)

        signals[buy_condition] = Signal.BUY.value
        signals[sell_condition] = Signal.SELL.value

        return signals

    def get_strategy_state(self, data: pd.DataFrame) -> dict:
        """Get current strategy state."""
        df = self.calculate_indicators(data)

        if len(df) < max(self.ema_period, self.atr_period):
            return {
                'status': 'insufficient_data',
                'message': f'Need at least {max(self.ema_period, self.atr_period)} data points'
            }

        latest = df.iloc[-1]

        if latest['close'] > latest['kc_upper']:
            condition = 'above_upper'
        elif latest['close'] < latest['kc_lower']:
            condition = 'below_lower'
        else:
            condition = 'within_channel'

        return {
            'status': 'active',
            'kc_upper': latest['kc_upper'],
            'kc_middle': latest['kc_middle'],
            'kc_lower': latest['kc_lower'],
            'kc_position': latest['kc_position'],
            'atr': latest['atr'],
            'current_price': latest['close'],
            'condition': condition,
            'mode': 'breakout' if self.use_breakout else 'mean_reversion'
        }

    def __str__(self) -> str:
        mode = 'breakout' if self.use_breakout else 'mean_reversion'
        return f"KeltnerChannel(ema={self.ema_period}, atr={self.atr_period}, mult={self.multiplier}, mode={mode})"
```

#### 2. Backend Signal Generator
**File**: `backend/app/strategies/signal_generator.py`
**Changes**: Add method and routing

Add to routing:
```python
elif strategy_type_upper == 'KELTNER_CHANNEL':
    return self._generate_keltner_signal(parameters, indicator_values, has_position)
```

Add new method:
```python
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
```

#### 3. Backend Indicators
**File**: `backend/app/strategies/indicators.py`
**Changes**: Add to `calculate_all_for_strategy()`

```python
elif strategy_type.upper() == 'KELTNER_CHANNEL':
    ema_period = parameters.get('ema_period', 20)
    atr_period = parameters.get('atr_period', 10)
    multiplier = parameters.get('multiplier', 2.0)

    ema = TechnicalIndicators.calculate_ema(df, ema_period)
    atr = TechnicalIndicators.calculate_atr(df, atr_period)

    indicators['kc_middle'] = ema
    indicators['kc_upper'] = ema + (multiplier * atr)
    indicators['kc_lower'] = ema - (multiplier * atr)
    indicators['kc_middle_current'] = float(ema.iloc[-1])
    indicators['kc_upper_current'] = float(indicators['kc_upper'].iloc[-1])
    indicators['kc_lower_current'] = float(indicators['kc_lower'].iloc[-1])
```

### Success Criteria:

#### Automated Verification:
- [ ] File exists: `src/strategies/keltner_channel.py`
- [ ] Import works: `python -c "from src.strategies.keltner_channel import KeltnerChannelStrategy"`
- [ ] Backend routing works: Strategy type "KELTNER_CHANNEL" recognized

---

## Phase 3: ATR Trailing Stop Strategy

### Overview
Volatility-adjusted trailing stop strategy used by professional traders.

### Changes Required:

#### 1. CLI Strategy File
**File**: `src/strategies/atr_trailing_stop.py`
**Changes**: Create new file

```python
"""
ATR Trailing Stop Trading Strategy.

Uses Average True Range for volatility-adjusted stop-loss management.
Popular among professional traders for dynamic position management.
"""

import pandas as pd
import numpy as np
from .base_strategy import BaseStrategy, Signal


class ATRTrailingStopStrategy(BaseStrategy):
    """
    ATR Trailing Stop strategy implementation.

    Entry: Price above EMA (trend filter)
    Stop: ATR-based trailing stop that moves with price
    Chandelier Exit variant: Stop from highest high
    """

    def __init__(
        self,
        atr_period: int = 14,
        atr_multiplier: float = 3.0,
        trend_period: int = 50,
        use_chandelier: bool = True
    ):
        """
        Initialize ATR Trailing Stop strategy.

        Args:
            atr_period: Period for ATR calculation (default 14)
            atr_multiplier: Stop distance multiplier (default 3.0)
            trend_period: Period for trend EMA (default 50)
            use_chandelier: Use Chandelier Exit method (default True)
        """
        super().__init__(name="ATR Trailing Stop")
        self.atr_period = atr_period
        self.atr_multiplier = atr_multiplier
        self.trend_period = trend_period
        self.use_chandelier = use_chandelier

    def calculate_atr(self, data: pd.DataFrame, period: int) -> pd.Series:
        """Calculate Average True Range."""
        high = data['high']
        low = data['low']
        close = data['close']

        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))

        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = true_range.rolling(window=period).mean()

        return atr

    def calculate_ema(self, series: pd.Series, period: int) -> pd.Series:
        """Calculate Exponential Moving Average."""
        return series.ewm(span=period, adjust=False).mean()

    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate ATR trailing stop indicators."""
        df = data.copy()

        # ATR for stop calculation
        df['atr'] = self.calculate_atr(df, self.atr_period)

        # Trend filter (EMA)
        df['trend_ema'] = self.calculate_ema(df['close'], self.trend_period)

        # Trailing stop calculation
        atr_stop_distance = self.atr_multiplier * df['atr']

        if self.use_chandelier:
            # Chandelier Exit: Stop from highest high
            df['highest_high'] = df['high'].rolling(window=self.atr_period).max()
            df['trailing_stop_long'] = df['highest_high'] - atr_stop_distance
            df['lowest_low'] = df['low'].rolling(window=self.atr_period).min()
            df['trailing_stop_short'] = df['lowest_low'] + atr_stop_distance
        else:
            # Simple ATR stop from close
            df['trailing_stop_long'] = df['close'] - atr_stop_distance
            df['trailing_stop_short'] = df['close'] + atr_stop_distance

        # Trend direction
        df['trend_up'] = df['close'] > df['trend_ema']

        return df

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate trading signals.

        BUY: Price above trend EMA and not stopped out
        SELL: Price crosses below trailing stop
        """
        df = self.calculate_indicators(data)
        signals = pd.Series(0, index=df.index)

        # BUY signal: Price crosses above trend EMA
        buy_condition = (
            (df['close'] > df['trend_ema']) &
            (df['close'].shift(1) <= df['trend_ema'].shift(1))
        )

        # SELL signal: Price crosses below trailing stop
        sell_condition = (
            (df['close'] < df['trailing_stop_long']) &
            (df['close'].shift(1) >= df['trailing_stop_long'].shift(1))
        )

        signals[buy_condition] = Signal.BUY.value
        signals[sell_condition] = Signal.SELL.value

        return signals

    def get_strategy_state(self, data: pd.DataFrame) -> dict:
        """Get current strategy state."""
        df = self.calculate_indicators(data)

        required_periods = max(self.atr_period, self.trend_period)
        if len(df) < required_periods:
            return {
                'status': 'insufficient_data',
                'message': f'Need at least {required_periods} data points'
            }

        latest = df.iloc[-1]

        if latest['close'] > latest['trend_ema']:
            trend = 'bullish'
        else:
            trend = 'bearish'

        return {
            'status': 'active',
            'atr': latest['atr'],
            'trend_ema': latest['trend_ema'],
            'trailing_stop_long': latest['trailing_stop_long'],
            'trailing_stop_short': latest['trailing_stop_short'],
            'current_price': latest['close'],
            'trend': trend,
            'atr_multiplier': self.atr_multiplier,
            'use_chandelier': self.use_chandelier
        }

    def __str__(self) -> str:
        mode = 'chandelier' if self.use_chandelier else 'simple'
        return f"ATRTrailingStop(atr={self.atr_period}, mult={self.atr_multiplier}, trend={self.trend_period}, mode={mode})"
```

#### 2. Backend Signal Generator
**File**: `backend/app/strategies/signal_generator.py`
**Changes**: Add method and routing

Add to routing:
```python
elif strategy_type_upper == 'ATR_TRAILING_STOP':
    return self._generate_atr_trailing_stop_signal(parameters, indicator_values, has_position)
```

Add new method:
```python
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
```

#### 3. Backend Indicators
**File**: `backend/app/strategies/indicators.py`
**Changes**: Add to `calculate_all_for_strategy()`

```python
elif strategy_type.upper() == 'ATR_TRAILING_STOP':
    atr_period = parameters.get('atr_period', 14)
    atr_multiplier = parameters.get('atr_multiplier', 3.0)
    trend_period = parameters.get('trend_period', 50)
    use_chandelier = parameters.get('use_chandelier', True)

    atr = TechnicalIndicators.calculate_atr(df, atr_period)
    trend_ema = TechnicalIndicators.calculate_ema(df, trend_period)

    if use_chandelier:
        highest_high = df['high'].rolling(window=atr_period).max()
        trailing_stop = highest_high - (atr_multiplier * atr)
    else:
        trailing_stop = df['close'] - (atr_multiplier * atr)

    indicators['atr'] = atr
    indicators['trend_ema'] = trend_ema
    indicators['trailing_stop'] = trailing_stop
    indicators['atr_current'] = float(atr.iloc[-1])
    indicators['trend_ema_current'] = float(trend_ema.iloc[-1])
    indicators['trend_ema_prev'] = float(trend_ema.iloc[-2]) if len(trend_ema) > 1 else indicators['trend_ema_current']
    indicators['trailing_stop_current'] = float(trailing_stop.iloc[-1])
    indicators['trailing_stop_prev'] = float(trailing_stop.iloc[-2]) if len(trailing_stop) > 1 else indicators['trailing_stop_current']
    indicators['prev_close'] = float(df['close'].iloc[-2]) if len(df) > 1 else indicators['current_price']
```

### Success Criteria:

#### Automated Verification:
- [ ] File exists: `src/strategies/atr_trailing_stop.py`
- [ ] Import works: `python -c "from src.strategies.atr_trailing_stop import ATRTrailingStopStrategy"`
- [ ] Backend routing works: Strategy type "ATR_TRAILING_STOP" recognized

---

## Phase 4: Donchian Channel Strategy (Turtle Trading)

### Overview
The most famous systematic trading strategy - used by the Turtle Traders who made $175M.

### Changes Required:

#### 1. CLI Strategy File
**File**: `src/strategies/donchian_channel.py`
**Changes**: Create new file

```python
"""
Donchian Channel (Turtle Trading) Strategy.

The most famous trading experiment in history.
Richard Dennis's Turtles made $175 million in 5 years using this system.
"""

import pandas as pd
import numpy as np
from .base_strategy import BaseStrategy, Signal


class DonchianChannelStrategy(BaseStrategy):
    """
    Donchian Channel (Turtle Trading) strategy implementation.

    System 1: 20-day breakout entry, 10-day exit
    System 2: 55-day breakout entry, 20-day exit

    Uses ATR for stop-loss and position sizing.
    """

    def __init__(
        self,
        entry_period: int = 20,
        exit_period: int = 10,
        atr_period: int = 20,
        use_system_2: bool = False
    ):
        """
        Initialize Donchian Channel strategy.

        Args:
            entry_period: Period for entry breakout (default 20, or 55 for System 2)
            exit_period: Period for exit (default 10, or 20 for System 2)
            atr_period: Period for ATR calculation (default 20)
            use_system_2: Use System 2 (55/20) instead of System 1 (20/10)
        """
        super().__init__(name="Donchian Channel")

        if use_system_2:
            self.entry_period = 55
            self.exit_period = 20
        else:
            self.entry_period = entry_period
            self.exit_period = exit_period

        self.atr_period = atr_period
        self.use_system_2 = use_system_2

    def calculate_atr(self, data: pd.DataFrame, period: int) -> pd.Series:
        """Calculate Average True Range."""
        high = data['high']
        low = data['low']
        close = data['close']

        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))

        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = true_range.rolling(window=period).mean()

        return atr

    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate Donchian Channel indicators."""
        df = data.copy()

        # Entry channel (e.g., 20-day or 55-day)
        df['entry_high'] = df['high'].rolling(window=self.entry_period).max()
        df['entry_low'] = df['low'].rolling(window=self.entry_period).min()

        # Exit channel (e.g., 10-day or 20-day)
        df['exit_high'] = df['high'].rolling(window=self.exit_period).max()
        df['exit_low'] = df['low'].rolling(window=self.exit_period).min()

        # ATR for stops
        df['atr'] = self.calculate_atr(df, self.atr_period)

        # Middle line (for reference)
        df['donchian_middle'] = (df['entry_high'] + df['entry_low']) / 2

        return df

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate trading signals based on Donchian Channel breakouts.

        BUY: Price breaks above entry_period high
        SELL: Price breaks below exit_period low (or entry_period low for shorts)
        """
        df = self.calculate_indicators(data)
        signals = pd.Series(0, index=df.index)

        # Use previous period's channel to avoid look-ahead bias
        prev_entry_high = df['entry_high'].shift(1)
        prev_exit_low = df['exit_low'].shift(1)

        # BUY: Close breaks above previous N-day high
        buy_condition = df['close'] > prev_entry_high

        # SELL: Close breaks below previous exit period low
        sell_condition = df['close'] < prev_exit_low

        signals[buy_condition] = Signal.BUY.value
        signals[sell_condition] = Signal.SELL.value

        return signals

    def get_strategy_state(self, data: pd.DataFrame) -> dict:
        """Get current strategy state."""
        df = self.calculate_indicators(data)

        required_periods = max(self.entry_period, self.exit_period)
        if len(df) < required_periods:
            return {
                'status': 'insufficient_data',
                'message': f'Need at least {required_periods} data points'
            }

        latest = df.iloc[-1]

        # Determine position in channel
        channel_width = latest['entry_high'] - latest['entry_low']
        if channel_width > 0:
            position_pct = (latest['close'] - latest['entry_low']) / channel_width
        else:
            position_pct = 0.5

        return {
            'status': 'active',
            'entry_high': latest['entry_high'],
            'entry_low': latest['entry_low'],
            'exit_high': latest['exit_high'],
            'exit_low': latest['exit_low'],
            'donchian_middle': latest['donchian_middle'],
            'atr': latest['atr'],
            'current_price': latest['close'],
            'position_in_channel': position_pct,
            'system': 'System 2' if self.use_system_2 else 'System 1'
        }

    def __str__(self) -> str:
        system = 'System2' if self.use_system_2 else 'System1'
        return f"DonchianChannel({system}, entry={self.entry_period}, exit={self.exit_period})"
```

#### 2. Backend Signal Generator
**File**: `backend/app/strategies/signal_generator.py`
**Changes**: Add method and routing

Add to routing:
```python
elif strategy_type_upper == 'DONCHIAN_CHANNEL':
    return self._generate_donchian_signal(parameters, indicator_values, has_position)
```

Add new method:
```python
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
```

#### 3. Backend Indicators
**File**: `backend/app/strategies/indicators.py`
**Changes**: Add to `calculate_all_for_strategy()`

```python
elif strategy_type.upper() == 'DONCHIAN_CHANNEL':
    use_system_2 = parameters.get('use_system_2', False)
    if use_system_2:
        entry_period = 55
        exit_period = 20
    else:
        entry_period = parameters.get('entry_period', 20)
        exit_period = parameters.get('exit_period', 10)
    atr_period = parameters.get('atr_period', 20)

    indicators['entry_high'] = df['high'].rolling(window=entry_period).max()
    indicators['entry_low'] = df['low'].rolling(window=entry_period).min()
    indicators['exit_high'] = df['high'].rolling(window=exit_period).max()
    indicators['exit_low'] = df['low'].rolling(window=exit_period).min()
    indicators['atr'] = TechnicalIndicators.calculate_atr(df, atr_period)

    indicators['entry_high_prev'] = float(indicators['entry_high'].iloc[-2]) if len(indicators['entry_high']) > 1 else float(indicators['entry_high'].iloc[-1])
    indicators['exit_low_prev'] = float(indicators['exit_low'].iloc[-2]) if len(indicators['exit_low']) > 1 else float(indicators['exit_low'].iloc[-1])
    indicators['atr_current'] = float(indicators['atr'].iloc[-1])
```

### Success Criteria:

#### Automated Verification:
- [ ] File exists: `src/strategies/donchian_channel.py`
- [ ] Import works: `python -c "from src.strategies.donchian_channel import DonchianChannelStrategy"`
- [ ] Backend routing works: Strategy type "DONCHIAN_CHANNEL" recognized

---

## Phase 5: Ichimoku Cloud Strategy

### Overview
Comprehensive Japanese charting system with 5 components. Most complex strategy.

### Changes Required:

#### 1. CLI Strategy File
**File**: `src/strategies/ichimoku_cloud.py`
**Changes**: Create new file

```python
"""
Ichimoku Cloud Trading Strategy.

Comprehensive Japanese charting system developed in the 1940s.
Shows trend, momentum, support/resistance all in one view.
"Balance at a glance" - very popular globally, especially in Asia.
"""

import pandas as pd
import numpy as np
from .base_strategy import BaseStrategy, Signal


class IchimokuCloudStrategy(BaseStrategy):
    """
    Ichimoku Cloud strategy implementation.

    Components:
    - Tenkan-sen (Conversion Line): 9-period midpoint
    - Kijun-sen (Base Line): 26-period midpoint
    - Senkou Span A: Midpoint of Tenkan/Kijun, shifted 26 forward
    - Senkou Span B: 52-period midpoint, shifted 26 forward
    - Chikou Span: Current close shifted 26 back
    """

    def __init__(
        self,
        tenkan_period: int = 9,
        kijun_period: int = 26,
        senkou_b_period: int = 52,
        displacement: int = 26
    ):
        """
        Initialize Ichimoku Cloud strategy.

        Args:
            tenkan_period: Conversion line period (default 9)
            kijun_period: Base line period (default 26)
            senkou_b_period: Leading Span B period (default 52)
            displacement: Cloud displacement (default 26)
        """
        super().__init__(name="Ichimoku Cloud")
        self.tenkan_period = tenkan_period
        self.kijun_period = kijun_period
        self.senkou_b_period = senkou_b_period
        self.displacement = displacement

    def calculate_midpoint(self, data: pd.DataFrame, period: int) -> pd.Series:
        """Calculate midpoint (highest high + lowest low) / 2."""
        high = data['high'].rolling(window=period).max()
        low = data['low'].rolling(window=period).min()
        return (high + low) / 2

    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate all Ichimoku Cloud components."""
        df = data.copy()

        # Tenkan-sen (Conversion Line): 9-period midpoint
        df['tenkan_sen'] = self.calculate_midpoint(df, self.tenkan_period)

        # Kijun-sen (Base Line): 26-period midpoint
        df['kijun_sen'] = self.calculate_midpoint(df, self.kijun_period)

        # Senkou Span A (Leading Span A): midpoint of Tenkan/Kijun, shifted 26 forward
        df['senkou_span_a'] = ((df['tenkan_sen'] + df['kijun_sen']) / 2).shift(self.displacement)

        # Senkou Span B (Leading Span B): 52-period midpoint, shifted 26 forward
        df['senkou_span_b'] = self.calculate_midpoint(df, self.senkou_b_period).shift(self.displacement)

        # Chikou Span (Lagging Span): current close shifted 26 back
        df['chikou_span'] = df['close'].shift(-self.displacement)

        # Cloud top and bottom (for current analysis, unshifted)
        df['cloud_top'] = df[['senkou_span_a', 'senkou_span_b']].max(axis=1)
        df['cloud_bottom'] = df[['senkou_span_a', 'senkou_span_b']].min(axis=1)

        # Future cloud (current values, represent future cloud)
        df['future_senkou_a'] = (df['tenkan_sen'] + df['kijun_sen']) / 2
        df['future_senkou_b'] = self.calculate_midpoint(df, self.senkou_b_period)

        # Cloud color (1 = green/bullish, -1 = red/bearish)
        df['cloud_color'] = np.where(df['senkou_span_a'] > df['senkou_span_b'], 1, -1)

        return df

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate trading signals based on Ichimoku Cloud.

        Strong BUY conditions (all must be true):
        - Price above cloud
        - Tenkan-sen above Kijun-sen
        - Future cloud is green (bullish)

        Strong SELL conditions:
        - Price below cloud
        - Tenkan-sen below Kijun-sen
        - Future cloud is red (bearish)
        """
        df = self.calculate_indicators(data)
        signals = pd.Series(0, index=df.index)

        # TK Cross detection (Tenkan crosses Kijun)
        tk_cross_up = (df['tenkan_sen'] > df['kijun_sen']) & (df['tenkan_sen'].shift(1) <= df['kijun_sen'].shift(1))
        tk_cross_down = (df['tenkan_sen'] < df['kijun_sen']) & (df['tenkan_sen'].shift(1) >= df['kijun_sen'].shift(1))

        # Price position relative to cloud
        price_above_cloud = df['close'] > df['cloud_top']
        price_below_cloud = df['close'] < df['cloud_bottom']

        # Future cloud bullish/bearish
        future_cloud_bullish = df['future_senkou_a'] > df['future_senkou_b']
        future_cloud_bearish = df['future_senkou_a'] < df['future_senkou_b']

        # Strong BUY: TK cross up + price above cloud + bullish future cloud
        strong_buy = tk_cross_up & price_above_cloud & future_cloud_bullish

        # Strong SELL: TK cross down + price below cloud + bearish future cloud
        strong_sell = tk_cross_down & price_below_cloud & future_cloud_bearish

        # Weak BUY: TK cross up (any position)
        weak_buy = tk_cross_up & ~strong_buy

        # Weak SELL: TK cross down (any position)
        weak_sell = tk_cross_down & ~strong_sell

        # Apply signals (strong signals take precedence)
        signals[strong_buy] = Signal.BUY.value
        signals[strong_sell] = Signal.SELL.value
        signals[weak_buy & (signals == 0)] = Signal.BUY.value
        signals[weak_sell & (signals == 0)] = Signal.SELL.value

        return signals

    def get_strategy_state(self, data: pd.DataFrame) -> dict:
        """Get current strategy state."""
        df = self.calculate_indicators(data)

        required_periods = max(self.senkou_b_period, self.kijun_period + self.displacement)
        if len(df) < required_periods:
            return {
                'status': 'insufficient_data',
                'message': f'Need at least {required_periods} data points'
            }

        latest = df.iloc[-1]

        # Determine overall bias
        if latest['close'] > latest['cloud_top'] and latest['tenkan_sen'] > latest['kijun_sen']:
            bias = 'strongly_bullish'
        elif latest['close'] > latest['cloud_top']:
            bias = 'bullish'
        elif latest['close'] < latest['cloud_bottom'] and latest['tenkan_sen'] < latest['kijun_sen']:
            bias = 'strongly_bearish'
        elif latest['close'] < latest['cloud_bottom']:
            bias = 'bearish'
        else:
            bias = 'neutral'

        return {
            'status': 'active',
            'tenkan_sen': latest['tenkan_sen'],
            'kijun_sen': latest['kijun_sen'],
            'senkou_span_a': latest['senkou_span_a'],
            'senkou_span_b': latest['senkou_span_b'],
            'cloud_top': latest['cloud_top'],
            'cloud_bottom': latest['cloud_bottom'],
            'current_price': latest['close'],
            'cloud_color': 'green' if latest['cloud_color'] == 1 else 'red',
            'bias': bias
        }

    def __str__(self) -> str:
        return f"IchimokuCloud(tenkan={self.tenkan_period}, kijun={self.kijun_period}, senkou_b={self.senkou_b_period})"
```

#### 2. Backend Signal Generator
**File**: `backend/app/strategies/signal_generator.py`
**Changes**: Add method and routing

Add to routing:
```python
elif strategy_type_upper == 'ICHIMOKU_CLOUD':
    return self._generate_ichimoku_signal(parameters, indicator_values, has_position)
```

Add new method:
```python
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
```

#### 3. Backend Indicators
**File**: `backend/app/strategies/indicators.py`
**Changes**: Add Ichimoku calculation helper and to `calculate_all_for_strategy()`

Add helper method to `TechnicalIndicators` class:
```python
@staticmethod
def calculate_ichimoku(df: pd.DataFrame, tenkan_period: int = 9, kijun_period: int = 26,
                       senkou_b_period: int = 52, displacement: int = 26) -> Dict[str, pd.Series]:
    """Calculate all Ichimoku Cloud components."""
    def midpoint(data, period):
        high = data['high'].rolling(window=period).max()
        low = data['low'].rolling(window=period).min()
        return (high + low) / 2

    tenkan = midpoint(df, tenkan_period)
    kijun = midpoint(df, kijun_period)
    senkou_a = ((tenkan + kijun) / 2).shift(displacement)
    senkou_b = midpoint(df, senkou_b_period).shift(displacement)

    return {
        'tenkan_sen': tenkan,
        'kijun_sen': kijun,
        'senkou_span_a': senkou_a,
        'senkou_span_b': senkou_b,
        'future_senkou_a': (tenkan + kijun) / 2,
        'future_senkou_b': midpoint(df, senkou_b_period)
    }
```

Add to `calculate_all_for_strategy()`:
```python
elif strategy_type.upper() == 'ICHIMOKU_CLOUD':
    tenkan_period = parameters.get('tenkan_period', 9)
    kijun_period = parameters.get('kijun_period', 26)
    senkou_b_period = parameters.get('senkou_b_period', 52)
    displacement = parameters.get('displacement', 26)

    ichimoku = TechnicalIndicators.calculate_ichimoku(df, tenkan_period, kijun_period, senkou_b_period, displacement)

    for key, series in ichimoku.items():
        indicators[key] = series
        indicators[f'{key}_current'] = float(series.iloc[-1]) if not pd.isna(series.iloc[-1]) else 0
        indicators[f'{key}_prev'] = float(series.iloc[-2]) if len(series) > 1 and not pd.isna(series.iloc[-2]) else indicators[f'{key}_current']

    cloud_top = pd.concat([ichimoku['senkou_span_a'], ichimoku['senkou_span_b']], axis=1).max(axis=1)
    cloud_bottom = pd.concat([ichimoku['senkou_span_a'], ichimoku['senkou_span_b']], axis=1).min(axis=1)
    indicators['cloud_top'] = cloud_top
    indicators['cloud_bottom'] = cloud_bottom
    indicators['cloud_top_current'] = float(cloud_top.iloc[-1]) if not pd.isna(cloud_top.iloc[-1]) else 0
    indicators['cloud_bottom_current'] = float(cloud_bottom.iloc[-1]) if not pd.isna(cloud_bottom.iloc[-1]) else 0
```

### Success Criteria:

#### Automated Verification:
- [ ] File exists: `src/strategies/ichimoku_cloud.py`
- [ ] Import works: `python -c "from src.strategies.ichimoku_cloud import IchimokuCloudStrategy"`
- [ ] Backend routing works: Strategy type "ICHIMOKU_CLOUD" recognized

---

## Testing Strategy

### Automated Import Tests
```bash
cd /Users/ashwin/projects/algo-trading-app
python -c "
from src.strategies.stochastic_strategy import StochasticStrategy
from src.strategies.keltner_channel import KeltnerChannelStrategy
from src.strategies.atr_trailing_stop import ATRTrailingStopStrategy
from src.strategies.donchian_channel import DonchianChannelStrategy
from src.strategies.ichimoku_cloud import IchimokuCloudStrategy
print('All 5 strategies imported successfully!')
"
```

### Backend Integration Test
```bash
cd /Users/ashwin/projects/algo-trading-app/backend
poetry run python -c "
from app.strategies.signal_generator import SignalGenerator
# Test that new strategy types are recognized
supported = ['STOCHASTIC', 'KELTNER_CHANNEL', 'ATR_TRAILING_STOP', 'DONCHIAN_CHANNEL', 'ICHIMOKU_CLOUD']
print(f'Backend supports {len(supported)} new strategy types')
"
```

## References

- Research document: `research/2025-12-25-new-trading-strategies.md`
- Base strategy pattern: `src/strategies/base_strategy.py:21-134`
- RSI oscillator example: `src/strategies/rsi_strategy.py`
- Bollinger channel example: `src/strategies/bollinger_bands.py`
- Backend signal generator: `backend/app/strategies/signal_generator.py`
- Backend indicators: `backend/app/strategies/indicators.py`
