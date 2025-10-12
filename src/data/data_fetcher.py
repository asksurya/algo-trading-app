"""
Data Fetcher Module

Fetches historical and real-time market data from various sources.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import logging
from typing import Optional, List
import yfinance as yf

try:
    from alpaca.data.historical import StockHistoricalDataClient
    from alpaca.data.requests import StockBarsRequest
    from alpaca.data.timeframe import TimeFrame
    ALPACA_AVAILABLE = True
except ImportError:
    ALPACA_AVAILABLE = False
    logging.warning("Alpaca SDK not installed. Install with: pip install alpaca-py")

from config.alpaca_config import ALPACA_API_KEY, ALPACA_SECRET_KEY


class DataFetcher:
    """Fetch market data from multiple sources."""
    
    def __init__(self, data_provider: str = 'alpaca', cache_dir: str = 'data'):
        """
        Initialize DataFetcher.
        
        Args:
            data_provider: 'alpaca' or 'yahoo'
            cache_dir: Directory to cache data
        """
        self.data_provider = data_provider.lower()
        self.cache_dir = cache_dir
        self.logger = logging.getLogger(__name__)
        
        # Create cache directory
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Initialize Alpaca client if available
        if self.data_provider == 'alpaca' and ALPACA_AVAILABLE:
            try:
                self.alpaca_client = StockHistoricalDataClient(
                    ALPACA_API_KEY, 
                    ALPACA_SECRET_KEY
                )
                self.logger.info("Alpaca client initialized successfully")
            except Exception as e:
                self.logger.error(f"Failed to initialize Alpaca client: {e}")
                self.data_provider = 'yahoo'
                self.logger.info("Falling back to Yahoo Finance")
        elif self.data_provider == 'alpaca' and not ALPACA_AVAILABLE:
            self.logger.warning("Alpaca not available, using Yahoo Finance")
            self.data_provider = 'yahoo'
    
    def fetch_historical_data(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        timeframe: str = '1D',
        use_cache: bool = True
    ) -> pd.DataFrame:
        """
        Fetch historical market data.
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            timeframe: Data timeframe ('1D', '1H', '15Min', etc.)
            use_cache: Whether to use cached data
            
        Returns:
            DataFrame with OHLCV data
        """
        # Check cache first
        cache_file = self._get_cache_filename(symbol, start_date, end_date, timeframe)
        
        if use_cache and os.path.exists(cache_file):
            self.logger.info(f"Loading cached data for {symbol}")
            return pd.read_csv(cache_file, index_col=0, parse_dates=True)
        
        # Fetch new data
        self.logger.info(f"Fetching {symbol} data from {start_date} to {end_date}")
        
        if self.data_provider == 'alpaca':
            df = self._fetch_alpaca_data(symbol, start_date, end_date, timeframe)
        else:
            df = self._fetch_yahoo_data(symbol, start_date, end_date)
        
        # Cache the data
        if use_cache and df is not None and not df.empty:
            df.to_csv(cache_file)
            self.logger.info(f"Data cached to {cache_file}")
        
        return df
    
    def _fetch_alpaca_data(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        timeframe: str
    ) -> pd.DataFrame:
        """Fetch data from Alpaca API."""
        try:
            # Map timeframe string to Alpaca TimeFrame
            timeframe_map = {
                '1Min': TimeFrame.Minute,
                '5Min': TimeFrame(5, 'Min'),
                '15Min': TimeFrame(15, 'Min'),
                '1H': TimeFrame.Hour,
                '1D': TimeFrame.Day,
            }
            
            tf = timeframe_map.get(timeframe, TimeFrame.Day)
            
            # Create request
            request_params = StockBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=tf,
                start=datetime.strptime(start_date, '%Y-%m-%d'),
                end=datetime.strptime(end_date, '%Y-%m-%d')
            )
            
            # Get bars
            bars = self.alpaca_client.get_stock_bars(request_params)
            
            # Convert to DataFrame
            df = bars.df
            
            if symbol in df.index.get_level_values(0):
                df = df.xs(symbol, level=0)
            
            # Rename columns to standard format
            df.columns = ['open', 'high', 'low', 'close', 'volume', 'trade_count', 'vwap']
            
            return df[['open', 'high', 'low', 'close', 'volume']]
            
        except Exception as e:
            self.logger.error(f"Error fetching Alpaca data: {e}")
            self.logger.info("Falling back to Yahoo Finance")
            # Fall back to Yahoo Finance
            return self._fetch_yahoo_data(symbol, start_date, end_date)
    
    def _fetch_yahoo_data(
        self,
        symbol: str,
        start_date: str,
        end_date: str
    ) -> pd.DataFrame:
        """Fetch data from Yahoo Finance."""
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(start=start_date, end=end_date)
            
            # Rename columns to lowercase
            df.columns = [col.lower() for col in df.columns]
            
            return df[['open', 'high', 'low', 'close', 'volume']]
            
        except Exception as e:
            self.logger.error(f"Error fetching Yahoo data: {e}")
            return pd.DataFrame()
    
    def fetch_multiple_symbols(
        self,
        symbols: List[str],
        start_date: str,
        end_date: str,
        timeframe: str = '1D'
    ) -> dict:
        """
        Fetch data for multiple symbols.
        
        Args:
            symbols: List of stock symbols
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            timeframe: Data timeframe
            
        Returns:
            Dictionary mapping symbols to DataFrames
        """
        data = {}
        
        for symbol in symbols:
            self.logger.info(f"Fetching data for {symbol}")
            df = self.fetch_historical_data(symbol, start_date, end_date, timeframe)
            
            if df is not None and not df.empty:
                data[symbol] = df
            else:
                self.logger.warning(f"No data fetched for {symbol}")
        
        return data
    
    def _get_cache_filename(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        timeframe: str
    ) -> str:
        """Generate cache filename."""
        filename = f"{symbol}_{start_date}_{end_date}_{timeframe}.csv"
        return os.path.join(self.cache_dir, filename)
    
    def get_latest_price(self, symbol: str) -> Optional[float]:
        """
        Get the latest price for a symbol.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Latest closing price or None
        """
        try:
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
            
            df = self.fetch_historical_data(
                symbol, 
                start_date, 
                end_date, 
                use_cache=False
            )
            
            if not df.empty:
                return float(df['close'].iloc[-1])
            
        except Exception as e:
            self.logger.error(f"Error getting latest price for {symbol}: {e}")
        
        return None


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    fetcher = DataFetcher(data_provider='yahoo')
    
    # Fetch single symbol
    df = fetcher.fetch_historical_data(
        symbol='AAPL',
        start_date='2023-01-01',
        end_date='2024-01-01'
    )
    
    print(f"Fetched {len(df)} rows for AAPL")
    print(df.head())
    print(f"\nLatest price: ${fetcher.get_latest_price('AAPL'):.2f}")
