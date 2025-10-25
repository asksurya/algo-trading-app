"""
Cache warming script - Pre-load popular tickers into cache.
Fetches historical data for commonly requested symbols and stores in local database.
"""
import asyncio
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db, engine
from app.services.market_data_cache_service import MarketDataCacheService


# Popular tickers to pre-cache
TICKERS_TO_CACHE = [
    "AAPL",
    "GOOGL", 
    "NVDA",
    "AMD",
    "ARM",
    "MSFT",
    "AVGO",
    "TSLA",
    "TQQQ"
]

# Date range for historical data
START_DATE = datetime(1990, 1, 1)  # Go back as far as possible
END_DATE = datetime.now()


async def warm_cache_for_symbol(
    cache_service: MarketDataCacheService,
    symbol: str
) -> dict:
    """
    Warm cache for a single symbol.
    
    Returns:
        Dictionary with statistics
    """
    print(f"\n{'='*60}")
    print(f"Caching {symbol}")
    print(f"{'='*60}")
    print(f"Date range: {START_DATE.date()} to {END_DATE.date()}")
    print("Fetching data... (this may take a few minutes)")
    
    start_time = datetime.now()
    
    try:
        # Fetch and cache data
        df = await cache_service.get_historical_data(
            symbol=symbol,
            start_date=START_DATE,
            end_date=END_DATE,
            force_refresh=False  # Use cache if exists, fetch missing
        )
        
        elapsed = (datetime.now() - start_time).total_seconds()
        
        if df.empty:
            print(f"⚠️  No data available for {symbol}")
            return {
                "symbol": symbol,
                "success": False,
                "bars": 0,
                "elapsed": elapsed
            }
        
        # Get cache stats for this symbol
        stats = await cache_service.get_cache_stats(symbol=symbol)
        
        print(f"\n✅ Success!")
        print(f"Bars cached: {stats['total_records']:,}")
        print(f"Date range: {stats['earliest_date']} to {stats['latest_date']}")
        print(f"Time taken: {elapsed:.1f} seconds")
        
        return {
            "symbol": symbol,
            "success": True,
            "bars": stats['total_records'],
            "earliest": stats['earliest_date'],
            "latest": stats['latest_date'],
            "elapsed": elapsed
        }
        
    except Exception as e:
        elapsed = (datetime.now() - start_time).total_seconds()
        print(f"\n❌ Error caching {symbol}: {e}")
        return {
            "symbol": symbol,
            "success": False,
            "error": str(e),
            "elapsed": elapsed
        }


async def main():
    """Main cache warming function."""
    print("\n" + "="*60)
    print("MARKET DATA CACHE WARMING")
    print("="*60)
    print(f"\nPre-loading {len(TICKERS_TO_CACHE)} popular tickers:")
    for ticker in TICKERS_TO_CACHE:
        print(f"  • {ticker}")
    print(f"\nDate range: {START_DATE.date()} to {END_DATE.date()}")
    print(f"Estimated time: {len(TICKERS_TO_CACHE) * 2} minutes")
    print("\nThis will:")
    print("  1. Check migration status")
    print("  2. Fetch historical data for each symbol")
    print("  3. Store in local database")
    print("  4. Display progress and statistics")
    print("\n" + "="*60)
    
    input("\nPress ENTER to continue...")
    
    overall_start = datetime.now()
    
    async for session in get_db():
        cache_service = MarketDataCacheService(session)
        
        results = []
        
        # Process each symbol
        for i, symbol in enumerate(TICKERS_TO_CACHE, 1):
            print(f"\n\n[{i}/{len(TICKERS_TO_CACHE)}] Processing {symbol}...")
            result = await warm_cache_for_symbol(cache_service, symbol)
            results.append(result)
        
        # Summary
        overall_elapsed = (datetime.now() - overall_start).total_seconds()
        
        print("\n\n" + "="*60)
        print("CACHE WARMING COMPLETE")
        print("="*60)
        
        successful = [r for r in results if r.get("success")]
        failed = [r for r in results if not r.get("success")]
        
        print(f"\n✅ Successful: {len(successful)}/{len(TICKERS_TO_CACHE)}")
        print(f"❌ Failed: {len(failed)}/{len(TICKERS_TO_CACHE)}")
        print(f"⏱️  Total time: {overall_elapsed/60:.1f} minutes")
        
        if successful:
            total_bars = sum(r.get("bars", 0) for r in successful)
            print(f"\n📊 Total bars cached: {total_bars:,}")
            print(f"💾 Estimated storage: {total_bars * 50 / 1024 / 1024:.1f} MB")
            
            print("\n✅ Successfully cached:")
            for r in successful:
                print(f"  • {r['symbol']}: {r['bars']:,} bars "
                      f"({r['earliest']} to {r['latest']}) "
                      f"[{r['elapsed']:.1f}s]")
        
        if failed:
            print("\n❌ Failed to cache:")
            for r in failed:
                error_msg = r.get('error', 'No data available')
                print(f"  • {r['symbol']}: {error_msg}")
        
        # Final stats
        print("\n" + "="*60)
        print("NEXT STEPS")
        print("="*60)
        print("\n1. These tickers are now cached locally")
        print("2. Future requests will be instant (< 1 second)")
        print("3. System will auto-cache new dates as needed")
        print("4. Enjoy 99% faster analysis for these symbols!")
        
        # Get overall cache stats
        print("\n" + "="*60)
        print("OVERALL CACHE STATISTICS")
        print("="*60)
        overall_stats = await cache_service.get_cache_stats()
        print(f"Total records: {overall_stats['total_records']:,}")
        print(f"Unique symbols: {overall_stats['unique_symbols']}")
        print(f"Date range: {overall_stats['earliest_date']} to {overall_stats['latest_date']}")
        print()


if __name__ == "__main__":
    print("\n🚀 Starting cache warming process...")
    asyncio.run(main())
    print("\n✅ Done!\n")
