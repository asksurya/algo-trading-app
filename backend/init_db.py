"""
Initialize database tables.
Run this once before starting the application.
"""
import asyncio
from app.database import Base, get_engine
from app.models import user, strategy, trade  # Import all models


async def init_db():
    """Create all database tables."""
    print("Creating database tables...")
    
    engine = get_engine()
    async with engine.begin() as conn:
        # Drop all tables (optional - comment out in production)
        # await conn.run_sync(Base.metadata.drop_all)
        
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
    
    print("✅ Database tables created successfully!")
    print("\nTables created:")
    print("  - users")
    print("  - strategies")
    print("  - strategy_tickers")
    print("  - trades")
    print("  - positions")


if __name__ == "__main__":
    asyncio.run(init_db())
