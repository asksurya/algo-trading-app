"""
Integrations package for external services.
Provides interfaces to broker APIs, market data, and order execution.
"""
from app.integrations.alpaca_client import AlpacaClient, get_alpaca_client

__all__ = ["AlpacaClient", "get_alpaca_client"]