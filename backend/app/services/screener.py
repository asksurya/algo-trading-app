"""
Stock screener service for finding stocks based on criteria.
"""
import asyncio
from typing import List, Dict, Optional
import yfinance as yf
from sqlalchemy.ext.asyncio import AsyncSession


class ScreenerService:
    """
    Service for screening stocks based on fundamental and technical criteria.
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def screen_stocks(
        self,
        # Fundamental filters
        min_market_cap: Optional[float] = None,
        max_market_cap: Optional[float] = None,
        min_pe_ratio: Optional[float] = None,
        max_pe_ratio: Optional[float] = None,
        min_dividend_yield: Optional[float] = None,
        # Technical filters
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        min_volume: Optional[int] = None,
        min_rsi: Optional[float] = None,
        max_rsi: Optional[float] = None,
        # Other filters
        sectors: Optional[List[str]] = None,
        exchanges: Optional[List[str]] = None,
        limit: int = 50
    ) -> List[Dict]:
        """
        Screen stocks based on criteria.
        
        Args:
            min_market_cap: Minimum market capitalization
            max_market_cap: Maximum market capitalization
            min_pe_ratio: Minimum P/E ratio
            max_pe_ratio: Maximum P/E ratio
            min_dividend_yield: Minimum dividend yield %
            min_price: Minimum stock price
            max_price: Maximum stock price
            min_volume: Minimum daily volume
            min_rsi: Minimum RSI value
            max_rsi: Maximum RSI value
            sectors: List of sectors to include
            exchanges: List of exchanges (NYSE, NASDAQ, etc.)
            limit: Maximum number of results
        
        Returns:
            List of stock symbols matching criteria
        """
        # TODO: Implement actual screening logic
        # This would typically:
        # 1. Fetch stock universe from data provider
        # 2. Apply filters
        # 3. Calculate technical indicators
        # 4. Return filtered results
        
        # Mock results for now
        mock_results = [
            {
                "symbol": "AAPL",
                "name": "Apple Inc.",
                "price": 180.50,
                "market_cap": 2800000000000,
                "pe_ratio": 28.5,
                "dividend_yield": 0.5,
                "volume": 50000000,
                "rsi": 65,
                "sector": "Technology",
                "exchange": "NASDAQ"
            },
            {
                "symbol": "MSFT",
                "name": "Microsoft Corporation",
                "price": 380.00,
                "market_cap": 2850000000000,
                "pe_ratio": 32.0,
                "dividend_yield": 0.8,
                "volume": 25000000,
                "rsi": 58,
                "sector": "Technology",
                "exchange": "NASDAQ"
            },
            {
                "symbol": "JPM",
                "name": "JPMorgan Chase & Co.",
                "price": 150.00,
                "market_cap": 430000000000,
                "pe_ratio": 10.5,
                "dividend_yield": 2.5,
                "volume": 12000000,
                "rsi": 52,
                "sector": "Financials",
                "exchange": "NYSE"
            }
        ]
        
        # Apply filters to mock data
        results = mock_results
        
        if min_market_cap:
            results = [r for r in results if r["market_cap"] >= min_market_cap]
        if max_market_cap:
            results = [r for r in results if r["market_cap"] <= max_market_cap]
        if min_pe_ratio:
            results = [r for r in results if r["pe_ratio"] >= min_pe_ratio]
        if max_pe_ratio:
            results = [r for r in results if r["pe_ratio"] <= max_pe_ratio]
        if min_price:
            results = [r for r in results if r["price"] >= min_price]
        if max_price:
            results = [r for r in results if r["price"] <= max_price]
        if sectors:
            results = [r for r in results if r["sector"] in sectors]
        if exchanges:
            results = [r for r in results if r["exchange"] in exchanges]
        
        return results[:limit]
    
    async def get_top_gainers(self, limit: int = 10) -> List[Dict]:
        """Get top gaining stocks for the day."""
        # TODO: Implement with real market data
        return []
    
    async def get_top_losers(self, limit: int = 10) -> List[Dict]:
        """Get top losing stocks for the day."""
        # TODO: Implement with real market data
        return []
    
    async def get_most_active(self, limit: int = 10) -> List[Dict]:
        """Get most actively traded stocks by volume."""
        try:
            # Run blocking yfinance call in a separate thread
            data = await asyncio.to_thread(yf.screen, "most_actives")
            quotes = data.get('quotes', [])

            # Map results to standardized format
            results = []
            for q in quotes[:limit]:
                stock = {
                    "symbol": q.get('symbol'),
                    "name": q.get('shortName') or q.get('longName'),
                    "price": q.get('regularMarketPrice'),
                    "market_cap": q.get('marketCap'),
                    "pe_ratio": q.get('trailingPE'),
                    "dividend_yield": q.get('dividendYield'),
                    "volume": q.get('regularMarketVolume'),
                    "exchange": q.get('exchange'),
                    "sector": None  # Will be populated if limit is small
                }
                results.append(stock)

            # Enrich with sector data if limit is small (<= 20)
            # This is done because yf.screen doesn't provide sector info
            if limit <= 20 and results:
                async def _get_sector(stock_dict):
                    try:
                        ticker = yf.Ticker(stock_dict['symbol'])
                        # Accessing .info triggers a network request, so run in thread
                        info = await asyncio.to_thread(lambda: ticker.info)
                        stock_dict['sector'] = info.get('sector')
                    except Exception:
                        pass # Leave as None if fetch fails

                await asyncio.gather(*[_get_sector(r) for r in results])

            return results

        except Exception as e:
            # In a real app we would log this error
            print(f"Error fetching most active stocks: {e}")
            return []


async def get_screener_service(session: AsyncSession) -> ScreenerService:
    """Get screener service instance."""
    return ScreenerService(session)
