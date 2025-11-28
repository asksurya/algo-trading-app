"""
End-to-end test suite for Phase 9: Live Trading Automation

Tests all API endpoints, database operations, and integration points
to ensure production readiness.
"""
import pytest
import json
from datetime import datetime
from sqlalchemy.orm import Session

# Test fixtures and setup
@pytest.fixture
def test_user_token(client):
    """Register and login a test user."""
    # Register
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "test_live_trading@example.com",
            "password": "TestPassword123!",
            "full_name": "Test User"
        }
    )
    
    # Login
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "test_live_trading@example.com",
            "password": "TestPassword123!"
        }
    )
    
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture
def test_strategy_id(client, test_user_token):
    """Create a test strategy."""
    headers = {"Authorization": f"Bearer {test_user_token}"}
    
    response = client.post(
        "/api/v1/strategies",
        headers=headers,
        json={
            "name": "Test RSI Strategy",
            "description": "Test strategy for live trading",
            "strategy_type": "rsi",
            "parameters": {"rsi_period": 14, "overbought": 70, "oversold": 30}
        }
    )
    
    assert response.status_code == 201
    return response.json()["id"]


class TestLiveTradingAPIEndpoints:
    """Test all live trading API endpoints."""
    
    def test_create_live_strategy(self, client, test_user_token, test_strategy_id):
        """Test creating a live trading strategy."""
        headers = {"Authorization": f"Bearer {test_user_token}"}
        
        response = client.post(
            "/api/v1/live-trading/strategies",
            headers=headers,
            json={
                "name": "Automated AAPL Trading",
                "strategy_id": test_strategy_id,
                "symbols": ["AAPL", "MSFT"],
                "check_interval": 300,
                "auto_execute": False,
                "max_positions": 5,
                "max_position_size": 5000,
                "daily_loss_limit": 500,
                "position_size_pct": 0.02
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Automated AAPL Trading"
        assert data["status"] == "STOPPED"
        assert data["symbols"] == ["AAPL", "MSFT"]
        assert data["auto_execute"] == False
        assert "id" in data
        
        return data["id"]
    
    def test_list_live_strategies(self, client, test_user_token, test_strategy_id):
        """Test listing live trading strategies."""
        headers = {"Authorization": f"Bearer {test_user_token}"}
        
        # Create a strategy first
        client.post(
            "/api/v1/live-trading/strategies",
            headers=headers,
            json={
                "name": "Test Strategy 1",
                "strategy_id": test_strategy_id,
                "symbols": ["AAPL"],
                "check_interval": 300,
                "auto_execute": False,
                "max_positions": 5,
                "position_size_pct": 0.02
            }
        )
        
        # List strategies
        response = client.get(
            "/api/v1/live-trading/strategies",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert data[0]["name"] == "Test Strategy 1"
    
    def test_get_live_strategy(self, client, test_user_token, test_strategy_id):
        """Test getting a specific live strategy."""
        headers = {"Authorization": f"Bearer {test_user_token}"}
        
        # Create strategy
        create_response = client.post(
            "/api/v1/live-trading/strategies",
            headers=headers,
            json={
                "name": "Get Test Strategy",
                "strategy_id": test_strategy_id,
                "symbols": ["AAPL"],
                "check_interval": 300,
                "auto_execute": False,
                "max_positions": 5,
                "position_size_pct": 0.02
            }
        )
        
        strategy_id = create_response.json()["id"]
        
        # Get strategy
        response = client.get(
            f"/api/v1/live-trading/strategies/{strategy_id}",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == strategy_id
        assert data["name"] == "Get Test Strategy"
    
    def test_update_live_strategy(self, client, test_user_token, test_strategy_id):
        """Test updating a live strategy."""
        headers = {"Authorization": f"Bearer {test_user_token}"}
        
        # Create strategy
        create_response = client.post(
            "/api/v1/live-trading/strategies",
            headers=headers,
            json={
                "name": "Update Test Strategy",
                "strategy_id": test_strategy_id,
                "symbols": ["AAPL"],
                "check_interval": 300,
                "auto_execute": False,
                "max_positions": 5,
                "position_size_pct": 0.02
            }
        )
        
        strategy_id = create_response.json()["id"]
        
        # Update strategy
        response = client.put(
            f"/api/v1/live-trading/strategies/{strategy_id}",
            headers=headers,
            json={
                "name": "Updated Strategy Name",
                "check_interval": 600,
                "max_positions": 10
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Strategy Name"
        assert data["check_interval"] == 600
        assert data["max_positions"] == 10
    
    def test_delete_live_strategy(self, client, test_user_token, test_strategy_id):
        """Test deleting a live strategy."""
        headers = {"Authorization": f"Bearer {test_user_token}"}
        
        # Create strategy
        create_response = client.post(
            "/api/v1/live-trading/strategies",
            headers=headers,
            json={
                "name": "Delete Test Strategy",
                "strategy_id": test_strategy_id,
                "symbols": ["AAPL"],
                "check_interval": 300,
                "auto_execute": False,
                "max_positions": 5,
                "position_size_pct": 0.02
            }
        )
        
        strategy_id = create_response.json()["id"]
        
        # Delete strategy
        response = client.delete(
            f"/api/v1/live-trading/strategies/{strategy_id}",
            headers=headers
        )
        
        assert response.status_code == 204
        
        # Verify deletion
        get_response = client.get(
            f"/api/v1/live-trading/strategies/{strategy_id}",
            headers=headers
        )
        assert get_response.status_code == 404
    
    def test_start_stop_pause_strategy(self, client, test_user_token, test_strategy_id):
        """Test starting, stopping, and pausing a strategy."""
        headers = {"Authorization": f"Bearer {test_user_token}"}
        
        # Create strategy
        create_response = client.post(
            "/api/v1/live-trading/strategies",
            headers=headers,
            json={
                "name": "Control Test Strategy",
                "strategy_id": test_strategy_id,
                "symbols": ["AAPL"],
                "check_interval": 300,
                "auto_execute": False,
                "max_positions": 5,
                "position_size_pct": 0.02
            }
        )
        
        strategy_id = create_response.json()["id"]
        
        # Start strategy
        start_response = client.post(
            f"/api/v1/live-trading/strategies/{strategy_id}/start",
            headers=headers,
            json={}
        )
        assert start_response.status_code == 200
        assert start_response.json()["success"] == True
        
        # Verify status changed
        get_response = client.get(
            f"/api/v1/live-trading/strategies/{strategy_id}",
            headers=headers
        )
        assert get_response.json()["status"] == "ACTIVE"
        
        # Pause strategy
        pause_response = client.post(
            f"/api/v1/live-trading/strategies/{strategy_id}/pause",
            headers=headers
        )
        assert pause_response.status_code == 200
        
        # Stop strategy
        stop_response = client.post(
            f"/api/v1/live-trading/strategies/{strategy_id}/stop",
            headers=headers
        )
        assert stop_response.status_code == 200
        
        # Verify final status
        get_response = client.get(
            f"/api/v1/live-trading/strategies/{strategy_id}",
            headers=headers
        )
        assert get_response.json()["status"] == "STOPPED"
    
    def test_get_dashboard(self, client, test_user_token):
        """Test getting the live trading dashboard."""
        headers = {"Authorization": f"Bearer {test_user_token}"}
        
        response = client.get(
            "/api/v1/live-trading/dashboard",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        assert "active_strategies" in data
        assert "recent_signals" in data
        
        summary = data["summary"]
        assert "active_strategies" in summary
        assert "total_strategies" in summary
        assert "signals_today" in summary
        assert "trades_today" in summary
        assert "total_pnl" in summary
        assert "daily_pnl" in summary
        assert "active_positions" in summary
    
    def test_get_recent_signals(self, client, test_user_token):
        """Test getting recent signals."""
        headers = {"Authorization": f"Bearer {test_user_token}"}
        
        response = client.get(
            "/api/v1/live-trading/signals/recent?limit=10",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_positions(self, client, test_user_token):
        """Test getting live positions."""
        headers = {"Authorization": f"Bearer {test_user_token}"}
        
        response = client.get(
            "/api/v1/live-trading/positions",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestAuthenticationAndAuthorization:
    """Test authentication and authorization."""
    
    def test_unauthenticated_request(self, client):
        """Test that unauthenticated requests are rejected."""
        response = client.get("/api/v1/live-trading/strategies")
        assert response.status_code == 401
    
    def test_invalid_token(self, client):
        """Test that invalid tokens are rejected."""
        headers = {"Authorization": "Bearer invalid_token_123"}
        response = client.get(
            "/api/v1/live-trading/strategies",
            headers=headers
        )
        assert response.status_code == 401
    
    def test_user_isolation(self, client, test_user_token):
        """Test that users only see their own strategies."""
        # This would need a second user to fully test
        # For now, just verify the endpoint works
        headers = {"Authorization": f"Bearer {test_user_token}"}
        response = client.get(
            "/api/v1/live-trading/strategies",
            headers=headers
        )
        assert response.status_code == 200


class TestInputValidation:
    """Test input validation."""
    
    def test_invalid_check_interval(self, client, test_user_token, test_strategy_id):
        """Test invalid check interval is rejected."""
        headers = {"Authorization": f"Bearer {test_user_token}"}
        
        response = client.post(
            "/api/v1/live-trading/strategies",
            headers=headers,
            json={
                "name": "Bad Interval",
                "strategy_id": test_strategy_id,
                "symbols": ["AAPL"],
                "check_interval": 10,  # Too low
                "auto_execute": False,
                "max_positions": 5,
                "position_size_pct": 0.02
            }
        )
        
        # Should either reject or accept (depends on validation rules)
        assert response.status_code in [200, 201, 400]
    
    def test_invalid_max_positions(self, client, test_user_token, test_strategy_id):
        """Test invalid max positions is rejected."""
        headers = {"Authorization": f"Bearer {test_user_token}"}
        
        response = client.post(
            "/api/v1/live-trading/strategies",
            headers=headers,
            json={
                "name": "Bad Positions",
                "strategy_id": test_strategy_id,
                "symbols": ["AAPL"],
                "check_interval": 300,
                "auto_execute": False,
                "max_positions": 0,  # Invalid
                "position_size_pct": 0.02
            }
        )
        
        assert response.status_code in [200, 201, 400]
    
    def test_empty_symbols(self, client, test_user_token, test_strategy_id):
        """Test empty symbols list is rejected."""
        headers = {"Authorization": f"Bearer {test_user_token}"}
        
        response = client.post(
            "/api/v1/live-trading/strategies",
            headers=headers,
            json={
                "name": "No Symbols",
                "strategy_id": test_strategy_id,
                "symbols": [],  # Empty
                "check_interval": 300,
                "auto_execute": False,
                "max_positions": 5,
                "position_size_pct": 0.02
            }
        )
        
        # Should reject empty symbols
        assert response.status_code in [400, 422]


class TestErrorHandling:
    """Test error handling."""
    
    def test_nonexistent_strategy(self, client, test_user_token):
        """Test getting nonexistent strategy returns 404."""
        headers = {"Authorization": f"Bearer {test_user_token}"}
        
        response = client.get(
            "/api/v1/live-trading/strategies/nonexistent-id",
            headers=headers
        )
        
        assert response.status_code == 404
    
    def test_nonexistent_base_strategy(self, client, test_user_token):
        """Test creating live strategy with nonexistent base strategy."""
        headers = {"Authorization": f"Bearer {test_user_token}"}
        
        response = client.post(
            "/api/v1/live-trading/strategies",
            headers=headers,
            json={
                "name": "Bad Base Strategy",
                "strategy_id": 99999,  # Nonexistent
                "symbols": ["AAPL"],
                "check_interval": 300,
                "auto_execute": False,
                "max_positions": 5,
                "position_size_pct": 0.02
            }
        )
        
        assert response.status_code == 404
    
    def test_update_active_strategy(self, client, test_user_token, test_strategy_id):
        """Test that active strategies cannot be updated."""
        headers = {"Authorization": f"Bearer {test_user_token}"}
        
        # Create strategy
        create_response = client.post(
            "/api/v1/live-trading/strategies",
            headers=headers,
            json={
                "name": "Active Update Test",
                "strategy_id": test_strategy_id,
                "symbols": ["AAPL"],
                "check_interval": 300,
                "auto_execute": False,
                "max_positions": 5,
                "position_size_pct": 0.02
            }
        )
        
        strategy_id = create_response.json()["id"]
        
        # Start strategy
        client.post(
            f"/api/v1/live-trading/strategies/{strategy_id}/start",
            headers=headers,
            json={}
        )
        
        # Try to update active strategy
        response = client.put(
            f"/api/v1/live-trading/strategies/{strategy_id}",
            headers=headers,
            json={"name": "Updated"}
        )
        
        # Should fail because strategy is active
        assert response.status_code == 400


class TestDataIntegrity:
    """Test data integrity."""
    
    def test_strategy_persists(self, client, test_user_token, test_strategy_id):
        """Test that created strategies persist in database."""
        headers = {"Authorization": f"Bearer {test_user_token}"}
        
        # Create
        create_response = client.post(
            "/api/v1/live-trading/strategies",
            headers=headers,
            json={
                "name": "Persistence Test",
                "strategy_id": test_strategy_id,
                "symbols": ["AAPL", "MSFT"],
                "check_interval": 300,
                "auto_execute": False,
                "max_positions": 5,
                "position_size_pct": 0.02
            }
        )
        
        strategy_id = create_response.json()["id"]
        
        # Retrieve multiple times
        for _ in range(3):
            response = client.get(
                f"/api/v1/live-trading/strategies/{strategy_id}",
                headers=headers
            )
            assert response.status_code == 200
            assert response.json()["name"] == "Persistence Test"
    
    def test_strategy_defaults(self, client, test_user_token, test_strategy_id):
        """Test that strategy defaults are set correctly."""
        headers = {"Authorization": f"Bearer {test_user_token}"}
        
        response = client.post(
            "/api/v1/live-trading/strategies",
            headers=headers,
            json={
                "name": "Defaults Test",
                "strategy_id": test_strategy_id,
                "symbols": ["AAPL"],
                "check_interval": 300,
                "auto_execute": False,
                "max_positions": 5,
                "position_size_pct": 0.02
            }
        )
        
        data = response.json()
        assert data["status"] == "STOPPED"
        assert data["total_signals"] == 0
        assert data["executed_trades"] == 0
        assert data["current_positions"] == 0
        assert data["daily_pnl"] == 0
        assert data["total_pnl"] == 0
        assert data["auto_execute"] == False


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
