"""
Apply market data cache migration (006).
Creates the market_data_cache table for storing historical price data.
"""
import asyncio
from sqlalchemy import text
from app.database import engine


async def apply_migration():
    """Apply the market data cache migration."""
    print("=" * 60)
    print("Market Data Cache Migration (006)")
    print("=" * 60)
    print()
    print("This migration adds local caching for historical market data.")
    print()
    
    async with engine.begin() as conn:
        # Check if table already exists
        result = await conn.execute(text(
            "SELECT EXISTS (SELECT FROM information_schema.tables "
            "WHERE table_name = 'market_data_cache')"
        ))
        exists = result.scalar()
        
        if exists:
            print("⚠️  market_data_cache table already exists. Skipping creation.")
            print()
            return
        
        print("Creating market_data_cache table...")
        
        # Create table
        await conn.execute(text("""
            CREATE TABLE market_data_cache (
                id SERIAL PRIMARY KEY,
                symbol VARCHAR(10) NOT NULL,
                date DATE NOT NULL,
                open FLOAT NOT NULL,
                high FLOAT NOT NULL,
                low FLOAT NOT NULL,
                close FLOAT NOT NULL,
                volume INTEGER NOT NULL,
                source VARCHAR(50) DEFAULT 'alpaca',
                created_at TIMESTAMP DEFAULT NOW() NOT NULL,
                updated_at TIMESTAMP DEFAULT NOW() NOT NULL,
                CONSTRAINT uix_symbol_date UNIQUE (symbol, date)
            )
        """))
        
        print("✓ Table created")
        
        # Create indexes
        print("Creating indexes...")
        
        await conn.execute(text(
            "CREATE INDEX idx_market_data_cache_symbol ON market_data_cache(symbol)"
        ))
        print("✓ Created idx_market_data_cache_symbol")
        
        await conn.execute(text(
            "CREATE INDEX idx_market_data_cache_date ON market_data_cache(date)"
        ))
        print("✓ Created idx_market_data_cache_date")
        
        await conn.execute(text(
            "CREATE INDEX idx_symbol_date_range ON market_data_cache(symbol, date)"
        ))
        print("✓ Created idx_symbol_date_range")
        
        print()
        print("=" * 60)
        print("✅ Migration completed successfully!")
        print("=" * 60)
        print()
        print("The system will now cache all historical data locally.")
        print("Benefits:")
        print("  • First request: Fetches from API and caches")
        print("  • Subsequent requests: Instant retrieval from database")
        print("  • Partial cache hits: Only fetches missing date ranges")
        print("  • Reduced API calls: ~90%+ reduction for repeated analysis")
        print()


if __name__ == "__main__":
    asyncio.run(apply_migration())
