"""
State Management Module

Handles persistent storage of:
- Strategy evaluation results
- Trading state (active/inactive)
- Trading configuration
- Trade history
"""

import sqlite3
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
import threading


class StateManager:
    """Manage persistent state for trading system."""
    
    def __init__(self, db_path: str = "data/trading_state.db"):
        """Initialize state manager with SQLite database."""
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self._lock = threading.Lock()
        
        # Ensure data directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self._init_database()
    
    def _init_database(self):
        """Create database tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Strategy evaluations table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS strategy_evaluations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticker TEXT NOT NULL,
                    strategy_name TEXT NOT NULL,
                    evaluation_date TIMESTAMP NOT NULL,
                    metrics TEXT NOT NULL,
                    score REAL NOT NULL,
                    metric_name TEXT NOT NULL,
                    UNIQUE(ticker, strategy_name)
                )
            """)
            
            # Best strategies table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS best_strategies (
                    ticker TEXT PRIMARY KEY,
                    strategy_name TEXT NOT NULL,
                    score REAL NOT NULL,
                    evaluation_date TIMESTAMP NOT NULL,
                    metric_name TEXT NOT NULL
                )
            """)
            
            # Trading configuration table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trading_config (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    tickers TEXT NOT NULL,
                    paper_trading INTEGER NOT NULL,
                    initial_capital REAL NOT NULL,
                    risk_per_trade REAL NOT NULL,
                    max_positions INTEGER NOT NULL,
                    check_interval INTEGER NOT NULL,
                    last_updated TIMESTAMP NOT NULL
                )
            """)
            
            # Trading state table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trading_state (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    is_active INTEGER NOT NULL,
                    started_at TIMESTAMP,
                    stopped_at TIMESTAMP,
                    last_check TIMESTAMP
                )
            """)
            
            # Initialize default trading state if not exists
            cursor.execute("""
                INSERT OR IGNORE INTO trading_state (id, is_active)
                VALUES (1, 0)
            """)
            
            # Trade history table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trade_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticker TEXT NOT NULL,
                    strategy_name TEXT NOT NULL,
                    action TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    price REAL NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    order_id TEXT,
                    signal INTEGER NOT NULL
                )
            """)
            
            # Historical price data cache table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS price_data_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticker TEXT NOT NULL,
                    date TEXT NOT NULL,
                    open REAL NOT NULL,
                    high REAL NOT NULL,
                    low REAL NOT NULL,
                    close REAL NOT NULL,
                    volume INTEGER NOT NULL,
                    UNIQUE(ticker, date)
                )
            """)
            
            # Create index for faster queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_price_cache_ticker_date 
                ON price_data_cache(ticker, date)
            """)
            
            conn.commit()
            self.logger.info("Database initialized")
    
    def save_strategy_evaluation(
        self,
        ticker: str,
        strategy_name: str,
        metrics: Dict,
        score: float,
        metric_name: str
    ):
        """Save strategy evaluation results."""
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO strategy_evaluations
                    (ticker, strategy_name, evaluation_date, metrics, score, metric_name)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    ticker,
                    strategy_name,
                    datetime.now(),
                    json.dumps(metrics),
                    score,
                    metric_name
                ))
                conn.commit()
    
    def save_best_strategy(
        self,
        ticker: str,
        strategy_name: str,
        score: float,
        metric_name: str
    ):
        """Save best strategy for a ticker."""
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO best_strategies
                    (ticker, strategy_name, score, evaluation_date, metric_name)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    ticker,
                    strategy_name,
                    score,
                    datetime.now(),
                    metric_name
                ))
                conn.commit()
    
    def get_best_strategy(self, ticker: str) -> Optional[Dict]:
        """Get best strategy for a ticker."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT strategy_name, score, evaluation_date, metric_name
                FROM best_strategies
                WHERE ticker = ?
            """, (ticker,))
            
            row = cursor.fetchone()
            if row:
                return {
                    'strategy_name': row[0],
                    'score': row[1],
                    'evaluation_date': row[2],
                    'metric_name': row[3]
                }
            return None
    
    def get_all_evaluations(self, ticker: str) -> List[Dict]:
        """Get all strategy evaluations for a ticker."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT strategy_name, metrics, score, evaluation_date, metric_name
                FROM strategy_evaluations
                WHERE ticker = ?
                ORDER BY score DESC
            """, (ticker,))
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    'strategy_name': row[0],
                    'metrics': json.loads(row[1]),
                    'score': row[2],
                    'evaluation_date': row[3],
                    'metric_name': row[4]
                })
            return results
    
    def save_trading_config(
        self,
        tickers: List[str],
        paper_trading: bool,
        initial_capital: float,
        risk_per_trade: float,
        max_positions: int,
        check_interval: int
    ):
        """Save trading configuration."""
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO trading_config
                    (id, tickers, paper_trading, initial_capital, risk_per_trade,
                     max_positions, check_interval, last_updated)
                    VALUES (1, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    json.dumps(tickers),
                    1 if paper_trading else 0,
                    initial_capital,
                    risk_per_trade,
                    max_positions,
                    check_interval,
                    datetime.now()
                ))
                conn.commit()
    
    def get_trading_config(self) -> Optional[Dict]:
        """Get current trading configuration."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT tickers, paper_trading, initial_capital, risk_per_trade,
                       max_positions, check_interval, last_updated
                FROM trading_config
                WHERE id = 1
            """)
            
            row = cursor.fetchone()
            if row:
                return {
                    'tickers': json.loads(row[0]),
                    'paper_trading': bool(row[1]),
                    'initial_capital': row[2],
                    'risk_per_trade': row[3],
                    'max_positions': row[4],
                    'check_interval': row[5],
                    'last_updated': row[6]
                }
            return None
    
    def set_trading_active(self, active: bool):
        """Set trading state to active or inactive."""
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if active:
                    cursor.execute("""
                        UPDATE trading_state
                        SET is_active = 1, started_at = ?, stopped_at = NULL
                        WHERE id = 1
                    """, (datetime.now(),))
                else:
                    cursor.execute("""
                        UPDATE trading_state
                        SET is_active = 0, stopped_at = ?
                        WHERE id = 1
                    """, (datetime.now(),))
                
                conn.commit()
    
    def is_trading_active(self) -> bool:
        """Check if trading is currently active."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT is_active FROM trading_state WHERE id = 1")
            row = cursor.fetchone()
            return bool(row[0]) if row else False
    
    def get_trading_state(self) -> Dict:
        """Get full trading state."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT is_active, started_at, stopped_at, last_check
                FROM trading_state
                WHERE id = 1
            """)
            
            row = cursor.fetchone()
            if row:
                return {
                    'is_active': bool(row[0]),
                    'started_at': row[1],
                    'stopped_at': row[2],
                    'last_check': row[3]
                }
            return {'is_active': False}
    
    def update_last_check(self):
        """Update last check timestamp."""
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE trading_state
                    SET last_check = ?
                    WHERE id = 1
                """, (datetime.now(),))
                conn.commit()
    
    def record_trade(
        self,
        ticker: str,
        strategy_name: str,
        action: str,
        quantity: int,
        price: float,
        signal: int,
        order_id: Optional[str] = None
    ):
        """Record a trade in history."""
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO trade_history
                    (ticker, strategy_name, action, quantity, price, timestamp, order_id, signal)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    str(ticker),
                    str(strategy_name),
                    str(action),
                    int(quantity),
                    float(price),
                    datetime.now().isoformat(),
                    str(order_id) if order_id is not None else None,
                    int(signal)
                ))
                conn.commit()
    
    def get_trade_history(
        self,
        ticker: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """Get trade history."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            if ticker:
                cursor.execute("""
                    SELECT ticker, strategy_name, action, quantity, price,
                           timestamp, order_id, signal
                    FROM trade_history
                    WHERE ticker = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (ticker, limit))
            else:
                cursor.execute("""
                    SELECT ticker, strategy_name, action, quantity, price,
                           timestamp, order_id, signal
                    FROM trade_history
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (limit,))
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    'ticker': row[0],
                    'strategy_name': row[1],
                    'action': row[2],
                    'quantity': row[3],
                    'price': row[4],
                    'timestamp': row[5],
                    'order_id': row[6],
                    'signal': row[7]
                })
            return results
    
    def clear_evaluations(self, ticker: Optional[str] = None):
        """Clear strategy evaluations."""
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if ticker:
                    cursor.execute("DELETE FROM strategy_evaluations WHERE ticker = ?", (ticker,))
                    cursor.execute("DELETE FROM best_strategies WHERE ticker = ?", (ticker,))
                else:
                    cursor.execute("DELETE FROM strategy_evaluations")
                    cursor.execute("DELETE FROM best_strategies")
                
                conn.commit()
    
    def save_price_data(self, ticker: str, price_data: Any):
        """
        Save historical price data to cache.
        
        Args:
            ticker: Stock symbol
            price_data: DataFrame with date index and OHLCV columns
        """
        import pandas as pd
        
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                for date, row in price_data.iterrows():
                    date_str = date.strftime('%Y-%m-%d') if isinstance(date, pd.Timestamp) else str(date)
                    
                    cursor.execute("""
                        INSERT OR REPLACE INTO price_data_cache
                        (ticker, date, open, high, low, close, volume)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        str(ticker),
                        date_str,
                        float(row['open']),
                        float(row['high']),
                        float(row['low']),
                        float(row['close']),
                        int(row['volume'])
                    ))
                
                conn.commit()
                self.logger.info(f"Cached {len(price_data)} rows for {ticker}")
    
    def get_cached_price_data(self, ticker: str, start_date: str = None, end_date: str = None) -> Optional[Any]:
        """
        Get cached price data for a ticker.
        
        Args:
            ticker: Stock symbol
            start_date: Start date (YYYY-MM-DD), optional
            end_date: End date (YYYY-MM-DD), optional
            
        Returns:
            DataFrame with price data or None if no data
        """
        import pandas as pd
        
        with sqlite3.connect(self.db_path) as conn:
            query = "SELECT date, open, high, low, close, volume FROM price_data_cache WHERE ticker = ?"
            params = [ticker]
            
            if start_date:
                query += " AND date >= ?"
                params.append(start_date)
            
            if end_date:
                query += " AND date <= ?"
                params.append(end_date)
            
            query += " ORDER BY date"
            
            df = pd.read_sql_query(query, conn, params=params)
            
            if df.empty:
                return None
            
            # Convert date column to datetime and set as index
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            
            self.logger.info(f"Retrieved {len(df)} cached rows for {ticker}")
            return df
    
    def get_last_cached_date(self, ticker: str) -> Optional[str]:
        """Get the last date for which we have cached data."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT MAX(date) FROM price_data_cache WHERE ticker = ?
            """, (ticker,))
            
            row = cursor.fetchone()
            return row[0] if row and row[0] else None
    
    def clear_price_cache(self, ticker: Optional[str] = None):
        """Clear cached price data."""
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if ticker:
                    cursor.execute("DELETE FROM price_data_cache WHERE ticker = ?", (ticker,))
                    self.logger.info(f"Cleared price cache for {ticker}")
                else:
                    cursor.execute("DELETE FROM price_data_cache")
                    self.logger.info("Cleared all price cache")
                
                conn.commit()
