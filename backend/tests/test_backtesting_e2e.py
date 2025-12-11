import pytest
from unittest.mock import MagicMock, patch
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Mock data for backtesting
def create_mock_data():
    dates = pd.date_range(start="2023-01-01", end="2023-01-31", freq="D")
    df = pd.DataFrame(index=dates)
    # Create a sine wave to ensure crossovers
    # 100 baseline, +/- 10 amplitude, 1.5 cycles
    x = np.linspace(0, 3*np.pi, len(dates))
    df["close"] = 100 + 10 * np.sin(x)
    df["open"] = df["close"]
    df["high"] = df["close"] + 1
    df["low"] = df["close"] - 1
    df["volume"] = 1000000
    return df

@pytest.fixture
def mock_market_data_cache():
    # Patch DataFetcher where it is used in the BacktestEngine
    # The runner imports BacktestEngine, which imports DataFetcher
    with patch("src.backtesting.backtest_engine.DataFetcher") as MockFetcher:
        fetcher_instance = MockFetcher.return_value
        # Mock fetch_historical_data to return our mock dataframe
        fetcher_instance.fetch_historical_data = MagicMock(return_value=create_mock_data())
        yield fetcher_instance

@pytest.mark.asyncio
async def test_backtest_e2e_flow(client, auth_headers, mock_market_data_cache):
    """
    Test the full backtesting flow:
    1. Create a strategy
    2. Create and run a backtest
    3. Verify results
    """
    
    # 1. Create Strategy
    strategy_data = {
        "name": "E2E Test Strategy",
        "description": "Test Strategy",
        "strategy_type": "sma_crossover",
        "parameters": {
            "symbol": "AAPL",
            "short_window": 10,
            "long_window": 20
        }
    }
    
    response = await client.post(
        "/api/v1/strategies",
        json=strategy_data,
        headers=auth_headers
    )
    assert response.status_code == 201
    strategy_id = response.json()["id"]
    
    # 2. Create and Run Backtest
    backtest_data = {
        "strategy_id": strategy_id,
        "name": "E2E Backtest",
        "start_date": "2023-01-01",
        "end_date": "2023-01-31",
        "initial_capital": 10000.0,
        "commission": 0.0,
        "slippage": 0.0
    }
    
    response = await client.post(
        "/api/v1/backtests",
        json=backtest_data,
        headers=auth_headers
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["data"]["status"] == "completed"
    
    backtest_id = data["data"]["id"]
    result = data["data"]["result"]
    
    # 3. Verify Results
    assert result["success"] is True
    metrics = result["metrics"]
    
    # Since our mock data is a steady uptrend, SMA crossover might not trigger many trades
    # depending on window sizes (10/20).
    # With 30 days of data and windows 10/20, we might get one buy signal if short > long.
    # Let's verify we got some result structure back at least.
    
    assert "total_return" in metrics
    assert "total_trades" in metrics
    
    # Verify we can fetch details
    response = await client.get(
        f"/api/v1/backtests/{backtest_id}?include_trades=true",
        headers=auth_headers
    )
    assert response.status_code == 200
    response_data = response.json().get("data", {})
    print(f"Backtest Response: {response.json()}")
    assert response_data["status"] == "completed"
    assert response_data["id"] == backtest_id
    assert response_data["results"] is not None
