"""
Market data cache model for storing historical price data locally.
"""
from sqlalchemy import Column, String, Float, Integer, DateTime, Date, Index, UniqueConstraint
from sqlalchemy.sql import func
from datetime import datetime

from app.models.base import Base


class MarketDataCache(Base):
    """
    Stores historical market data (OHLCV) to reduce API calls.
    Data is stored per symbol per day.
    """
    __tablename__ = "market_data_cache"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(10), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    
    # OHLCV data
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Integer, nullable=False)
    
    # Metadata
    source = Column(String(50), default="alpaca")  # Data source
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Ensure one record per symbol per date
    __table_args__ = (
        UniqueConstraint('symbol', 'date', name='uix_symbol_date'),
        Index('idx_symbol_date_range', 'symbol', 'date'),
    )
    
    def __repr__(self):
        return f"<MarketDataCache(symbol={self.symbol}, date={self.date}, close={self.close})>"
