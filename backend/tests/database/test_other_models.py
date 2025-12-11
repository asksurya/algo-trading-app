"""
Tests for remaining models: RiskRule, Notification, ApiKey, LiveStrategy.

This module tests supporting models used throughout the trading platform.
"""
import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    RiskRule, RiskRuleType, RiskRuleAction,
    Notification, NotificationPreference,
    NotificationType, NotificationChannel, NotificationPriority,
    ApiKey, ApiKeyAuditLog, BrokerType, ApiKeyStatus,
    LiveStrategy, SignalHistory, LiveStrategyStatus, SignalType,
    MarketDataCache,
    User, Strategy,
)


class TestRiskRuleModel:
    """Test suite for RiskRule model."""
    
    @pytest.mark.asyncio
    async def test_create_risk_rule(self, db_session: AsyncSession, test_user: User):
        """Test creating a risk rule."""
        rule = RiskRule(
            user_id=test_user.id,
            name="Max Daily Loss",
            description="Stop trading if daily loss exceeds $1000",
            rule_type=RiskRuleType.MAX_DAILY_LOSS,
            threshold_value=1000.0,
            threshold_unit="dollars",
            action=RiskRuleAction.BLOCK,
            is_active=True,
        )
        db_session.add(rule)
        await db_session.flush()
        
        assert rule.id is not None
        assert rule.rule_type == RiskRuleType.MAX_DAILY_LOSS
        assert rule.action == RiskRuleAction.BLOCK
    
    @pytest.mark.asyncio
    async def test_risk_rule_with_strategy(
        self, db_session: AsyncSession, test_user: User, test_strategy: Strategy
    ):
        """Test risk rule associated with a strategy."""
        rule = RiskRule(
            user_id=test_user.id,
            strategy_id=test_strategy.id,
            name="Strategy Stop Loss",
            rule_type=RiskRuleType.STOP_LOSS,
            threshold_value=5.0,
            threshold_unit="percent",
            action=RiskRuleAction.CLOSE_POSITION,
        )
        db_session.add(rule)
        await db_session.flush()
        
        assert rule.strategy_id == test_strategy.id
    
    @pytest.mark.asyncio
    async def test_risk_rule_breach_tracking(self, db_session: AsyncSession, test_risk_rule: RiskRule):
        """Test tracking risk rule breaches."""
        original_count = test_risk_rule.breach_count
        
        # Simulate breach
        test_risk_rule.breach_count += 1
        test_risk_rule.last_breach_at = datetime.utcnow()
        
        await db_session.flush()
        await db_session.refresh(test_risk_rule)
        
        assert test_risk_rule.breach_count == original_count + 1
        assert test_risk_rule.last_breach_at is not None
    
    @pytest.mark.asyncio
    async def test_all_risk_rule_types(self, db_session: AsyncSession, test_user: User):
        """Test creating rules for all risk rule types."""
        for rule_type in RiskRuleType:
            rule = RiskRule(
                user_id=test_user.id,
                name=f"Rule for {rule_type.name}",
                rule_type=rule_type,
                threshold_value=10.0,
                action=RiskRuleAction.ALERT,
            )
            db_session.add(rule)
        
        await db_session.flush()
        
        result = await db_session.execute(
            select(RiskRule).where(RiskRule.user_id == test_user.id)
        )
        rules = result.scalars().all()
        
        assert len(rules) == len(list(RiskRuleType))


class TestNotificationModel:
    """Test suite for Notification model."""
    
    @pytest.mark.asyncio
    async def test_create_notification(self, db_session: AsyncSession, test_user: User):
        """Test creating a notification."""
        notification = Notification(
            user_id=test_user.id,
            type=NotificationType.RISK_BREACH,
            priority=NotificationPriority.HIGH,
            title="Risk Limit Breached",
            message="Daily loss limit of $1000 has been exceeded.",
            data={"rule_id": "123", "current_loss": 1050.0},
            is_read=False,
            sent_via=["in_app", "email"],
        )
        db_session.add(notification)
        await db_session.flush()
        
        assert notification.id is not None
        assert notification.type == NotificationType.RISK_BREACH
        assert notification.priority == NotificationPriority.HIGH
        assert len(notification.sent_via) == 2
    
    @pytest.mark.asyncio
    async def test_mark_notification_as_read(
        self, db_session: AsyncSession, test_notification: Notification
    ):
        """Test marking a notification as read."""
        assert test_notification.is_read is False
        
        test_notification.is_read = True
        test_notification.read_at = datetime.utcnow()
        
        await db_session.flush()
        await db_session.refresh(test_notification)
        
        assert test_notification.is_read is True
        assert test_notification.read_at is not None
    
    @pytest.mark.asyncio
    async def test_notification_with_expiry(self, db_session: AsyncSession, test_user: User):
        """Test notification with expiration date."""
        notification = Notification(
            user_id=test_user.id,
            type=NotificationType.DAILY_SUMMARY,
            priority=NotificationPriority.LOW,
            title="Daily Summary",
            message="Your trading summary for today.",
            expires_at=datetime.utcnow() + timedelta(days=7),
        )
        db_session.add(notification)
        await db_session.flush()
        
        assert notification.expires_at is not None


class TestNotificationPreferenceModel:
    """Test suite for NotificationPreference model."""
    
    @pytest.mark.asyncio
    async def test_create_notification_preference(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test creating a notification preference."""
        pref = NotificationPreference(
            user_id=test_user.id,
            notification_type=NotificationType.RISK_BREACH,
            channel=NotificationChannel.PUSH,
            is_enabled=True,
            min_priority=NotificationPriority.HIGH,
        )
        db_session.add(pref)
        await db_session.flush()
        
        assert pref.id is not None
        assert pref.channel == NotificationChannel.PUSH
    
    @pytest.mark.asyncio
    async def test_quiet_hours_preference(self, db_session: AsyncSession, test_user: User):
        """Test notification preference with quiet hours."""
        pref = NotificationPreference(
            user_id=test_user.id,
            notification_type=NotificationType.ORDER_FILLED,
            channel=NotificationChannel.PUSH,
            is_enabled=True,
            quiet_hours_enabled=True,
            quiet_start_hour=22,  # 10 PM
            quiet_end_hour=8,    # 8 AM
        )
        db_session.add(pref)
        await db_session.flush()
        
        assert pref.quiet_hours_enabled is True
        assert pref.quiet_start_hour == 22
        assert pref.quiet_end_hour == 8


class TestApiKeyModel:
    """Test suite for ApiKey model."""
    
    @pytest.mark.asyncio
    async def test_create_api_key(self, db_session: AsyncSession, test_user: User):
        """Test creating an API key."""
        api_key = ApiKey(
            user_id=test_user.id,
            broker=BrokerType.ALPACA,
            name="Trading Account",
            description="Main trading account",
            encrypted_api_key="encrypted_key",
            encrypted_api_secret="encrypted_secret",
            is_paper_trading=False,
            status=ApiKeyStatus.ACTIVE,
        )
        db_session.add(api_key)
        await db_session.flush()
        
        assert api_key.id is not None
        assert api_key.broker == BrokerType.ALPACA
        assert api_key.status == ApiKeyStatus.ACTIVE
    
    @pytest.mark.asyncio
    async def test_api_key_usage_tracking(self, db_session: AsyncSession, test_api_key: ApiKey):
        """Test API key usage tracking."""
        original_count = test_api_key.usage_count
        
        test_api_key.usage_count += 1
        test_api_key.last_used_at = datetime.utcnow()
        
        await db_session.flush()
        await db_session.refresh(test_api_key)
        
        assert test_api_key.usage_count == original_count + 1
        assert test_api_key.last_used_at is not None
    
    @pytest.mark.asyncio
    async def test_api_key_error_tracking(self, db_session: AsyncSession, test_api_key: ApiKey):
        """Test API key error tracking."""
        test_api_key.error_count += 1
        test_api_key.last_error = "Authentication failed"
        
        await db_session.flush()
        await db_session.refresh(test_api_key)
        
        assert test_api_key.error_count >= 1
        assert test_api_key.last_error == "Authentication failed"
    
    @pytest.mark.asyncio
    async def test_api_key_revocation(self, db_session: AsyncSession, test_api_key: ApiKey):
        """Test revoking an API key."""
        test_api_key.status = ApiKeyStatus.REVOKED
        test_api_key.revoked_at = datetime.utcnow()
        
        await db_session.flush()
        await db_session.refresh(test_api_key)
        
        assert test_api_key.status == ApiKeyStatus.REVOKED
        assert test_api_key.revoked_at is not None


class TestApiKeyAuditLogModel:
    """Test suite for ApiKeyAuditLog model."""
    
    @pytest.mark.asyncio
    async def test_create_audit_log(
        self, db_session: AsyncSession, test_user: User, test_api_key: ApiKey
    ):
        """Test creating an API key audit log entry."""
        log = ApiKeyAuditLog(
            api_key_id=test_api_key.id,
            user_id=test_user.id,
            action="api_call",
            description="Fetched account balance",
            ip_address="192.168.1.100",
            user_agent="TradingBot/1.0",
            success=True,
        )
        db_session.add(log)
        await db_session.flush()
        
        assert log.id is not None
        assert log.action == "api_call"
        assert log.success is True
    
    @pytest.mark.asyncio
    async def test_audit_log_with_error(
        self, db_session: AsyncSession, test_user: User, test_api_key: ApiKey
    ):
        """Test audit log with error message."""
        log = ApiKeyAuditLog(
            api_key_id=test_api_key.id,
            user_id=test_user.id,
            action="order_submit",
            description="Attempted to submit market order",
            success=False,
            error_message="Insufficient buying power",
        )
        db_session.add(log)
        await db_session.flush()
        
        assert log.success is False
        assert log.error_message == "Insufficient buying power"


class TestLiveStrategyModel:
    """Test suite for LiveStrategy model."""
    
    @pytest.mark.asyncio
    async def test_create_live_strategy(
        self, db_session: AsyncSession, test_user: User, test_strategy: Strategy
    ):
        """Test creating a live strategy."""
        live_strategy = LiveStrategy(
            user_id=test_user.id,
            strategy_id=test_strategy.id,
            name="Live SMA Crossover",
            symbols=["AAPL", "GOOGL", "MSFT"],
            status=LiveStrategyStatus.STOPPED,
            check_interval=60,
            auto_execute=False,
        )
        db_session.add(live_strategy)
        await db_session.flush()
        
        assert live_strategy.id is not None
        assert live_strategy.status == LiveStrategyStatus.STOPPED
        assert len(live_strategy.symbols) == 3
    
    @pytest.mark.asyncio
    async def test_live_strategy_activation(
        self, db_session: AsyncSession, test_live_strategy: LiveStrategy
    ):
        """Test activating a live strategy."""
        test_live_strategy.status = LiveStrategyStatus.ACTIVE
        test_live_strategy.started_at = datetime.utcnow()
        test_live_strategy.auto_execute = True
        
        await db_session.flush()
        await db_session.refresh(test_live_strategy)
        
        assert test_live_strategy.status == LiveStrategyStatus.ACTIVE
        assert test_live_strategy.started_at is not None
    
    @pytest.mark.asyncio
    async def test_live_strategy_performance_tracking(
        self, db_session: AsyncSession, test_live_strategy: LiveStrategy
    ):
        """Test live strategy performance updates."""
        test_live_strategy.total_signals = 10
        test_live_strategy.executed_trades = 8
        test_live_strategy.current_positions = 3
        test_live_strategy.daily_pnl = 250.0
        test_live_strategy.total_pnl = 1500.0
        
        await db_session.flush()
        await db_session.refresh(test_live_strategy)
        
        assert test_live_strategy.total_signals == 10
        assert test_live_strategy.total_pnl == 1500.0
    
    @pytest.mark.asyncio
    async def test_live_strategy_error_state(
        self, db_session: AsyncSession, test_live_strategy: LiveStrategy
    ):
        """Test live strategy error handling."""
        test_live_strategy.status = LiveStrategyStatus.ERROR
        test_live_strategy.error_message = "Connection to broker failed"
        
        await db_session.flush()
        await db_session.refresh(test_live_strategy)
        
        assert test_live_strategy.status == LiveStrategyStatus.ERROR
        assert "Connection" in test_live_strategy.error_message


class TestSignalHistoryModel:
    """Test suite for SignalHistory model."""
    
    @pytest.mark.asyncio
    async def test_create_signal_history(
        self, db_session: AsyncSession, test_live_strategy: LiveStrategy
    ):
        """Test creating a signal history entry."""
        signal = SignalHistory(
            live_strategy_id=test_live_strategy.id,
            symbol="AAPL",
            signal_type=SignalType.BUY,
            signal_strength=0.85,
            price=150.00,
            volume=1000000.0,
            indicators={
                "sma_20": 148.50,
                "sma_50": 145.00,
                "rsi": 65.0,
            },
            executed=False,
        )
        db_session.add(signal)
        await db_session.flush()
        
        assert signal.id is not None
        assert signal.signal_type == SignalType.BUY
        assert signal.signal_strength == 0.85
    
    @pytest.mark.asyncio
    async def test_signal_execution(
        self, db_session: AsyncSession, test_live_strategy: LiveStrategy
    ):
        """Test recording signal execution."""
        signal = SignalHistory(
            live_strategy_id=test_live_strategy.id,
            symbol="GOOGL",
            signal_type=SignalType.SELL,
            price=140.00,
            executed=True,
            execution_price=139.75,
            execution_time=datetime.utcnow(),
        )
        db_session.add(signal)
        await db_session.flush()
        await db_session.refresh(signal)
        
        assert signal.executed is True
        assert signal.execution_price == 139.75
    
    @pytest.mark.asyncio
    async def test_signal_execution_error(
        self, db_session: AsyncSession, test_live_strategy: LiveStrategy
    ):
        """Test recording signal execution error."""
        signal = SignalHistory(
            live_strategy_id=test_live_strategy.id,
            symbol="TSLA",
            signal_type=SignalType.BUY,
            price=200.00,
            executed=False,
            execution_error="Insufficient buying power",
        )
        db_session.add(signal)
        await db_session.flush()
        
        assert signal.executed is False
        assert signal.execution_error is not None


class TestMarketDataCacheModel:
    """Test suite for MarketDataCache model."""
    
    @pytest.mark.asyncio
    async def test_create_market_data_cache(self, db_session: AsyncSession):
        """Test creating market data cache entry."""
        cache = MarketDataCache(
            symbol="AAPL",
            date=datetime(2024, 1, 15).date(),
            open=150.00,
            high=152.50,
            low=149.00,
            close=151.75,
            volume=50000000,
            source="alpaca",
        )
        db_session.add(cache)
        await db_session.flush()
        
        assert cache.id is not None
        assert cache.symbol == "AAPL"
        assert cache.close == 151.75
    
    @pytest.mark.asyncio
    async def test_market_data_cache_multiple_days(self, db_session: AsyncSession):
        """Test caching multiple days of data."""
        base_date = datetime(2024, 1, 1).date()
        
        for i in range(5):
            cache = MarketDataCache(
                symbol="AAPL",
                date=base_date + timedelta(days=i),
                open=150.00 + i,
                high=152.00 + i,
                low=149.00 + i,
                close=151.00 + i,
                volume=50000000,
            )
            db_session.add(cache)
        
        await db_session.flush()
        
        result = await db_session.execute(
            select(MarketDataCache)
            .where(MarketDataCache.symbol == "AAPL")
            .order_by(MarketDataCache.date)
        )
        entries = result.scalars().all()
        
        assert len(entries) == 5
        assert entries[0].close == 151.00
        assert entries[4].close == 155.00
