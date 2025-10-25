"""
Market data caching service.
Manages local storage of historical market data to minimize API calls.
"""
import logging
from datetime import datetime, date, timedelta
from typing import List, Optional, Tuple
import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, delete
from sqlalchemy.dialects.postgresql import insert

from app.models.market_data_cache import MarketDataCache
from app.integrations.market_data import get_market_data_service

logger = logging.getLogger(__name__)


class MarketDataCacheService:
    """
    Service for caching historical market data locally.
    Implements intelligent fetching that only downloads missing data.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.market_data = get_market_data_service()
    
    async def get_historical_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        force_refresh: bool = False
    ) -> pd.DataFrame:
        """
        Get historical data with intelligent caching.
        
        Strategy:
        1. Check cache for existing data
        2. Identify missing date ranges
        3. Fetch only missing data from API
        4. Store fetched data in cache
        5. Return combined dataset
        
        Args:
            symbol: Stock symbol
            start_date: Start date
            end_date: End date
            force_refresh: If True, bypass cache and fetch fresh data
            
        Returns:
            DataFrame with OHLCV data
        """
        logger.info(f"Fetching {symbol} from {start_date.date()} to {end_date.date()}")
        
        if force_refresh:
            logger.info(f"Force refresh - bypassing cache for {symbol}")
            return await self._fetch_and_cache(symbol, start_date, end_date)
        
        # Check cache for existing data
        cached_data = await self._get_cached_data(symbol, start_date, end_date)
        
        if cached_data.empty:
            # No cached data - fetch everything
            logger.info(f"No cached data for {symbol} - fetching from API")
            return await self._fetch_and_cache(symbol, start_date, end_date)
        
        # Find missing date ranges
        missing_ranges = await self._find_missing_ranges(
            symbol, start_date, end_date, cached_data
        )
        
        if not missing_ranges:
            # All data cached
            logger.info(
                f"Complete cache hit for {symbol}: {len(cached_data)} bars from cache"
            )
            return self._dataframe_from_cache(cached_data)
        
        # Partial cache hit - fetch missing data
        logger.info(
            f"Partial cache hit for {symbol}: fetching {len(missing_ranges)} missing ranges"
        )
        
        new_data_frames = []
        for range_start, range_end in missing_ranges:
            logger.debug(f"Fetching missing: {range_start.date()} to {range_end.date()}")
            new_data = await self._fetch_and_cache(symbol, range_start, range_end)
            if not new_data.empty:
                new_data_frames.append(new_data)
        
        # Combine cached and new data
        all_frames = [self._dataframe_from_cache(cached_data)] + new_data_frames
        combined = pd.concat(all_frames)
        combined = combined.sort_index()
        combined = combined[~combined.index.duplicated(keep='first')]
        
        logger.info(
            f"Combined data for {symbol}: {len(combined)} total bars "
            f"({len(cached_data)} cached, {len(combined) - len(cached_data)} fetched)"
        )
        
        return combined
    
    async def _get_cached_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[MarketDataCache]:
        """Fetch cached data for date range."""
        result = await self.db.execute(
            select(MarketDataCache)
            .where(
                and_(
                    MarketDataCache.symbol == symbol,
                    MarketDataCache.date >= start_date.date(),
                    MarketDataCache.date <= end_date.date()
                )
            )
            .order_by(MarketDataCache.date)
        )
        return result.scalars().all()
    
    async def _find_missing_ranges(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        cached_data: List[MarketDataCache]
    ) -> List[Tuple[datetime, datetime]]:
        """
        Identify date ranges that are missing from cache.
        
        Returns list of (start, end) tuples for missing ranges.
        """
        if not cached_data:
            return [(start_date, end_date)]
        
        # Get set of cached dates
        cached_dates = {record.date for record in cached_data}
        
        # Generate all expected trading days (approximate - every day)
        # In production, would use actual trading calendar
        current = start_date.date()
        end = end_date.date()
        
        missing_ranges = []
        range_start = None
        
        while current <= end:
            if current not in cached_dates:
                if range_start is None:
                    range_start = current
            else:
                if range_start is not None:
                    # End of missing range
                    missing_ranges.append((
                        datetime.combine(range_start, datetime.min.time()),
                        datetime.combine(current - timedelta(days=1), datetime.max.time())
                    ))
                    range_start = None
            
            current += timedelta(days=1)
        
        # Handle missing range at end
        if range_start is not None:
            missing_ranges.append((
                datetime.combine(range_start, datetime.min.time()),
                end_date
            ))
        
        return missing_ranges
    
    async def _fetch_and_cache(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime
    ) -> pd.DataFrame:
        """
        Fetch data from API and store in cache.
        Includes chunking for large date ranges.
        """
        date_range_days = (end_date - start_date).days
        
        # Use chunking for large ranges
        if date_range_days <= 180:
            df = await self._fetch_single_chunk(symbol, start_date, end_date)
            if not df.empty:
                await self._store_in_cache(symbol, df)
            return df
        
        # Large range - chunk it
        logger.info(f"Chunking {date_range_days} days into 180-day periods")
        chunks = []
        current_start = start_date
        
        while current_start < end_date:
            current_end = min(
                current_start + timedelta(days=180),
                end_date
            )
            
            chunk_df = await self._fetch_single_chunk(symbol, current_start, current_end)
            if not chunk_df.empty:
                await self._store_in_cache(symbol, chunk_df)
                chunks.append(chunk_df)
            
            current_start = current_end + timedelta(days=1)
        
        if not chunks:
            return pd.DataFrame()
        
        combined = pd.concat(chunks)
        combined = combined.sort_index()
        combined = combined[~combined.index.duplicated(keep='first')]
        
        return combined
    
    async def _fetch_single_chunk(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime
    ) -> pd.DataFrame:
        """Fetch a single chunk from API."""
        try:
            bars = await self.market_data.get_bars(
                symbol=symbol,
                start=start_date,
                end=end_date,
                timeframe="1Day"
            )
            
            df = pd.DataFrame([
                {
                    "timestamp": bar.timestamp,
                    "open": float(bar.open),
                    "high": float(bar.high),
                    "low": float(bar.low),
                    "close": float(bar.close),
                    "volume": int(bar.volume),
                }
                for bar in bars
            ])
            
            if not df.empty:
                df.set_index("timestamp", inplace=True)
            
            return df
            
        except Exception as e:
            logger.error(f"Failed to fetch {symbol}: {e}")
            return pd.DataFrame()
    
    async def _store_in_cache(self, symbol: str, df: pd.DataFrame):
        """Store DataFrame in cache using bulk insert."""
        if df.empty:
            return
        
        records = []
        for timestamp, row in df.iterrows():
            records.append({
                "symbol": symbol,
                "date": timestamp.date(),
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
                "volume": int(row["volume"]),
                "source": "alpaca"
            })
        
        # Use INSERT ... ON CONFLICT DO NOTHING for PostgreSQL
        stmt = insert(MarketDataCache).values(records)
        stmt = stmt.on_conflict_do_nothing(index_elements=['symbol', 'date'])
        
        await self.db.execute(stmt)
        await self.db.commit()
        
        logger.info(f"Cached {len(records)} bars for {symbol}")
    
    def _dataframe_from_cache(
        self,
        cached_data: List[MarketDataCache]
    ) -> pd.DataFrame:
        """Convert cached records to DataFrame."""
        if not cached_data:
            return pd.DataFrame()
        
        df = pd.DataFrame([
            {
                "timestamp": datetime.combine(record.date, datetime.min.time()),
                "open": record.open,
                "high": record.high,
                "low": record.low,
                "close": record.close,
                "volume": record.volume,
            }
            for record in cached_data
        ])
        
        df.set_index("timestamp", inplace=True)
        return df
    
    async def clear_cache(
        self,
        symbol: Optional[str] = None,
        before_date: Optional[date] = None
    ):
        """
        Clear cached data.
        
        Args:
            symbol: If provided, only clear this symbol
            before_date: If provided, only clear data before this date
        """
        query = delete(MarketDataCache)
        
        conditions = []
        if symbol:
            conditions.append(MarketDataCache.symbol == symbol)
        if before_date:
            conditions.append(MarketDataCache.date < before_date)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        result = await self.db.execute(query)
        await self.db.commit()
        
        deleted_count = result.rowcount
        logger.info(f"Cleared {deleted_count} cached records")
        
        return deleted_count
    
    async def get_cache_stats(self, symbol: Optional[str] = None) -> dict:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache stats
        """
        from sqlalchemy import func, distinct
        
        query = select(
            func.count(MarketDataCache.id).label('total_records'),
            func.count(distinct(MarketDataCache.symbol)).label('unique_symbols'),
            func.min(MarketDataCache.date).label('earliest_date'),
            func.max(MarketDataCache.date).label('latest_date')
        )
        
        if symbol:
            query = query.where(MarketDataCache.symbol == symbol)
        
        result = await self.db.execute(query)
        row = result.first()
        
        return {
            'total_records': row.total_records or 0,
            'unique_symbols': row.unique_symbols or 0,
            'earliest_date': row.earliest_date,
            'latest_date': row.latest_date,
            'symbol': symbol
        }
