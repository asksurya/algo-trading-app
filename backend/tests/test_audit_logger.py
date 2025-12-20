
import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from unittest.mock import MagicMock, AsyncMock
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.audit_logger import AuditLogger
from app.models.enums import AuditEventType
from app.models.audit_log import AuditLog

@pytest.fixture
def mock_session():
    session = AsyncMock(spec=AsyncSession)
    return session

@pytest.mark.asyncio
async def test_log_event(mock_session):
    service = AuditLogger(mock_session)
    user_id = "test_user"
    event_type = AuditEventType.LOGIN
    description = "User logged in"

    result = await service.log_event(user_id, event_type, description)

    assert result["user_id"] == user_id
    assert result["event_type"] == event_type.value
    assert result["description"] == description

    # Verify add was called
    assert mock_session.add.called
    assert mock_session.commit.called
    assert mock_session.refresh.called

@pytest.mark.asyncio
async def test_get_audit_trail(mock_session):
    service = AuditLogger(mock_session)
    user_id = "test_user"

    # Mock return values
    mock_log = AuditLog(
        id=1,
        user_id=user_id,
        event_type=AuditEventType.LOGIN,
        description="Login",
        created_at=datetime.utcnow()
    )

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [mock_log]
    mock_session.execute.return_value = mock_result

    logs = await service.get_audit_trail(user_id=user_id)

    assert len(logs) == 1
    assert logs[0] == mock_log

    # Verify execute was called
    assert mock_session.execute.called

@pytest.mark.asyncio
async def test_generate_compliance_report(mock_session):
    service = AuditLogger(mock_session)
    user_id = "test_user"
    start_date = datetime.utcnow() - timedelta(days=7)
    end_date = datetime.utcnow()

    # Create mock logs for different categories
    trade_log = AuditLog(
        id=1,
        user_id=user_id,
        event_type=AuditEventType.ORDER_FILLED,
        description="Trade executed",
        metadata_data={"symbol": "AAPL", "qty": 10},
        created_at=datetime.utcnow(),
        severity="info"
    )

    risk_log = AuditLog(
        id=2,
        user_id=user_id,
        event_type=AuditEventType.RISK_RULE_TRIGGERED,
        description="Risk rule triggered",
        metadata_data={"rule": "max_drawdown"},
        created_at=datetime.utcnow(),
        severity="warning"
    )

    security_log = AuditLog(
        id=3,
        user_id=user_id,
        event_type=AuditEventType.LOGIN_FAILED,
        description="Login failed",
        metadata_data={},
        created_at=datetime.utcnow(),
        severity="warning"
    )

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [trade_log, risk_log, security_log]
    mock_session.execute.return_value = mock_result

    report = await service.generate_compliance_report(user_id, start_date, end_date)

    assert report["user_id"] == user_id
    assert report["summary"]["total_trades"] == 1
    assert report["summary"]["risk_events"] == 1
    assert report["summary"]["security_events"] == 1
    assert report["summary"]["total_events"] == 3

    assert len(report["details"]["trades"]) == 1
    assert report["details"]["trades"][0]["description"] == "Trade executed"

    assert len(report["details"]["risk_events"]) == 1
    assert len(report["details"]["security_events"]) == 1
