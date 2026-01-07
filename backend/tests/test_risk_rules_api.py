"""
Test suite for Risk Rules API endpoints.

Tests cover:
- Creating risk rules
- Listing risk rules with filters
- Retrieving specific risk rules
- Updating risk rules
- Deleting risk rules
- Testing risk rule evaluation
- Portfolio risk metrics retrieval
- Position size calculation
- Authorization and error handling
"""
import pytest
from fastapi import status
from unittest.mock import patch, AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.risk_rule import RiskRule
from app.models.strategy import Strategy
from app.models.enums import RiskRuleType, RiskRuleAction


class TestCreateRiskRule:
    """Test risk rule creation endpoint."""

    async def test_create_risk_rule(self, client, auth_headers, committed_test_user, db: AsyncSession):
        """Test creating a new risk rule."""
        rule_data = {
            "name": "Max Position Size Rule",
            "description": "Limit position size to 5% of portfolio",
            "rule_type": RiskRuleType.MAX_POSITION_SIZE.value,
            "threshold_value": 5000.0,
            "threshold_unit": "dollars",
            "action": RiskRuleAction.BLOCK.value,
            "is_active": True,
            "strategy_id": None
        }

        response = await client.post(
            "/api/v1/risk-rules",
            json=rule_data,
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == rule_data["name"]
        assert data["description"] == rule_data["description"]
        assert data["rule_type"] == rule_data["rule_type"]
        assert data["threshold_value"] == rule_data["threshold_value"]
        assert data["threshold_unit"] == rule_data["threshold_unit"]
        assert data["action"] == rule_data["action"]
        assert data["is_active"] == rule_data["is_active"]
        assert data["user_id"] == committed_test_user.id
        assert "id" in data
        assert data["breach_count"] == 0

    async def test_create_risk_rule_with_strategy(self, client, auth_headers, committed_test_user, db: AsyncSession):
        """Test creating a risk rule associated with a strategy."""
        # First create a strategy for the user
        strategy = Strategy(
            user_id=committed_test_user.id,
            name="Test Strategy",
            description="Test strategy for risk rule"
        )
        db.add(strategy)
        await db.flush()
        await db.refresh(strategy)

        rule_data = {
            "name": "Strategy-Specific Risk Rule",
            "description": "Risk rule for specific strategy",
            "rule_type": RiskRuleType.MAX_DAILY_LOSS.value,
            "threshold_value": 500.0,
            "threshold_unit": "dollars",
            "action": RiskRuleAction.ALERT.value,
            "is_active": True,
            "strategy_id": strategy.id
        }

        response = await client.post(
            "/api/v1/risk-rules",
            json=rule_data,
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["strategy_id"] == strategy.id
        assert data["user_id"] == committed_test_user.id

    async def test_create_risk_rule_with_invalid_strategy(self, client, auth_headers, committed_test_user):
        """Test creating a risk rule with non-existent strategy."""
        rule_data = {
            "name": "Invalid Strategy Rule",
            "description": "This will fail",
            "rule_type": RiskRuleType.MAX_POSITION_SIZE.value,
            "threshold_value": 5000.0,
            "threshold_unit": "dollars",
            "action": RiskRuleAction.BLOCK.value,
            "is_active": True,
            "strategy_id": "nonexistent-strategy-id"
        }

        response = await client.post(
            "/api/v1/risk-rules",
            json=rule_data,
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "Strategy not found" in response.json()["detail"]

    async def test_create_risk_rule_unauthorized(self, client):
        """Test creating a risk rule without authentication."""
        rule_data = {
            "name": "Unauthorized Rule",
            "description": "This should fail",
            "rule_type": RiskRuleType.MAX_POSITION_SIZE.value,
            "threshold_value": 5000.0,
            "threshold_unit": "dollars",
            "action": RiskRuleAction.BLOCK.value,
            "is_active": True
        }

        response = await client.post(
            "/api/v1/risk-rules",
            json=rule_data
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Could not validate credentials" in response.json()["detail"]

    async def test_create_risk_rule_invalid_threshold(self, client, auth_headers):
        """Test creating a risk rule with invalid threshold value."""
        rule_data = {
            "name": "Invalid Threshold Rule",
            "description": "Threshold must be positive",
            "rule_type": RiskRuleType.MAX_POSITION_SIZE.value,
            "threshold_value": -100.0,  # Invalid: negative value
            "threshold_unit": "dollars",
            "action": RiskRuleAction.BLOCK.value,
            "is_active": True
        }

        response = await client.post(
            "/api/v1/risk-rules",
            json=rule_data,
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestListRiskRules:
    """Test risk rule listing endpoint."""

    async def test_list_risk_rules_empty(self, client, auth_headers, committed_test_user):
        """Test listing risk rules when none exist."""
        response = await client.get(
            "/api/v1/risk-rules",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    async def test_list_risk_rules_multiple(self, client, auth_headers, committed_test_user, db: AsyncSession):
        """Test listing multiple risk rules."""
        # Create multiple risk rules
        for i in range(3):
            rule = RiskRule(
                user_id=committed_test_user.id,
                name=f"Risk Rule {i+1}",
                rule_type=RiskRuleType.MAX_POSITION_SIZE,
                threshold_value=1000.0 * (i+1),
                threshold_unit="dollars",
                action=RiskRuleAction.ALERT
            )
            db.add(rule)
        await db.commit()

        response = await client.get(
            "/api/v1/risk-rules",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 3
        # Verify ordering by created_at descending
        assert data[0]["name"] == "Risk Rule 3"
        assert data[1]["name"] == "Risk Rule 2"
        assert data[2]["name"] == "Risk Rule 1"

    async def test_list_risk_rules_filter_by_is_active(self, client, auth_headers, committed_test_user, db: AsyncSession):
        """Test listing risk rules filtered by active status."""
        # Create active and inactive rules
        for i in range(2):
            rule = RiskRule(
                user_id=committed_test_user.id,
                name=f"Active Rule {i+1}",
                rule_type=RiskRuleType.MAX_POSITION_SIZE,
                threshold_value=1000.0,
                threshold_unit="dollars",
                action=RiskRuleAction.ALERT,
                is_active=True
            )
            db.add(rule)

        for i in range(2):
            rule = RiskRule(
                user_id=committed_test_user.id,
                name=f"Inactive Rule {i+1}",
                rule_type=RiskRuleType.MAX_DAILY_LOSS,
                threshold_value=500.0,
                threshold_unit="dollars",
                action=RiskRuleAction.ALERT,
                is_active=False
            )
            db.add(rule)
        await db.commit()

        # Get active rules only
        response = await client.get(
            "/api/v1/risk-rules?is_active=true",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2
        assert all(rule["is_active"] for rule in data)

        # Get inactive rules only
        response = await client.get(
            "/api/v1/risk-rules?is_active=false",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2
        assert all(not rule["is_active"] for rule in data)

    async def test_list_risk_rules_filter_by_strategy(self, client, auth_headers, committed_test_user, db: AsyncSession):
        """Test listing risk rules filtered by strategy."""
        # Create strategies
        strategy1 = Strategy(
            user_id=committed_test_user.id,
            name="Strategy 1"
        )
        strategy2 = Strategy(
            user_id=committed_test_user.id,
            name="Strategy 2"
        )
        db.add(strategy1)
        db.add(strategy2)
        await db.flush()
        await db.refresh(strategy1)
        await db.refresh(strategy2)

        # Create rules for different strategies
        rule1 = RiskRule(
            user_id=committed_test_user.id,
            name="Rule for Strategy 1",
            strategy_id=strategy1.id,
            rule_type=RiskRuleType.MAX_POSITION_SIZE,
            threshold_value=1000.0,
            threshold_unit="dollars",
            action=RiskRuleAction.ALERT
        )
        rule2 = RiskRule(
            user_id=committed_test_user.id,
            name="Rule for Strategy 2",
            strategy_id=strategy2.id,
            rule_type=RiskRuleType.MAX_DAILY_LOSS,
            threshold_value=500.0,
            threshold_unit="dollars",
            action=RiskRuleAction.ALERT
        )
        db.add(rule1)
        db.add(rule2)
        await db.commit()

        # Get rules for strategy1
        response = await client.get(
            f"/api/v1/risk-rules?strategy_id={strategy1.id}",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["strategy_id"] == strategy1.id
        assert data[0]["name"] == "Rule for Strategy 1"

    async def test_list_risk_rules_other_user_isolated(self, client, auth_headers, committed_test_user, db: AsyncSession):
        """Test that users only see their own risk rules."""
        from app.models.user import User
        from app.core.security import get_password_hash

        # Create another user
        other_user = User(
            email="other@example.com",
            hashed_password=get_password_hash("otherpass123"),
            full_name="Other User"
        )
        db.add(other_user)
        await db.flush()

        # Create rules for both users
        rule1 = RiskRule(
            user_id=committed_test_user.id,
            name="User 1 Rule",
            rule_type=RiskRuleType.MAX_POSITION_SIZE,
            threshold_value=1000.0,
            threshold_unit="dollars",
            action=RiskRuleAction.ALERT
        )
        rule2 = RiskRule(
            user_id=other_user.id,
            name="User 2 Rule",
            rule_type=RiskRuleType.MAX_DAILY_LOSS,
            threshold_value=500.0,
            threshold_unit="dollars",
            action=RiskRuleAction.ALERT
        )
        db.add(rule1)
        db.add(rule2)
        await db.commit()

        # List rules - should only see user 1's rule
        response = await client.get(
            "/api/v1/risk-rules",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["user_id"] == committed_test_user.id


class TestGetRiskRule:
    """Test getting a specific risk rule."""

    async def test_get_risk_rule(self, client, auth_headers, committed_test_user, db: AsyncSession):
        """Test retrieving a specific risk rule."""
        rule = RiskRule(
            user_id=committed_test_user.id,
            name="Get Rule Test",
            rule_type=RiskRuleType.MAX_POSITION_SIZE,
            threshold_value=5000.0,
            threshold_unit="dollars",
            action=RiskRuleAction.BLOCK,
            is_active=True
        )
        db.add(rule)
        await db.commit()
        await db.refresh(rule)

        response = await client.get(
            f"/api/v1/risk-rules/{rule.id}",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == rule.id
        assert data["name"] == "Get Rule Test"
        assert data["user_id"] == committed_test_user.id
        assert data["threshold_value"] == 5000.0

    async def test_get_risk_rule_not_found(self, client, auth_headers):
        """Test retrieving a non-existent risk rule."""
        response = await client.get(
            "/api/v1/risk-rules/nonexistent-id",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "Risk rule not found" in response.json()["detail"]

    async def test_get_risk_rule_unauthorized_user(self, client, committed_test_user, db: AsyncSession):
        """Test retrieving a risk rule belonging to another user."""
        from app.models.user import User
        from app.core.security import get_password_hash

        # Create another user
        other_user = User(
            email="other@example.com",
            hashed_password=get_password_hash("otherpass123"),
            full_name="Other User"
        )
        db.add(other_user)
        await db.flush()

        # Create rule for other user
        rule = RiskRule(
            user_id=other_user.id,
            name="Other User's Rule",
            rule_type=RiskRuleType.MAX_POSITION_SIZE,
            threshold_value=5000.0,
            threshold_unit="dollars",
            action=RiskRuleAction.ALERT
        )
        db.add(rule)
        await db.commit()
        await db.refresh(rule)

        # Try to get it with another user's token
        response = await client.get(
            f"/api/v1/risk-rules/{rule.id}",
            headers={"Authorization": "Bearer invalid"}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestUpdateRiskRule:
    """Test updating risk rules."""

    async def test_update_risk_rule(self, client, auth_headers, committed_test_user, db: AsyncSession):
        """Test updating a risk rule."""
        rule = RiskRule(
            user_id=committed_test_user.id,
            name="Original Name",
            description="Original description",
            rule_type=RiskRuleType.MAX_POSITION_SIZE,
            threshold_value=5000.0,
            threshold_unit="dollars",
            action=RiskRuleAction.ALERT,
            is_active=True
        )
        db.add(rule)
        await db.commit()
        await db.refresh(rule)

        update_data = {
            "name": "Updated Name",
            "description": "Updated description",
            "threshold_value": 10000.0,
            "action": RiskRuleAction.BLOCK.value,
            "is_active": False
        }

        response = await client.put(
            f"/api/v1/risk-rules/{rule.id}",
            json=update_data,
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["description"] == "Updated description"
        assert data["threshold_value"] == 10000.0
        assert data["action"] == RiskRuleAction.BLOCK.value
        assert data["is_active"] is False
        assert data["rule_type"] == RiskRuleType.MAX_POSITION_SIZE.value  # Unchanged

    async def test_update_risk_rule_partial(self, client, auth_headers, committed_test_user, db: AsyncSession):
        """Test partial update of a risk rule."""
        rule = RiskRule(
            user_id=committed_test_user.id,
            name="Original Name",
            description="Original description",
            rule_type=RiskRuleType.MAX_POSITION_SIZE,
            threshold_value=5000.0,
            threshold_unit="dollars",
            action=RiskRuleAction.ALERT,
            is_active=True
        )
        db.add(rule)
        await db.commit()
        await db.refresh(rule)

        # Only update name
        update_data = {"name": "Partially Updated Name"}

        response = await client.put(
            f"/api/v1/risk-rules/{rule.id}",
            json=update_data,
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "Partially Updated Name"
        assert data["description"] == "Original description"  # Unchanged
        assert data["threshold_value"] == 5000.0  # Unchanged

    async def test_update_risk_rule_not_found(self, client, auth_headers):
        """Test updating a non-existent risk rule."""
        update_data = {"name": "Updated Name"}

        response = await client.put(
            "/api/v1/risk-rules/nonexistent-id",
            json=update_data,
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "Risk rule not found" in response.json()["detail"]

    async def test_update_risk_rule_unauthorized_user(self, client, committed_test_user, db: AsyncSession):
        """Test updating a risk rule belonging to another user."""
        from app.models.user import User
        from app.core.security import get_password_hash

        # Create another user
        other_user = User(
            email="other@example.com",
            hashed_password=get_password_hash("otherpass123"),
            full_name="Other User"
        )
        db.add(other_user)
        await db.flush()

        # Create rule for other user
        rule = RiskRule(
            user_id=other_user.id,
            name="Other User's Rule",
            rule_type=RiskRuleType.MAX_POSITION_SIZE,
            threshold_value=5000.0,
            threshold_unit="dollars",
            action=RiskRuleAction.ALERT
        )
        db.add(rule)
        await db.commit()
        await db.refresh(rule)

        # Try to update with another user's token
        response = await client.put(
            f"/api/v1/risk-rules/{rule.id}",
            json={"name": "Attempted Update"},
            headers={"Authorization": "Bearer invalid"}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestDeleteRiskRule:
    """Test deleting risk rules."""

    async def test_delete_risk_rule(self, client, auth_headers, committed_test_user, db: AsyncSession):
        """Test deleting a risk rule."""
        rule = RiskRule(
            user_id=committed_test_user.id,
            name="Rule to Delete",
            rule_type=RiskRuleType.MAX_POSITION_SIZE,
            threshold_value=5000.0,
            threshold_unit="dollars",
            action=RiskRuleAction.ALERT
        )
        db.add(rule)
        await db.commit()
        await db.refresh(rule)
        rule_id = rule.id

        response = await client.delete(
            f"/api/v1/risk-rules/{rule_id}",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify rule was deleted
        from sqlalchemy import select
        result = await db.execute(select(RiskRule).where(RiskRule.id == rule_id))
        assert result.scalar_one_or_none() is None

    async def test_delete_risk_rule_not_found(self, client, auth_headers):
        """Test deleting a non-existent risk rule."""
        response = await client.delete(
            "/api/v1/risk-rules/nonexistent-id",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "Risk rule not found" in response.json()["detail"]

    async def test_delete_risk_rule_unauthorized_user(self, client, committed_test_user, db: AsyncSession):
        """Test deleting a risk rule belonging to another user."""
        from app.models.user import User
        from app.core.security import get_password_hash

        # Create another user
        other_user = User(
            email="other@example.com",
            hashed_password=get_password_hash("otherpass123"),
            full_name="Other User"
        )
        db.add(other_user)
        await db.flush()

        # Create rule for other user
        rule = RiskRule(
            user_id=other_user.id,
            name="Other User's Rule",
            rule_type=RiskRuleType.MAX_POSITION_SIZE,
            threshold_value=5000.0,
            threshold_unit="dollars",
            action=RiskRuleAction.ALERT
        )
        db.add(rule)
        await db.commit()
        await db.refresh(rule)

        # Try to delete with another user's token
        response = await client.delete(
            f"/api/v1/risk-rules/{rule.id}",
            headers={"Authorization": "Bearer invalid"}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestGetPortfolioRisk:
    """Test portfolio risk metrics endpoint."""

    @patch("app.api.v1.risk_rules.get_alpaca_client")
    @patch("app.api.v1.risk_rules.RiskManager")
    async def test_get_portfolio_risk(self, mock_risk_manager_class, mock_get_alpaca_client, client, auth_headers, committed_test_user):
        """Test retrieving portfolio risk metrics."""
        # Setup mocks
        mock_alpaca_client = AsyncMock()
        mock_get_alpaca_client.return_value = mock_alpaca_client

        mock_risk_manager = AsyncMock()
        mock_risk_manager_class.return_value = mock_risk_manager
        mock_risk_manager.get_portfolio_risk_metrics.return_value = {
            "account_value": 100000.0,
            "buying_power": 100000.0,
            "total_position_value": 50000.0,
            "cash": 50000.0,
            "number_of_positions": 5,
            "daily_pl": 500.0,
            "daily_pl_percent": 0.5,
            "total_unrealized_pl": 1000.0,
            "total_unrealized_pl_percent": 2.0,
            "leverage": 1.0,
            "max_drawdown_percent": -5.0
        }

        response = await client.get(
            "/api/v1/risk-rules/portfolio-risk",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["account_value"] == 100000.0
        assert data["buying_power"] == 100000.0
        assert data["total_position_value"] == 50000.0
        assert data["cash"] == 50000.0
        assert data["number_of_positions"] == 5
        assert data["daily_pl"] == 500.0
        assert data["daily_pl_percent"] == 0.5
        assert data["leverage"] == 1.0

    @patch("app.api.v1.risk_rules.get_alpaca_client")
    @patch("app.api.v1.risk_rules.RiskManager")
    async def test_get_portfolio_risk_fallback_on_error(self, mock_risk_manager_class, mock_get_alpaca_client, client, auth_headers):
        """Test portfolio risk endpoint returns defaults on error."""
        # Setup mocks to raise exception
        mock_alpaca_client = AsyncMock()
        mock_get_alpaca_client.return_value = mock_alpaca_client

        mock_risk_manager = AsyncMock()
        mock_risk_manager_class.return_value = mock_risk_manager
        mock_risk_manager.get_portfolio_risk_metrics.side_effect = Exception("API Error")

        response = await client.get(
            "/api/v1/risk-rules/portfolio-risk",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # Verify defaults are returned
        assert data["account_value"] == 0.0
        assert data["buying_power"] == 0.0
        assert data["leverage"] == 0.0

    async def test_get_portfolio_risk_unauthorized(self, client):
        """Test portfolio risk endpoint without authentication."""
        response = await client.get("/api/v1/risk-rules/portfolio-risk")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestTestRiskRule:
    """Test risk rule evaluation endpoint."""

    @patch("app.api.v1.risk_rules.get_alpaca_client")
    @patch("app.api.v1.risk_rules.RiskManager")
    async def test_test_risk_rule_no_breaches(self, mock_risk_manager_class, mock_get_alpaca_client, client, auth_headers, committed_test_user):
        """Test evaluating a risk rule with no breaches."""
        # Setup mocks
        mock_alpaca_client = AsyncMock()
        mock_get_alpaca_client.return_value = mock_alpaca_client

        mock_risk_manager = AsyncMock()
        mock_risk_manager_class.return_value = mock_risk_manager
        mock_risk_manager.evaluate_rules.return_value = []

        test_request = {
            "strategy_id": None,
            "symbol": "AAPL",
            "order_qty": 100.0,
            "order_value": 15000.0
        }

        response = await client.post(
            "/api/v1/risk-rules/test",
            json=test_request,
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["would_block"] is False
        assert data["would_warn"] is False
        assert len(data["breaches"]) == 0

    @patch("app.api.v1.risk_rules.get_alpaca_client")
    @patch("app.api.v1.risk_rules.RiskManager")
    async def test_test_risk_rule_with_breaches(self, mock_risk_manager_class, mock_get_alpaca_client, client, auth_headers, committed_test_user):
        """Test evaluating a risk rule with breaches."""
        # Setup mocks
        mock_alpaca_client = AsyncMock()
        mock_get_alpaca_client.return_value = mock_alpaca_client

        mock_breach = MagicMock()
        mock_breach.rule_id = "rule-123"
        mock_breach.rule_name = "Max Position Size"
        mock_breach.rule_type = RiskRuleType.MAX_POSITION_SIZE
        mock_breach.threshold = 10000.0
        mock_breach.current_value = 15000.0
        mock_breach.action = "BLOCK"
        mock_breach.message = "Position size exceeds maximum"

        mock_risk_manager = AsyncMock()
        mock_risk_manager_class.return_value = mock_risk_manager
        mock_risk_manager.evaluate_rules.return_value = [mock_breach]

        test_request = {
            "strategy_id": None,
            "symbol": "AAPL",
            "order_qty": 150.0,
            "order_value": 20000.0
        }

        response = await client.post(
            "/api/v1/risk-rules/test",
            json=test_request,
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["would_block"] is True
        assert data["would_warn"] is False
        assert len(data["breaches"]) == 1
        assert data["breaches"][0]["rule_id"] == "rule-123"
        assert data["breaches"][0]["action"] == "BLOCK"

    @patch("app.api.v1.risk_rules.get_alpaca_client")
    @patch("app.api.v1.risk_rules.RiskManager")
    async def test_test_risk_rule_with_alert(self, mock_risk_manager_class, mock_get_alpaca_client, client, auth_headers, committed_test_user):
        """Test evaluating a risk rule with alert action."""
        # Setup mocks
        mock_alpaca_client = AsyncMock()
        mock_get_alpaca_client.return_value = mock_alpaca_client

        mock_breach = MagicMock()
        mock_breach.rule_id = "rule-456"
        mock_breach.rule_name = "Daily Loss Limit"
        mock_breach.rule_type = RiskRuleType.MAX_DAILY_LOSS
        mock_breach.threshold = 500.0
        mock_breach.current_value = 600.0
        mock_breach.action = "WARN"
        mock_breach.message = "Approaching daily loss limit"

        mock_risk_manager = AsyncMock()
        mock_risk_manager_class.return_value = mock_risk_manager
        mock_risk_manager.evaluate_rules.return_value = [mock_breach]

        test_request = {
            "strategy_id": None,
            "symbol": "TSLA",
            "order_qty": 50.0,
            "order_value": 8000.0
        }

        response = await client.post(
            "/api/v1/risk-rules/test",
            json=test_request,
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["would_warn"] is True
        assert data["would_block"] is False
        assert len(data["breaches"]) == 1

    async def test_test_risk_rule_unauthorized(self, client):
        """Test risk rule test endpoint without authentication."""
        test_request = {
            "symbol": "AAPL",
            "order_qty": 100.0,
            "order_value": 15000.0
        }

        response = await client.post(
            "/api/v1/risk-rules/test",
            json=test_request
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestCalculatePositionSize:
    """Test position size calculation endpoint."""

    @patch("app.api.v1.risk_rules.get_alpaca_client")
    @patch("app.api.v1.risk_rules.RiskManager")
    async def test_calculate_position_size(self, mock_risk_manager_class, mock_get_alpaca_client, client, auth_headers, committed_test_user):
        """Test calculating position size based on risk rules."""
        # Setup mocks
        mock_alpaca_client = AsyncMock()
        mock_get_alpaca_client.return_value = mock_alpaca_client

        mock_risk_manager = AsyncMock()
        mock_risk_manager_class.return_value = mock_risk_manager
        mock_risk_manager.calculate_position_size.return_value = {
            "recommended_shares": 50,
            "recommended_value": 7500.0,
            "max_loss": 250.0,
            "risk_per_share": 5.0,
            "account_value": 100000.0,
            "risk_percentage": 0.25
        }

        request_data = {
            "strategy_id": None,
            "symbol": "AAPL",
            "entry_price": 150.0,
            "stop_loss": 145.0
        }

        response = await client.post(
            "/api/v1/risk-rules/calculate-position-size",
            json=request_data,
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["symbol"] == "AAPL"
        assert data["recommended_shares"] == 50
        assert data["recommended_value"] == 7500.0
        assert data["max_loss"] == 250.0
        assert data["risk_per_share"] == 5.0
        assert data["account_value"] == 100000.0
        assert data["risk_percentage"] == 0.25

    @patch("app.api.v1.risk_rules.get_alpaca_client")
    @patch("app.api.v1.risk_rules.RiskManager")
    async def test_calculate_position_size_fallback_on_error(self, mock_risk_manager_class, mock_get_alpaca_client, client, auth_headers):
        """Test position size calculation returns safe defaults on error."""
        # Setup mocks to raise exception
        mock_alpaca_client = AsyncMock()
        mock_get_alpaca_client.return_value = mock_alpaca_client

        mock_risk_manager = AsyncMock()
        mock_risk_manager_class.return_value = mock_risk_manager
        mock_risk_manager.calculate_position_size.side_effect = Exception("Calculation Error")

        request_data = {
            "strategy_id": None,
            "symbol": "AAPL",
            "entry_price": 150.0,
            "stop_loss": 145.0
        }

        response = await client.post(
            "/api/v1/risk-rules/calculate-position-size",
            json=request_data,
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # Verify safe defaults
        assert data["symbol"] == "AAPL"
        assert data["recommended_shares"] == 0
        assert data["recommended_value"] == 0.0
        assert data["risk_per_share"] == 5.0  # 150 - 145

    @patch("app.api.v1.risk_rules.get_alpaca_client")
    @patch("app.api.v1.risk_rules.RiskManager")
    async def test_calculate_position_size_without_stop_loss(self, mock_risk_manager_class, mock_get_alpaca_client, client, auth_headers):
        """Test calculating position size without explicit stop loss."""
        # Setup mocks
        mock_alpaca_client = AsyncMock()
        mock_get_alpaca_client.return_value = mock_alpaca_client

        mock_risk_manager = AsyncMock()
        mock_risk_manager_class.return_value = mock_risk_manager
        mock_risk_manager.calculate_position_size.return_value = {
            "recommended_shares": 100,
            "recommended_value": 15000.0,
            "max_loss": 750.0,
            "risk_per_share": 7.5,  # 5% of entry price
            "account_value": 100000.0,
            "risk_percentage": 0.75
        }

        request_data = {
            "strategy_id": None,
            "symbol": "TSLA",
            "entry_price": 200.0,
            "stop_loss": None
        }

        response = await client.post(
            "/api/v1/risk-rules/calculate-position-size",
            json=request_data,
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["symbol"] == "TSLA"
        assert data["recommended_shares"] == 100

    async def test_calculate_position_size_unauthorized(self, client):
        """Test position size calculation without authentication."""
        request_data = {
            "symbol": "AAPL",
            "entry_price": 150.0,
            "stop_loss": 145.0
        }

        response = await client.post(
            "/api/v1/risk-rules/calculate-position-size",
            json=request_data
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
