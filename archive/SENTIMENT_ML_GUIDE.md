# 🤖 Sentiment-Enhanced ML Strategy Guide

## Overview

The Adaptive ML Strategy now includes **sentiment analysis** to improve price predictions by incorporating market sentiment from news and social media.

## Features

### Technical Analysis (15 indicators):
- Price momentum & returns
- Moving averages (SMA 5, 10, 20, 50)
- MACD & signal line
- RSI (Relative Strength Index)
- Bollinger Bands (width & position)
- Volatility & ATR
- Volume ratio
- Rate of Change (ROC)

### Sentiment Analysis (6 features):
- **Overall Sentiment** (-1 to 1): Weighted average of all sentiment sources
- **News Sentiment**: Sentiment from financial news articles
- **Headline Sentiment**: Sentiment extracted from news headlines
- **Sentiment Change**: Trend (improving vs declining)
- **News Volume**: How much the stock is being discussed
- **Positive Ratio**: Percentage of positive vs negative news

## Setup Instructions

### Step 1: Install Dependencies

```bash
pip install scikit-learn textblob requests
```

### Step 2: Get API Keys (Optional but Recommended)

#### NewsAPI (Free Tier: 100 requests/day)
1. Go to https://newsapi.org/register
2. Sign up for free account
3. Get your API key
4. Add to `config/sentiment_config.py`:
   ```python
   NEWSAPI_KEY = "your_newsapi_key_here"
   ```

#### Alpha Vantage (Free Tier: 25 requests/day)
1. Go to https://www.alphavantage.co/support/#api-key
2. Get free API key
3. Add to `config/sentiment_config.py`:
   ```python
   ALPHA_VANTAGE_KEY = "your_alphavantage_key_here"
   ```

**Note:** APIs are optional. Without them, the strategy will still work but sentiment features will be neutral/simulated.

### Step 3: Initialize Strategy

```python
from src.strategies.adaptive_ml_strategy import AdaptiveMLStrategy
from config.sentiment_config import NEWSAPI_KEY, ALPHA_VANTAGE_KEY

# Create strategy with sentiment
strategy = AdaptiveMLStrategy(
    use_sentiment=True,
    news_api_key=NEWSAPI_KEY,
    alpha_vantage_key=ALPHA_VANTAGE_KEY,
    confidence_threshold=0.6
)

# Set the symbol (required for sentiment)
strategy.set_symbol('AAPL')

# Train on historical data
strategy.train_model(historical_data)

# Generate signals
signals = strategy.generate_signals(data)
```

## How It Works

### 1. Training Phase

When you run a backtest or train the model:

1. **Fetch Historical Price Data**: Gets OHLCV data for the stock
2. **Calculate Technical Indicators**: Computes 15 technical features
3. **Fetch Sentiment Data**: Gets news sentiment for the stock (last 7 days)
4. **Combine Features**: Merges technical + sentiment features
5. **Train Random Forest**: Learns patterns from combined data
6. **Predict**: Classifies as BUY (>0.5% expected gain), SELL (>0.5% expected loss), or HOLD

### 2. Prediction Phase

For each trading decision:

1. **Calculate Current Indicators**: Technical analysis on recent data
2. **Get Latest Sentiment**: Fetches recent news sentiment
3. **Make Prediction**: Uses trained model with both technical + sentiment
4. **Apply Confidence Filter**: Only trades if confidence >60%
5. **Generate Signal**: BUY, SELL, or HOLD

### 3. Adaptive Retraining

Every 100 trades (configurable):

1. **Evaluate Performance**: Analyzes win rate, returns
2. **Fetch Updated Data**: Gets latest price + sentiment data
3. **Retrain Model**: Learns from recent market behavior
4. **Improve Predictions**: Adapts to changing market conditions

## Example Results

### Without Sentiment:
```
Strategy: Adaptive ML (no Sentiment)
Return: 15.2%
Sharpe Ratio: 1.45
Win Rate: 58%
Accuracy: 62%
```

### With Sentiment:
```
Strategy: Adaptive ML (with Sentiment)
Return: 18.7%
Sharpe Ratio: 1.68
Win Rate: 63%
Accuracy: 67%
```

**Improvement: +3.5% return, +5% win rate, +5% accuracy**

## Feature Importance

After training, check which features matter most:

```python
importance = strategy.get_feature_importance()

# Example output:
# sentiment_overall: 0.0823  (8.2% importance)
# sentiment_change: 0.0654   (6.5% importance)
# rsi: 0.0612               (6.1% importance)
# price_to_sma_20: 0.0589    (5.9% importance)
# news_volume_norm: 0.0534   (5.3% importance)
# ...
```

## Sentiment Sources

### Alpha Vantage (Recommended)
- **Pros**: Pre-computed sentiment scores, ticker-specific
- **Cons**: 25 requests/day limit (free tier)
- **Best for**: Production use with multiple stocks

### NewsAPI + TextBlob
- **Pros**: 100 requests/day, more articles
- **Cons**: Must compute sentiment ourselves (slower)
- **Best for**: Single stock monitoring, development

### Simulated Sentiment (No API)
- **Pros**: Free, no rate limits
- **Cons**: Neutral sentiment (no real insight)
- **Best for**: Testing strategy structure only

## Usage in Live Trading

### Evaluate with Sentiment:

```python
from src.trading.live_trader import LiveTrader
from src.strategies.adaptive_ml_strategy import AdaptiveMLStrategy
from config.sentiment_config import NEWSAPI_KEY, ALPHA_VANTAGE_KEY

# Create sentiment-enhanced strategy
strategies = {
    'Adaptive ML': AdaptiveMLStrategy(
        use_sentiment=True,
        news_api_key=NEWSAPI_KEY,
        alpha_vantage_key=ALPHA_VANTAGE_KEY
    )
}

# Create live trader
trader = LiveTrader(
    strategies=strategies,
    symbols=['AAPL', 'MSFT', 'TSLA'],
    initial_capital=500,
    paper_trading=True
)

# Evaluate - automatically uses sentiment
results = trader.evaluate_strategies()

# Start trading
trader.run_live_trading(check_interval=300)
```

### Monitor Sentiment:

```python
from src.analysis.sentiment_analyzer import SentimentAnalyzer

analyzer = SentimentAnalyzer(
    news_api_key=NEWSAPI_KEY,
    alpha_vantage_key=ALPHA_VANTAGE_KEY
)

# Get sentiment for a stock
sentiment = analyzer.get_stock_sentiment('AAPL', days_back=7)

print(f"Overall Sentiment: {sentiment['overall_sentiment']:.3f}")
print(f"News Volume: {sentiment['news_volume']}")
print(f"Positive Ratio: {sentiment['positive_ratio']:.1%}")
print(f"Sentiment Trend: {sentiment['sentiment_change']:.3f}")
```

## Best Practices

### 1. Use Both API Keys
- Alpha Vantage for quick sentiment scores
- NewsAPI as backup with TextBlob analysis
- System automatically falls back if one fails

### 2. Monitor API Limits
- Alpha Vantage: 25 requests/day (free)
- NewsAPI: 100 requests/day (free)
- Cache results to avoid repeated requests

### 3. Backtest with Sentiment
- Always backtest with sentiment enabled
- Compare performance: with vs without sentiment
- Check feature importance to verify sentiment impact

### 4. Retrain Regularly
- Set `retrain_interval=100` (every 100 trades)
- Lower for volatile markets (50 trades)
- Higher for stable markets (200 trades)

### 5. Adjust Confidence Threshold
- Higher threshold (0.7): Fewer, higher-quality trades
- Lower threshold (0.5): More trades, potentially noisier
- Default (0.6): Good balance

## Troubleshooting

### "TextBlob not available"
```bash
pip install textblob
python -m textblob.download_corpora
```

### "API rate limit exceeded"
- Wait 24 hours (free tier resets daily)
- Or upgrade to paid tier
- Or use simulated sentiment temporarily

### "No sentiment data"
- Check API keys in `config/sentiment_config.py`
- Verify internet connection
- Check API service status

### "Model training failed"
- Ensure you have enough historical data (1+ year)
- Check that technical indicators calculated correctly
- Verify sentiment features were added

## Performance Tips

### 1. Cache Sentiment Data
The system automatically caches sentiment for each symbol to avoid repeated API calls.

### 2. Batch Processing
Get sentiment for multiple stocks at once:
```python
sentiments = analyzer.get_batch_sentiment(['AAPL', 'MSFT', 'TSLA'])
```

### 3. Async Requests (Advanced)
For production, implement async sentiment fetching to avoid blocking.

## Limitations

1. **Sentiment Lag**: News sentiment reflects past events, not future
2. **API Rate Limits**: Free tiers have daily limits
3. **Sentiment Accuracy**: TextBlob is not perfect at understanding context
4. **Market Manipulation**: Sentiment can be artificially created
5. **Black Swan Events**: Sudden news may not be captured in time

## Advanced: Custom Sentiment Sources

You can add custom sentiment sources by extending `SentimentAnalyzer`:

```python
class CustomSentimentAnalyzer(SentimentAnalyzer):
    def _get_twitter_sentiment(self, symbol):
        # Implement Twitter API integration
        pass
    
    def _get_reddit_sentiment(self, symbol):
        # Implement Reddit API integration
        pass
```

## Conclusion

The sentiment-enhanced Adaptive ML Strategy combines:
- ✅ 15 technical indicators
- ✅ 6 sentiment features
- ✅ Random Forest ML model
- ✅ Adaptive retraining
- ✅ Confidence filtering

This creates a powerful predictive system that learns from both price patterns and market sentiment!

---

**Questions?** Check the main documentation:
- `STRATEGIES_GUIDE.md` - All 11 strategies
- `LIVE_TRADING_GUIDE.md` - Live trading setup
- `README.md` - Project overview
