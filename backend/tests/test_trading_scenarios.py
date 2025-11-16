# backend/tests/test_trading_scenarios.py
import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.main import app
from app.dependencies import get_current_user
from app.models.user import User
from app.core.security import get_password_hash


class TestTradingScenarios:
    @pytest.mark.asyncio
    async def test_create_and_start_strategy(self, client, committed_test_user):
        """Test creating and starting a simple SMA crossover strategy."""
        # 1. Login user to get token
        login_data = {
            "email": committed_test_user.email,
            "password": "testpass123"
        }
        response = client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == status.HTTP_200_OK
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. Create a strategy
        strategy_data = {
            "name": "Test SMA Strategy",
            "description": "A simple SMA crossover strategy for testing.",
            "strategy_type": "sma_crossover",
            "parameters": {"short_window": 20, "long_window": 50},
            "tickers": ["AAPL"]
        }
        response = client.post("/api/v1/strategies", json=strategy_data, headers=headers)
        assert response.status_code == status.HTTP_201_CREATED
        strategy_id = response.json()["id"]

        # 3. Start the strategy
        response = client.post(f"/api/v1/strategies/execution/{strategy_id}/start", headers=headers)
        assert response.status_code == status.HTTP_200_OK
        execution_id = response.json()["data"]["execution_id"]

        # 4. Check that the strategy execution is active
        response = client.get(f"/api/v1/strategies/execution/{strategy_id}/status", headers=headers)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["data"]["is_active"] is True
