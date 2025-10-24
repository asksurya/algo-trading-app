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

# Handle both local and Streamlit Cloud deployments
try:
    import streamlit as st
    # Try Streamlit secrets first (for cloud deployment)
    if hasattr(st, 'secrets'):
        ALPACA_API_KEY = st.secrets.get("ALPACA_API_KEY", "")
        ALPACA_SECRET_KEY = st.secrets.get("ALPACA_SECRET_KEY", "")
    else:
        raise ImportError("Streamlit secrets not available")
except (ImportError, FileNotFoundError):
    # Fall back to config file (for local deployment)
    try:
        from config.alpaca_config import ALPACA_API_KEY, ALPACA_SECRET_KEY
    except ImportError:
        # If neither works, use empty strings (will use Yahoo Finance)
        ALPACA_API_KEY = ""
        ALPACA_SECRET_KEY = ""
        logging.warning("No Alpaca credentials found. Using Yahoo Finance only.")


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
        use_cache: bool = True  # Default to True - use database cache
    ) -> pd.DataFrame:
        """
        Fetch historical market data with database caching.
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            timeframe: Data timeframe ('1D', '1H', '15Min', etc.)
            use_cache: Whether to use database cache (default: True)
            
        Returns:
            DataFrame with split-adjusted OHLCV data
        
        Note: Uses database cache to store historical data. Only fetches new data
        since the last cached date, making subsequent fetches much faster.
        """
        from src.trading.state_manager import StateManager
        from datetime import datetime, timedelta
        
        # Only use database cache for daily data
        if use_cache and timeframe == '1D':
            state_manager = StateManager()
            
            # Check if we have cached data
            last_cached_date = state_manager.get_last_cached_date(symbol)
            
            if last_cached_date:
                self.logger.info(f"Found cached data for {symbol} up to {last_cached_date}")
                
                # Get cached data
                cached_df = state_manager.get_cached_price_data(symbol, start_date, end_date)
                
                # Calculate if we need to fetch new data
                last_date = datetime.strptime(last_cached_date, '%Y-%m-%d')
                end_datetime = datetime.strptime(end_date, '%Y-%m-%d')
                
                # If cache is up to date, return it
                if last_date >= end_datetime:
                    self.logger.info(f"Cache is up to date for {symbol}")
                    return cached_df
                
                # Fetch only new data since last cached date
                fetch_start = (last_date + timedelta(days=1)).strftime('%Y-%m-%d')
                self.logger.info(f"Fetching new data for {symbol} from {fetch_start} to {end_date}")
                
                if self.data_provider == 'alpaca':
                    new_df = self._fetch_alpaca_data(symbol, fetch_start, end_date, timeframe)
                else:
                    new_df = self._fetch_yahoo_data(symbol, fetch_start, end_date)
                
                # Save new data to cache
                if new_df is not None and not new_df.empty:
                    state_manager.save_price_data(symbol, new_df)
                    
                    # Combine cached and new data
                    combined_df = pd.concat([cached_df, new_df])
                    combined_df = combined_df[~combined_df.index.duplicated(keep='last')]
                    combined_df = combined_df.sort_index()
                    
                    # Filter to requested date range
                    combined_df = combined_df.loc[start_date:end_date]
                    
                    self.logger.info(f"Combined cache + new data: {len(combined_df)} rows for {symbol}")
                    return combined_df
                
                return cached_df
            
            else:
                # No cache, fetch all data
                self.logger.info(f"No cache found for {symbol}, fetching all historical data")
                
                if self.data_provider == 'alpaca':
                    df = self._fetch_alpaca_data(symbol, start_date, end_date, timeframe)
                else:
                    df = self._fetch_yahoo_data(symbol, start_date, end_date)
                
                # Save to cache
                if df is not None and not df.empty:
                    state_manager.save_price_data(symbol, df)
                    self.logger.info(f"Saved {len(df)} rows to cache for {symbol}")
                
                return df
        
        else:
            # Not using cache or not daily data, fetch directly
            self.logger.info(f"Fetching {symbol} data from {start_date} to {end_date} (no cache)")
            
            if self.data_provider == 'alpaca':
                df = self._fetch_alpaca_data(symbol, start_date, end_date, timeframe)
            else:
                df = self._fetch_yahoo_data(symbol, start_date, end_date)
            
            return df
    
    def _fetch_alpaca_data(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        timeframe: str
    ) -> pd.DataFrame:
        """
        Fetch data from Alpaca API.
        
        Note: We request 'split' adjustment to handle stock splits automatically.
        This ensures prices are adjusted for splits (like NVDA's 10-for-1 split).
        """
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
            
            # Create request with adjustment='split' for split-adjusted prices
            # Options: 'raw' (default), 'split', 'dividend', 'all'
            request_params = StockBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=tf,
                start=datetime.strptime(start_date, '%Y-%m-%d'),
                end=datetime.strptime(end_date, '%Y-%m-%d'),
                adjustment='split'  # Adjust for stock splits
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
        """
        Fetch data from Yahoo Finance.
        
        Note: Yahoo Finance automatically returns split-adjusted and dividend-adjusted
        prices, which is correct for backtesting. The 'Close' column is adjusted,
        while 'Open', 'High', 'Low' are also adjusted proportionally.
        """
        try:
            ticker = yf.Ticker(symbol)
            # auto_adjust=True ensures we get adjusted prices (default behavior)
            # This handles stock splits, dividends, etc. automatically
            df = ticker.history(start=start_date, end=end_date, auto_adjust=True)
            
            if df.empty:
                self.logger.warning(f"No data returned for {symbol}")
                return pd.DataFrame()
            
            # Rename columns to lowercase
            df.columns = [col.lower() for col in df.columns]
            
            # Return only OHLCV data
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
    
    def clear_cache(self, symbol: Optional[str] = None):
        """
        Clear cached data.
        
        Args:
            symbol: If provided, only clear cache for this symbol.
                   If None, clear all cache.
        """
        if not os.path.exists(self.cache_dir):
            return
        
        files_cleared = 0
        for filename in os.listdir(self.cache_dir):
            if filename.endswith('.csv'):
                if symbol is None or filename.startswith(symbol):
                    filepath = os.path.join(self.cache_dir, filename)
                    os.remove(filepath)
                    files_cleared += 1
                    self.logger.info(f"Cleared cache file: {filename}")
        
        self.logger.info(f"Cleared {files_cleared} cache files")
    
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
