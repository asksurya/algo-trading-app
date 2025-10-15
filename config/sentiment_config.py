"""
Sentiment Analysis API Configuration

Get free API keys from:
- NewsAPI: https://newsapi.org (free tier: 100 requests/day)
- Alpha Vantage: https://www.alphavantage.co (free tier: 25 requests/day)
"""

# NewsAPI Configuration
# Sign up at: https://newsapi.org/register
NEWSAPI_KEY = None  # Replace with your NewsAPI key

# Alpha Vantage Configuration  
# Sign up at: https://www.alphavantage.co/support/#api-key
ALPHA_VANTAGE_KEY = None  # Replace with your Alpha Vantage key

# Note: Both APIs are optional. The system will work without them,
# but sentiment features will be simulated/neutral.
# For production use, add at least one API key.
