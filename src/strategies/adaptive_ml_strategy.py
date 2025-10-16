"""
Adaptive ML Strategy

Type: Machine Learning / Predictive
Complexity: ⭐⭐⭐⭐⭐

How it works:
- Trains ML model (Random Forest) on historical data
- Uses multiple technical indicators as features
- Predicts next-day price movement
- Can retrain with paper/live trading results
- Adapts to market conditions
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict, List
import pickle
import os
from datetime import datetime
import sys
sys.path.append('../..')

try:
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import train_test_split
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

from .base_strategy import BaseStrategy, Signal

try:
    from src.analysis.sentiment_analyzer import SentimentAnalyzer
    SENTIMENT_AVAILABLE = True
except ImportError:
    SENTIMENT_AVAILABLE = False


class AdaptiveMLStrategy(BaseStrategy):
    """
    Adaptive Machine Learning strategy using Random Forest.
    
    Features:
    - Trains on historical data
    - Uses technical indicators as features
    - Predicts buy/sell/hold signals
    - Can retrain with new data
    - Saves model for persistence
    """
    
    def __init__(
        self,
        lookback_period: int = 30,
        confidence_threshold: float = 0.45,  # Lower threshold = more trades
        retrain_interval: int = 100,
        model_path: str = "models/adaptive_ml_model.pkl",
        use_sentiment: bool = True,
        news_api_key: Optional[str] = None,
        alpha_vantage_key: Optional[str] = None,
        name: str = "Adaptive ML"
    ):
        """
        Initialize Adaptive ML Strategy.
        
        Args:
            lookback_period: Days of history for feature calculation
            confidence_threshold: Minimum prediction confidence (0-1)
            retrain_interval: Retrain model every N trades
            model_path: Path to save/load trained model
            name: Strategy name
        """
        super().__init__(name)
        
        if not SKLEARN_AVAILABLE:
            raise ImportError("scikit-learn required. Install: pip install scikit-learn")
        
        self.lookback_period = lookback_period
        self.confidence_threshold = confidence_threshold
        self.retrain_interval = retrain_interval
        self.model_path = model_path
        self.use_sentiment = use_sentiment and SENTIMENT_AVAILABLE
        
        # Initialize sentiment analyzer if enabled
        self.sentiment_analyzer = None
        if self.use_sentiment:
            self.sentiment_analyzer = SentimentAnalyzer(
                news_api_key=news_api_key,
                alpha_vantage_key=alpha_vantage_key
            )
        
        # Cache for sentiment data
        self.sentiment_data = {}
        
        # Model and scaler
        self.model = None
        self.scaler = None
        self.is_trained = False
        
        # Performance tracking for retraining
        self.trade_history = []
        self.trades_since_retrain = 0
        
        # Try to load existing model
        self._load_model()
    
    def calculate_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate technical indicators to use as ML features.
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            DataFrame with feature columns
        """
        df = data.copy()
        
        # Price-based features
        df['returns'] = df['close'].pct_change()
        df['log_returns'] = np.log(df['close'] / df['close'].shift(1))
        
        # Moving averages
        for period in [5, 10, 20, 50]:
            df[f'sma_{period}'] = df['close'].rolling(window=period).mean()
            df[f'price_to_sma_{period}'] = df['close'] / df[f'sma_{period}']
        
        # Exponential moving averages
        df['ema_12'] = df['close'].ewm(span=12).mean()
        df['ema_26'] = df['close'].ewm(span=26).mean()
        df['macd'] = df['ema_12'] - df['ema_26']
        df['macd_signal'] = df['macd'].ewm(span=9).mean()
        
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # Bollinger Bands
        df['bb_middle'] = df['close'].rolling(window=20).mean()
        df['bb_std'] = df['close'].rolling(window=20).std()
        df['bb_upper'] = df['bb_middle'] + (2 * df['bb_std'])
        df['bb_lower'] = df['bb_middle'] - (2 * df['bb_std'])
        df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
        df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
        
        # Volatility
        df['volatility'] = df['returns'].rolling(window=20).std()
        df['atr'] = self._calculate_atr(df)
        
        # Volume features
        df['volume_sma'] = df['volume'].rolling(window=20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_sma']
        
        # Momentum
        df['momentum'] = df['close'] - df['close'].shift(10)
        df['roc'] = df['close'].pct_change(periods=10) * 100
        
        # Add sentiment features if available
        if self.use_sentiment and hasattr(self, 'current_symbol'):
            df = self._add_sentiment_features(df, self.current_symbol)
        
        # Target variable (for training): next day's return
        df['target'] = df['close'].shift(-1) / df['close'] - 1
        
        # Convert target to classes: 1 (buy), -1 (sell), 0 (hold)
        df['target_class'] = 0
        df.loc[df['target'] > 0.005, 'target_class'] = 1  # >0.5% gain
        df.loc[df['target'] < -0.005, 'target_class'] = -1  # >0.5% loss
        
        return df
    
    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Average True Range."""
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        atr = true_range.rolling(period).mean()
        
        return atr
    
    def train_model(self, data: pd.DataFrame, test_size: float = 0.2):
        """
        Train the ML model on historical data.
        
        Args:
            data: DataFrame with OHLCV data
            test_size: Fraction of data for testing
        """
        # Calculate features
        df = self.calculate_features(data)
        
        # Select feature columns
        feature_cols = [
            'returns', 'price_to_sma_5', 'price_to_sma_10', 'price_to_sma_20', 'price_to_sma_50',
            'macd', 'macd_signal', 'rsi', 'bb_width', 'bb_position',
            'volatility', 'atr', 'volume_ratio', 'momentum', 'roc'
        ]
        
        # Add sentiment features if available
        if self.use_sentiment:
            sentiment_cols = [
                'sentiment_overall', 'sentiment_news', 'sentiment_headline',
                'sentiment_change', 'news_volume_norm', 'positive_ratio'
            ]
            # Only include sentiment columns that exist in the data
            feature_cols.extend([col for col in sentiment_cols if col in df.columns])
        
        # Remove NaN rows
        df_clean = df.dropna()
        
        if len(df_clean) < 100:
            raise ValueError("Insufficient data for training (need at least 100 samples)")
        
        # Prepare features and target
        X = df_clean[feature_cols]
        y = df_clean['target_class']
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, shuffle=False
        )
        
        # Scale features
        self.scaler = StandardScaler()
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train Random Forest with optimized hyperparameters
        self.model = RandomForestClassifier(
            n_estimators=200,  # More trees for better accuracy
            max_depth=15,  # Deeper trees to capture complex patterns
            min_samples_split=3,  # Less conservative splitting
            min_samples_leaf=1,  # Allow more granular leaves
            max_features='sqrt',  # Better feature selection
            random_state=42,
            class_weight='balanced',  # Handle imbalanced classes
            n_jobs=-1  # Use all CPU cores for faster training
        )
        
        self.model.fit(X_train_scaled, y_train)
        
        # Evaluate
        train_score = self.model.score(X_train_scaled, y_train)
        test_score = self.model.score(X_test_scaled, y_test)
        
        self.is_trained = True
        
        print(f"Model trained - Train accuracy: {train_score:.3f}, Test accuracy: {test_score:.3f}")
        
        # Save model
        self._save_model()
    
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate features for prediction."""
        return self.calculate_features(data)
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate trading signals using ML predictions.
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            Series with signals (1=BUY, -1=SELL, 0=HOLD)
        """
        # Train if not trained and have enough data
        if not self.is_trained:
            if len(data) < 100:
                # Not enough data to train, return HOLD signals
                print(f"Warning: Only {len(data)} samples, need 100+ for training. Returning HOLD.")
                return pd.Series(0, index=data.index)
            print("Training model on provided data...")
            self.train_model(data)
        
        # Calculate features
        df = self.calculate_features(data)
        
        # Feature columns  
        feature_cols = [
            'returns', 'price_to_sma_5', 'price_to_sma_10', 'price_to_sma_20', 'price_to_sma_50',
            'macd', 'macd_signal', 'rsi', 'bb_width', 'bb_position',
            'volatility', 'atr', 'volume_ratio', 'momentum', 'roc'
        ]
        
        # Add sentiment features if available
        if self.use_sentiment:
            sentiment_cols = [
                'sentiment_overall', 'sentiment_news', 'sentiment_headline',
                'sentiment_change', 'news_volume_norm', 'positive_ratio'
            ]
            feature_cols.extend([col for col in sentiment_cols if col in df.columns])
        
        # Prepare features
        X = df[feature_cols].ffill().fillna(0)
        X_scaled = self.scaler.transform(X)
        
        # Get predictions and probabilities
        predictions = self.model.predict(X_scaled)
        probabilities = self.model.predict_proba(X_scaled)
        
        # Get max probability for each prediction
        max_probs = np.max(probabilities, axis=1)
        
        # Create signals with confidence threshold
        signals = pd.Series(0, index=df.index)
        
        # Only trade when confidence exceeds threshold
        high_confidence = max_probs >= self.confidence_threshold
        signals[high_confidence] = predictions[high_confidence]
        
        return signals
    
    def add_trade_result(self, entry_price: float, exit_price: float, shares: int):
        """
        Add trade result for adaptive retraining.
        
        Args:
            entry_price: Entry price
            exit_price: Exit price
            shares: Number of shares
        """
        profit = (exit_price - entry_price) * shares
        profit_pct = (exit_price / entry_price - 1) * 100
        
        self.trade_history.append({
            'entry_price': entry_price,
            'exit_price': exit_price,
            'shares': shares,
            'profit': profit,
            'profit_pct': profit_pct,
            'timestamp': datetime.now()
        })
        
        self.trades_since_retrain += 1
    
    def should_retrain(self) -> bool:
        """Check if model should be retrained."""
        return self.trades_since_retrain >= self.retrain_interval
    
    def retrain_with_results(self, data: pd.DataFrame):
        """
        Retrain model incorporating recent trading results.
        
        Args:
            data: Updated historical data including recent trades
        """
        print(f"Retraining model with {len(self.trade_history)} recent trades...")
        self.train_model(data)
        self.trades_since_retrain = 0
        print("Model retrained successfully!")
    
    def _save_model(self):
        """Save trained model and scaler to disk."""
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'lookback_period': self.lookback_period,
            'confidence_threshold': self.confidence_threshold,
            'trade_history': self.trade_history,
            'timestamp': datetime.now()
        }
        
        with open(self.model_path, 'wb') as f:
            pickle.dump(model_data, f)
        
        print(f"Model saved to {self.model_path}")
    
    def _load_model(self):
        """Load trained model from disk if it exists."""
        if os.path.exists(self.model_path):
            try:
                with open(self.model_path, 'rb') as f:
                    model_data = pickle.load(f)
                
                self.model = model_data['model']
                self.scaler = model_data['scaler']
                self.trade_history = model_data.get('trade_history', [])
                self.is_trained = True
                
                print(f"Model loaded from {self.model_path}")
                print(f"Model trained on: {model_data.get('timestamp', 'Unknown')}")
            except Exception as e:
                print(f"Could not load model: {e}")
    
    def _add_sentiment_features(self, df: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """
        Add sentiment analysis features to the dataframe.
        
        Args:
            df: DataFrame with OHLCV data
            symbol: Stock symbol
            
        Returns:
            DataFrame with added sentiment features
        """
        if not self.sentiment_analyzer:
            return df
        
        # Get sentiment data for the symbol
        sentiment = self.sentiment_analyzer.get_stock_sentiment(symbol, days_back=7)
        
        # Add sentiment features (constant for all rows since we have one sentiment per symbol)
        df['sentiment_overall'] = sentiment['overall_sentiment']
        df['sentiment_news'] = sentiment['news_sentiment']
        df['sentiment_headline'] = sentiment['headline_sentiment']
        df['sentiment_change'] = sentiment['sentiment_change']
        df['news_volume_norm'] = min(sentiment['news_volume'] / 50, 1.0)  # Normalize to 0-1
        df['positive_ratio'] = sentiment['positive_ratio']
        
        return df
    
    def set_symbol(self, symbol: str):
        """Set the current symbol being analyzed (for sentiment features)."""
        self.current_symbol = symbol
        
    def get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance from trained model."""
        if not self.is_trained:
            return {}
        
        feature_cols = [
            'returns', 'price_to_sma_5', 'price_to_sma_10', 'price_to_sma_20', 'price_to_sma_50',
            'macd', 'macd_signal', 'rsi', 'bb_width', 'bb_position',
            'volatility', 'atr', 'volume_ratio', 'momentum', 'roc'
        ]
        
        # Add sentiment features if used
        if self.use_sentiment:
            sentiment_cols = [
                'sentiment_overall', 'sentiment_news', 'sentiment_headline',
                'sentiment_change', 'news_volume_norm', 'positive_ratio'
            ]
            feature_cols.extend(sentiment_cols)
        
        importances = self.model.feature_importances_
        
        # Only return features that were actually used
        if len(importances) == len(feature_cols):
            return dict(zip(feature_cols, importances))
        else:
            # Mismatch, return what we have
            return dict(zip(feature_cols[:len(importances)], importances))
    
    def __str__(self) -> str:
        status = "Trained" if self.is_trained else "Not Trained"
        trades = len(self.trade_history)
        sentiment_status = "with Sentiment" if self.use_sentiment else "no Sentiment"
        return f"Adaptive ML ({status}, {trades} trades, {sentiment_status})"


if __name__ == "__main__":
    # Example usage
    import sys
    sys.path.append('../..')
    
    from src.data.data_fetcher import DataFetcher
    
    # Fetch data
    fetcher = DataFetcher(data_provider='yahoo')
    df = fetcher.fetch_historical_data(
        symbol='AAPL',
        start_date='2023-01-01',
        end_date='2024-01-01'
    )
    
    # Initialize and train strategy
    strategy = AdaptiveMLStrategy()
    strategy.train_model(df)
    
    # Generate signals
    signals = strategy.generate_signals(df)
    
    print(f"\nSignals generated: {(signals != 0).sum()}")
    print(f"Buy signals: {(signals == 1).sum()}")
    print(f"Sell signals: {(signals == -1).sum()}")
    
    # Show feature importance
    print("\nFeature Importance:")
    importance = strategy.get_feature_importance()
    for feature, imp in sorted(importance.items(), key=lambda x: x[1], reverse=True):
        print(f"  {feature}: {imp:.4f}")
