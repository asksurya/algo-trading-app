# Trading Strategies Guide

## Currently Implemented

### 1. SMA Crossover (Moving Average Crossover)
**Type**: Trend Following  
**How it works**: 
- Buy when short-term MA crosses above long-term MA (Golden Cross)
- Sell when short-term MA crosses below long-term MA (Death Cross)

**Pros**: Simple, works well in trending markets  
**Cons**: Lags behind price, generates false signals in sideways markets  
**Best for**: Strong trending stocks, longer timeframes

**Parameters**:
- Short window: 20-50 days (default: 50)
- Long window: 100-200 days (default: 200)

### 2. RSI (Relative Strength Index)
**Type**: Mean Reversion  
**How it works**:
- Buy when RSI falls below oversold threshold (typically 30)
- Sell when RSI rises above overbought threshold (typically 70)

**Pros**: Works well in ranging markets, catches reversals  
**Cons**: Can give early signals in strong trends  
**Best for**: Volatile stocks, shorter timeframes

**Parameters**:
- Period: 14 days (default)
- Oversold: 30 (default)
- Overbought: 70 (default)

## Popular Strategies to Implement

### 3. MACD (Moving Average Convergence Divergence)
**Type**: Trend Following + Momentum  
**Complexity**: ⭐⭐⭐

**How it works**:
- MACD Line = 12-day EMA - 26-day EMA
- Signal Line = 9-day EMA of MACD
- Buy when MACD crosses above signal line
- Sell when MACD crosses below signal line

**Pros**: Combines trend and momentum, fewer false signals  
**Cons**: Still lags, complex to tune  
**Best for**: Medium to long-term trading

### 4. Bollinger Bands
**Type**: Volatility/Mean Reversion  
**Complexity**: ⭐⭐

**How it works**:
- Middle band = 20-day SMA
- Upper/Lower bands = Middle ± (2 × standard deviation)
- Buy when price touches lower band
- Sell when price touches upper band

**Pros**: Adapts to volatility, visual  
**Cons**: Whipsaws in trending markets  
**Best for**: Range-bound markets, high volatility stocks

### 5. Momentum Strategy
**Type**: Momentum  
**Complexity**: ⭐⭐

**How it works**:
- Calculate rate of price change over N periods
- Buy when momentum is positive and increasing
- Sell when momentum turns negative

**Pros**: Catches strong trends early  
**Cons**: Can reverse quickly  
**Best for**: Growth stocks, tech sector

### 6. Mean Reversion (Statistical Arbitrage)
**Type**: Mean Reversion  
**Complexity**: ⭐⭐⭐⭐

**How it works**:
- Calculate z-score: (Price - Mean) / Std Dev
- Buy when z-score < -2 (oversold)
- Sell when z-score > 2 (overbought)

**Pros**: Mathematical rigor, works in sideways markets  
**Cons**: Fails in trending markets  
**Best for**: Stable stocks, pairs trading

### 7. Breakout Strategy
**Type**: Trend Following  
**Complexity**: ⭐⭐

**How it works**:
- Identify support/resistance levels (52-week high/low, pivot points)
- Buy on breakout above resistance
- Sell on breakdown below support

**Pros**: Catches big moves, clear signals  
**Cons**: Many false breakouts  
**Best for**: High volume stocks, earnings plays

### 8. Volume-Weighted Average Price (VWAP)
**Type**: Intraday/Institutional  
**Complexity**: ⭐⭐⭐

**How it works**:
- VWAP = Cumulative (Price × Volume) / Cumulative Volume
- Buy when price crosses above VWAP
- Sell when price crosses below VWAP

**Pros**: Institutional benchmark, liquidity indicator  
**Cons**: Only for intraday, resets daily  
**Best for**: Day trading, high-frequency trading

### 9. Pairs Trading
**Type**: Market Neutral/Statistical Arbitrage  
**Complexity**: ⭐⭐⭐⭐⭐

**How it works**:
- Find correlated pairs (e.g., Coke vs Pepsi)
- Calculate spread = Stock A - β × Stock B
- Long when spread is low, short when high

**Pros**: Market neutral, reduces risk  
**Cons**: Complex, requires sophisticated risk management  
**Best for**: Hedge funds, professional traders

### 10. Machine Learning Based
**Type**: Predictive  
**Complexity**: ⭐⭐⭐⭐⭐

**How it works**:
- Use ML models (Random Forest, Neural Networks, etc.)
- Train on historical features (price, volume, indicators)
- Predict future price movement

**Pros**: Can capture complex patterns  
**Cons**: Overfitting risk, requires lots of data  
**Best for**: Quant funds, data scientists

## Strategy Selection Guide

### For Beginners:
1. RSI (easiest to understand)
2. SMA Crossover (simple trend following)
3. Bollinger Bands (visual and intuitive)

### For Trending Markets:
1. SMA Crossover
2. MACD
3. Breakout Strategy
4. Momentum

### For Range-Bound Markets:
1. RSI
2. Bollinger Bands
3. Mean Reversion
4. VWAP (intraday)

### For Professional Trading:
1. Pairs Trading
2. Statistical Arbitrage
3. Machine Learning
4. Multi-factor models

## Combining Strategies

**Strategy Stacking**: Use multiple strategies together
- Example: SMA for trend + RSI for entry timing
- Entry: SMA bullish AND RSI oversold
- Exit: SMA bearish OR RSI overbought

**Multi-Timeframe**: Same strategy, different timeframes
- Example: Daily SMA for trend, 1-hour RSI for entry
- Reduces false signals, improves timing

**Ensemble Methods**: Combine multiple signals
- Vote-based: Take position when majority agree
- Weighted: Different weights for different strategies
- Confidence-based: Size positions based on signal strength

## Risk Management Tips

1. **Position Sizing**: Never risk more than 1-2% per trade
2. **Stop Losses**: Always use stops (typically 5-10%)
3. **Diversification**: Don't put all capital in one strategy
4. **Backtesting**: Test strategies on at least 2-3 years of data
5. **Walk-Forward Testing**: Test on out-of-sample data
6. **Paper Trading**: Always paper trade before going live

## Common Mistakes to Avoid

1. **Overfitting**: Strategy works perfectly on historical data but fails live
2. **Ignoring Transaction Costs**: Commissions and slippage matter
3. **No Stop Losses**: One bad trade can wipe out months of gains
4. **Too Frequent Trading**: More trades = more costs
5. **Not Adapting**: Markets change, strategies need updates

## Next Steps

To implement a new strategy in this application:

1. Create new file in `src/strategies/` (e.g., `macd_strategy.py`)
2. Inherit from `BaseStrategy`
3. Implement `generate_signals()` method
4. Add to `main.py` command options
5. Backtest and optimize parameters
6. Paper trade before going live

See `src/strategies/sma_crossover.py` for a reference implementation.
