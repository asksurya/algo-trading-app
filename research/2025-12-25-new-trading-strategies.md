---
date: 2025-12-25T23:05:00-08:00
researcher: claude
git_commit: ff63e54a990737296b34d5dd612260c16bb38256
branch: main
repository: algo-trading-app
topic: "New Trading Strategies Research - 5 Missing Popular Strategies"
tags: [research, trading-strategies, technical-analysis, implementation]
status: complete
last_updated: 2025-12-25
---

# Research: New Trading Strategies to Implement

**Date**: 2025-12-25T23:05:00-08:00
**Git Commit**: ff63e54a990737296b34d5dd612260c16bb38256
**Branch**: main
**Repository**: algo-trading-app

## Research Question

Identify 5 famous and commonly used trading strategies that are NOT currently implemented in the codebase, for potential implementation.

## Summary

The codebase currently has **11 strategies**. After researching 22+ popular global strategies, I've identified **5 high-value strategies** to add that are:
- Widely used and proven in production
- Not duplicating existing functionality
- Complementary to existing strategy categories
- Implementable with available technical indicators

## Current Strategies Inventory

| # | Strategy | Type | Backend Support | Location |
|---|----------|------|-----------------|----------|
| 1 | SMA Crossover | Trend Following | ✅ Yes | `src/strategies/sma_crossover.py` |
| 2 | RSI | Mean Reversion | ✅ Yes | `src/strategies/rsi_strategy.py` |
| 3 | MACD | Trend/Momentum | ✅ Yes | `src/strategies/macd_strategy.py` |
| 4 | Bollinger Bands | Mean Reversion | ✅ Yes | `src/strategies/bollinger_bands.py` |
| 5 | VWAP | Volume-Based | ❌ CLI only | `src/strategies/vwap_strategy.py` |
| 6 | Momentum | Trend Following | ❌ CLI only | `src/strategies/momentum_strategy.py` |
| 7 | Breakout | Trend Following | ❌ CLI only | `src/strategies/breakout_strategy.py` |
| 8 | Mean Reversion | Statistical | ✅ Yes | `src/strategies/mean_reversion.py` |
| 9 | Pairs Trading | Stat Arb | ❌ CLI only | `src/strategies/pairs_trading.py` |
| 10 | ML Strategy | Ensemble | ❌ CLI only | `src/strategies/ml_strategy.py` |
| 11 | Adaptive ML | Random Forest | ❌ CLI only | `src/strategies/adaptive_ml_strategy.py` |

### Coverage Analysis

**Well Covered:**
- Trend Following: SMA, MACD, Momentum, Breakout
- Mean Reversion: RSI, Bollinger, Mean Reversion, Pairs
- Machine Learning: ML Strategy, Adaptive ML

**Gaps Identified:**
- No Donchian Channel / Turtle Trading (most famous systematic strategy ever)
- No Ichimoku Cloud (comprehensive Asian system)
- No Stochastic Oscillator (classic momentum oscillator)
- No ATR-based strategies (volatility-adjusted systems)
- No Keltner Channels (ATR-based bands)
- No Parabolic SAR (trailing stops)
- No CCI (Commodity Channel Index)

---

## Recommended 5 New Strategies

### 1. Donchian Channel Strategy (Turtle Trading)

**Why Add This:**
- The most famous trading experiment in history (Richard Dennis's Turtles made $175M in 5 years)
- Proven systematic approach with clear rules
- Works across all asset classes including stocks, crypto, forex
- Simple yet effective trend-following system

**How It Works:**
- **Entry:** Buy when price breaks 20-day high (System 1) or 55-day high (System 2)
- **Entry:** Sell/short when price breaks 20-day low or 55-day low
- **Stop Loss:** 2× ATR from entry price
- **Position Sizing:** Risk 2% of capital per trade, size based on ATR

**Key Parameters:**
```python
entry_period: int = 20      # Breakout period (20 or 55)
exit_period: int = 10       # Exit at 10-day low/high
atr_period: int = 20        # ATR for stops
risk_per_trade: float = 0.02  # 2% risk
```

**Indicators Required:**
- Donchian Channel (N-period high/low)
- ATR (Average True Range)

**Expected Files:**
- `src/strategies/donchian_channel.py`
- Backend: `backend/app/strategies/signal_generator.py` (add method)

---

### 2. Ichimoku Cloud Strategy

**Why Add This:**
- Comprehensive all-in-one system showing trend, momentum, support/resistance
- Very popular globally, especially in Asian markets
- Provides clear visual signals for entry/exit
- "Balance at a glance" - developed 1940s, still widely used

**How It Works:**
- **Components:**
  - Tenkan-sen (Conversion Line): 9-period midpoint
  - Kijun-sen (Base Line): 26-period midpoint
  - Senkou Span A: Midpoint of Tenkan/Kijun, shifted 26 periods forward
  - Senkou Span B: 52-period midpoint, shifted 26 periods forward
  - Chikou Span: Current close shifted 26 periods back

- **Signals:**
  - **Bullish:** Price above cloud, Tenkan crosses above Kijun, Chikou above price
  - **Bearish:** Price below cloud, Tenkan crosses below Kijun, Chikou below price
  - **Cloud:** Green (bullish bias), Red (bearish bias)

**Key Parameters:**
```python
tenkan_period: int = 9      # Conversion line period
kijun_period: int = 26      # Base line period
senkou_b_period: int = 52   # Leading span B period
displacement: int = 26      # Cloud displacement
```

**Indicators Required:**
- All 5 Ichimoku components (custom calculation)
- No external dependencies

**Expected Files:**
- `src/strategies/ichimoku_cloud.py`
- Backend: `backend/app/strategies/signal_generator.py` (add method)

---

### 3. Stochastic Oscillator Strategy

**Why Add This:**
- Classic momentum oscillator (developed by George Lane in 1950s)
- Complements RSI with different calculation method
- Very effective for identifying overbought/oversold conditions
- Widely used by retail and institutional traders

**How It Works:**
- **Stochastic %K:** `100 × (Close - Low_N) / (High_N - Low_N)`
- **Stochastic %D:** 3-period SMA of %K (signal line)
- **Buy Signal:** %K crosses above %D below 20 (oversold)
- **Sell Signal:** %K crosses below %D above 80 (overbought)
- **Divergence:** Price vs stochastic divergence for trend reversal

**Key Parameters:**
```python
k_period: int = 14        # %K lookback period
d_period: int = 3         # %D smoothing period
oversold: int = 20        # Oversold threshold
overbought: int = 80      # Overbought threshold
smooth_k: int = 3         # Optional %K smoothing (slow stochastic)
```

**Indicators Required:**
- Stochastic %K and %D (standard calculation)

**Expected Files:**
- `src/strategies/stochastic_strategy.py`
- Backend: `backend/app/strategies/signal_generator.py` (add method)

---

### 4. ATR Trailing Stop Strategy

**Why Add This:**
- Volatility-adjusted position management
- Used by professional traders for dynamic stop-loss
- Can be combined with any entry strategy
- Adapts automatically to market conditions

**How It Works:**
- **Entry:** Based on trend confirmation (price above/below EMA)
- **Initial Stop:** 3× ATR from entry price
- **Trailing Stop:** Moves up/down with price, never against position
- **Exit:** When price crosses trailing stop level
- **Chandelier Exit Variant:** ATR-based stop from highest high

**Key Parameters:**
```python
atr_period: int = 14        # ATR calculation period
atr_multiplier: float = 3.0 # Stop distance multiplier
trend_period: int = 50      # EMA for trend filter
use_chandelier: bool = True # Use highest high for stops
```

**Indicators Required:**
- ATR (Average True Range)
- EMA (Exponential Moving Average)

**Expected Files:**
- `src/strategies/atr_trailing_stop.py`
- Backend: `backend/app/strategies/signal_generator.py` (add method)

---

### 5. Keltner Channel Strategy

**Why Add This:**
- Volatility-based channel (like Bollinger but uses ATR)
- Less sensitive to outliers than standard deviation
- Clear breakout and mean reversion signals
- Works well for range-bound and trending markets

**How It Works:**
- **Middle Line:** 20-period EMA
- **Upper Band:** EMA + (ATR × multiplier)
- **Lower Band:** EMA - (ATR × multiplier)
- **Breakout Entry:** Buy when close breaks above upper band, sell when breaks below lower
- **Mean Reversion:** Buy at lower band, sell at upper band (in ranges)
- **Squeeze:** When Bollinger inside Keltner = low volatility, expect breakout

**Key Parameters:**
```python
ema_period: int = 20        # Middle line EMA period
atr_period: int = 10        # ATR period for bands
multiplier: float = 2.0     # Band width multiplier
use_breakout: bool = True   # Breakout mode (vs mean reversion)
```

**Indicators Required:**
- EMA (Exponential Moving Average)
- ATR (Average True Range)

**Expected Files:**
- `src/strategies/keltner_channel.py`
- Backend: `backend/app/strategies/signal_generator.py` (add method)

---

## Implementation Priority

| Priority | Strategy | Complexity | Reason |
|----------|----------|------------|--------|
| 1 | Stochastic Oscillator | ⭐⭐ Low | Simple, no new indicators needed, complements RSI |
| 2 | Keltner Channel | ⭐⭐ Low | Uses existing EMA/ATR, similar pattern to Bollinger |
| 3 | ATR Trailing Stop | ⭐⭐⭐ Medium | New trailing stop logic, but uses existing ATR |
| 4 | Donchian Channel | ⭐⭐⭐ Medium | New indicator calculation, position sizing logic |
| 5 | Ichimoku Cloud | ⭐⭐⭐⭐ High | 5 components to calculate, complex signal logic |

## Code References

### Base Strategy Pattern
- `src/strategies/base_strategy.py:21-134` - BaseStrategy abstract class
- `src/strategies/base_strategy.py:36` - `generate_signals()` abstract method
- `src/strategies/base_strategy.py:49` - `calculate_indicators()` abstract method

### Existing Similar Implementations
- `src/strategies/bollinger_bands.py` - Reference for channel-based strategy (Keltner)
- `src/strategies/rsi_strategy.py` - Reference for oscillator-based strategy (Stochastic)
- `src/strategies/breakout_strategy.py` - Reference for breakout logic (Donchian)
- `src/strategies/momentum_strategy.py` - Reference for trend-following (Ichimoku)

### Backend Signal Generator
- `backend/app/strategies/signal_generator.py:24` - SignalGenerator class
- `backend/app/strategies/signal_generator.py:33` - `generate_signal()` main method
- Strategy implementations: lines 76-302

### Technical Indicators Available
- `backend/app/services/technical_indicators.py` - Existing indicator calculations
- Uses pandas-ta library for most indicators

## Architecture Insights

### Strategy Pattern
All strategies follow the same pattern:
1. Inherit from `BaseStrategy`
2. Implement `calculate_indicators(data)` → returns DataFrame with indicators
3. Implement `generate_signals(data)` → returns Series with BUY/SELL/HOLD
4. Use `Signal` enum (BUY=1, SELL=-1, HOLD=0)

### Backend Integration
To add backend support:
1. Add method to `SignalGenerator` class (e.g., `_generate_stochastic_signal`)
2. Add strategy type to the match statement in `generate_signal()`
3. Return tuple: `(SignalType, strength, reasoning, indicator_values)`

### Required Indicator Calculations
For new strategies, ensure these are available in `TechnicalIndicators`:
- Stochastic: May need to add if not present
- Donchian Channel: May need to add (highest high, lowest low)
- Ichimoku: Will need to add all 5 components
- Keltner: Can compose from existing EMA + ATR

## Strategies Considered but Not Recommended

| Strategy | Reason Not Selected |
|----------|---------------------|
| Elliott Wave | Too subjective, hard to automate reliably |
| Grid Trading | Requires different execution model (continuous orders) |
| Market Making/HFT | Requires microsecond execution, not suitable for retail |
| Triangular Arbitrage | Requires multi-exchange setup, crypto-specific |
| Volatility Arbitrage | Requires options data, not in current data model |
| Pairs Trading (Advanced) | Already have simplified version |

## Open Questions

1. **Backend Priority:** Should all 5 strategies be added to backend SignalGenerator, or only CLI initially?
2. **Position Sizing:** Should ATR-based position sizing be standardized across all strategies?
3. **Ichimoku Complexity:** Consider implementing as two variants (simple cloud-only vs full 5-component)?
4. **Testing:** What test data/symbols should be used for backtesting new strategies?

## Next Steps

1. Create strategy files following existing patterns
2. Implement indicator calculations in TechnicalIndicators if needed
3. Add backend support to SignalGenerator
4. Write unit tests for each strategy
5. Run backtests to validate performance
6. Update frontend to display new strategy options
