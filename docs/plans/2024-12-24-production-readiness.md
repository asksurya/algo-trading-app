# Production Readiness Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make the algo-trading platform production-ready for 2-week live testing with automated signal execution, notifications, and monitoring.

**Architecture:** Six parallel workstreams targeting independent subsystems. Each workstream runs in its own git worktree, enabling concurrent development without merge conflicts.

**Tech Stack:** FastAPI, SQLAlchemy async, Next.js 14, Alpaca API, Redis, PostgreSQL, SMTP/Twilio

---

## Parallel Workstreams Overview

| Worktree Branch | Focus Area | Est. Time |
|-----------------|------------|-----------|
| `feature/signal-execution` | Auto-execute trades from signals | 3-4 hours |
| `feature/market-data-fix` | IEX feed + Yahoo fallback | 2 hours |
| `feature/notifications` | Email/SMS delivery | 3 hours |
| `feature/data-persistence` | Fix in-memory storage | 2 hours |
| `feature/audit-logging` | Trade audit trail | 2 hours |
| `feature/frontend-status` | Live execution UI | 3-4 hours |

---

## Workstream 1: Signal Execution Pipeline

**Branch:** `feature/signal-execution`

**Problem:** Strategies generate signals but don't automatically place orders.

**Files:**
- Modify: `backend/app/strategies/executor.py`
- Modify: `backend/app/services/live_trading_service.py`
- Create: `backend/app/services/signal_executor.py`
- Test: `backend/tests/services/test_signal_executor.py`

---

### Task 1.1: Create Signal Executor Service

**Step 1: Write the failing test**

Create `backend/tests/services/test_signal_executor.py`:

```python
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.signal_executor import SignalExecutor, ExecutionResult

@pytest.mark.asyncio
async def test_signal_executor_places_buy_order():
    """Signal executor should place buy order when BUY signal received."""
    mock_db = AsyncMock()
    executor = SignalExecutor(mock_db)

    signal = {
        "signal_type": "BUY",
        "symbol": "AAPL",
        "price": 150.00,
        "quantity": 10,
        "strategy_id": "test-strategy-123",
        "strength": 0.85
    }

    with patch.object(executor, '_place_order', new_callable=AsyncMock) as mock_place:
        mock_place.return_value = {"order_id": "order-123", "status": "filled"}

        result = await executor.execute_signal(signal, user_id="user-123")

        assert result.success is True
        assert result.order_id == "order-123"
        mock_place.assert_called_once()

@pytest.mark.asyncio
async def test_signal_executor_respects_dry_run():
    """Signal executor should not place orders in dry run mode."""
    mock_db = AsyncMock()
    executor = SignalExecutor(mock_db)

    signal = {
        "signal_type": "BUY",
        "symbol": "AAPL",
        "price": 150.00,
        "quantity": 10,
        "strategy_id": "test-strategy-123"
    }

    result = await executor.execute_signal(signal, user_id="user-123", dry_run=True)

    assert result.success is True
    assert result.dry_run is True
    assert result.order_id is None
```

**Step 2: Run test to verify it fails**

```bash
cd backend && poetry run pytest tests/services/test_signal_executor.py -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'app.services.signal_executor'"

**Step 3: Write the implementation**

Create `backend/app/services/signal_executor.py`:

```python
"""
Signal Executor Service - Converts trading signals into actual orders.
Handles order placement, position sizing, and execution logging.
"""
import logging
from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.paper_trading import get_paper_trading_service
from app.services.live_trading_service import LiveTradingService
from app.models.strategy_execution import StrategySignal, SignalType

logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    """Result of signal execution."""
    success: bool
    order_id: Optional[str] = None
    error: Optional[str] = None
    dry_run: bool = False
    execution_price: Optional[float] = None
    quantity: Optional[float] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)


class SignalExecutor:
    """
    Executes trading signals by placing orders.
    Supports both paper trading and live trading modes.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self._paper_service = None
        self._live_service = None

    @property
    def paper_service(self):
        if self._paper_service is None:
            self._paper_service = get_paper_trading_service(self.db)
        return self._paper_service

    @property
    def live_service(self):
        if self._live_service is None:
            self._live_service = LiveTradingService(self.db)
        return self._live_service

    async def execute_signal(
        self,
        signal: Dict[str, Any],
        user_id: str,
        dry_run: bool = False,
        use_paper_trading: bool = True
    ) -> ExecutionResult:
        """
        Execute a trading signal.

        Args:
            signal: Signal dict with signal_type, symbol, price, quantity
            user_id: User ID for the account
            dry_run: If True, don't actually place orders
            use_paper_trading: If True, use paper trading account

        Returns:
            ExecutionResult with order details or error
        """
        try:
            signal_type = signal.get("signal_type", "").upper()
            symbol = signal.get("symbol")
            price = signal.get("price")
            quantity = signal.get("quantity", self._calculate_position_size(signal))

            if not symbol:
                return ExecutionResult(success=False, error="No symbol in signal")

            if signal_type not in ["BUY", "SELL"]:
                logger.info(f"Signal type {signal_type} - no action needed")
                return ExecutionResult(success=True, dry_run=True)

            if dry_run:
                logger.info(f"DRY RUN: Would {signal_type} {quantity} {symbol} @ {price}")
                return ExecutionResult(
                    success=True,
                    dry_run=True,
                    quantity=quantity,
                    execution_price=price
                )

            # Execute the order
            result = await self._place_order(
                user_id=user_id,
                symbol=symbol,
                quantity=quantity,
                side=signal_type.lower(),
                use_paper=use_paper_trading
            )

            return ExecutionResult(
                success=result.get("success", False),
                order_id=result.get("order_id") or result.get("trade", {}).get("id"),
                execution_price=result.get("price") or result.get("trade", {}).get("price"),
                quantity=quantity,
                error=result.get("error")
            )

        except Exception as e:
            logger.error(f"Signal execution failed: {e}")
            return ExecutionResult(success=False, error=str(e))

    async def _place_order(
        self,
        user_id: str,
        symbol: str,
        quantity: float,
        side: str,
        use_paper: bool = True
    ) -> Dict[str, Any]:
        """Place an order through paper or live trading."""
        if use_paper:
            return await self.paper_service.execute_paper_order(
                user_id=user_id,
                symbol=symbol,
                qty=quantity,
                side=side,
                order_type="market"
            )
        else:
            return await self.live_service.execute_order(
                user_id=user_id,
                symbol=symbol,
                qty=quantity,
                side=side,
                order_type="market"
            )

    def _calculate_position_size(self, signal: Dict[str, Any]) -> float:
        """Calculate position size based on signal strength and risk parameters."""
        # Default to 10 shares if not specified
        base_qty = signal.get("quantity", 10)
        strength = signal.get("strength", 1.0)

        # Scale by signal strength (0.5 to 1.0 multiplier)
        adjusted_qty = int(base_qty * max(0.5, min(1.0, strength)))
        return max(1, adjusted_qty)


def get_signal_executor(db: AsyncSession) -> SignalExecutor:
    """Get signal executor instance."""
    return SignalExecutor(db)
```

**Step 4: Run test to verify it passes**

```bash
cd backend && poetry run pytest tests/services/test_signal_executor.py -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/services/signal_executor.py backend/tests/services/test_signal_executor.py
git commit -m "feat: add signal executor service for auto-trading"
```

---

### Task 1.2: Integrate Signal Executor into Strategy Executor

**Step 1: Modify executor.py to use SignalExecutor**

Modify `backend/app/strategies/executor.py`, add import at top:

```python
from app.services.signal_executor import get_signal_executor, ExecutionResult
```

**Step 2: Update execute_strategy method**

Find the section after signal generation (around line 180) and add:

```python
# After signal is generated and recorded, execute if not dry run
if signal_type != SignalType.HOLD and not execution.is_dry_run:
    signal_executor = get_signal_executor(db)
    exec_result = await signal_executor.execute_signal(
        signal={
            "signal_type": signal_type.value,
            "symbol": symbol,
            "price": current_price,
            "quantity": self._calculate_quantity(strategy, execution, current_price),
            "strategy_id": str(strategy.id),
            "strength": signal_strength
        },
        user_id=strategy.user_id,
        dry_run=execution.is_dry_run,
        use_paper_trading=True  # Default to paper trading
    )

    if exec_result.success and exec_result.order_id:
        result["order_id"] = exec_result.order_id
        result["order_executed"] = True
        execution.last_trade_at = datetime.now(timezone.utc)
```

**Step 3: Run existing tests**

```bash
cd backend && poetry run pytest tests/strategies/ -v
```

**Step 4: Commit**

```bash
git add backend/app/strategies/executor.py
git commit -m "feat: integrate signal executor for automatic order placement"
```

---

## Workstream 2: Market Data Fix (IEX Feed)

**Branch:** `feature/market-data-fix`

**Problem:** Alpaca free tier doesn't support SIP data, need IEX feed.

**Files:**
- Modify: `backend/app/integrations/market_data.py`

---

### Task 2.1: Add IEX Feed Support

**Step 1: Update AlpacaMarketData initialization**

Modify `backend/app/integrations/market_data.py`, update the `__init__` method:

```python
def __init__(self):
    """Initialize Alpaca market data client with IEX feed."""
    if self._client is None:
        try:
            from alpaca.data.enums import DataFeed

            self._client = StockHistoricalDataClient(
                api_key=settings.ALPACA_API_KEY,
                secret_key=settings.ALPACA_SECRET_KEY,
            )
            # Store feed preference for requests
            self._feed = DataFeed.IEX  # Use IEX for free tier
            logger.info("Alpaca market data client initialized with IEX feed")
        except Exception as e:
            logger.error(f"Failed to initialize market data client: {e}")
            raise MarketDataError(f"Client initialization failed: {str(e)}", original_error=e)
```

**Step 2: Update get_bars to use IEX feed**

In the `get_bars` method, update the StockBarsRequest:

```python
from alpaca.data.enums import DataFeed

# In get_bars method, update request creation:
request = StockBarsRequest(
    symbol_or_symbols=symbol,
    timeframe=tf,
    start=start,
    end=end,
    limit=limit,
    feed=DataFeed.IEX,  # Add this line
)
```

**Step 3: Fix datetime.UTC issue**

Add `timezone` to imports and replace all `datetime.UTC` with `timezone.utc`:

```python
from datetime import datetime, timedelta, timezone

# Replace all occurrences of datetime.UTC with timezone.utc
```

**Step 4: Test manually**

```bash
cd backend && poetry run python -c "
import asyncio
from app.integrations.market_data import get_market_data_service
async def test():
    svc = get_market_data_service()
    bars = await svc.get_bars('AAPL', '1Day', limit=5)
    print(f'Got {len(bars)} bars')
asyncio.run(test())
"
```

**Step 5: Commit**

```bash
git add backend/app/integrations/market_data.py
git commit -m "fix: use IEX feed for Alpaca free tier compatibility"
```

---

## Workstream 3: Email/SMS Notifications

**Branch:** `feature/notifications`

**Problem:** No delivery mechanism for trade alerts.

**Files:**
- Create: `backend/app/services/email_service.py`
- Create: `backend/app/services/sms_service.py`
- Modify: `backend/app/services/notification_service.py`
- Modify: `backend/app/core/config.py`

---

### Task 3.1: Create Email Service

**Step 1: Create email service**

Create `backend/app/services/email_service.py`:

```python
"""
Email delivery service using SMTP.
"""
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List
from dataclasses import dataclass

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class EmailMessage:
    """Email message structure."""
    to: List[str]
    subject: str
    body: str
    html_body: Optional[str] = None


class EmailService:
    """SMTP email delivery service."""

    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.from_email = settings.EMAIL_FROM
        self.enabled = bool(self.smtp_host and self.smtp_user)

    async def send_email(self, message: EmailMessage) -> bool:
        """Send an email message."""
        if not self.enabled:
            logger.warning("Email service not configured, skipping send")
            return False

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = message.subject
            msg["From"] = self.from_email
            msg["To"] = ", ".join(message.to)

            # Add plain text
            msg.attach(MIMEText(message.body, "plain"))

            # Add HTML if provided
            if message.html_body:
                msg.attach(MIMEText(message.html_body, "html"))

            # Send via SMTP
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.from_email, message.to, msg.as_string())

            logger.info(f"Email sent to {message.to}: {message.subject}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False

    async def send_trade_notification(
        self,
        to_email: str,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        strategy_name: str
    ) -> bool:
        """Send trade execution notification."""
        subject = f"Trade Executed: {side.upper()} {quantity} {symbol}"
        body = f"""
Trade Notification

Strategy: {strategy_name}
Action: {side.upper()}
Symbol: {symbol}
Quantity: {quantity}
Price: ${price:,.2f}
Total Value: ${quantity * price:,.2f}

This is an automated notification from your Algo Trading Platform.
        """

        html_body = f"""
<html>
<body style="font-family: Arial, sans-serif;">
<h2>Trade Executed</h2>
<table style="border-collapse: collapse;">
<tr><td><strong>Strategy:</strong></td><td>{strategy_name}</td></tr>
<tr><td><strong>Action:</strong></td><td style="color: {'green' if side.lower() == 'buy' else 'red'}">{side.upper()}</td></tr>
<tr><td><strong>Symbol:</strong></td><td>{symbol}</td></tr>
<tr><td><strong>Quantity:</strong></td><td>{quantity}</td></tr>
<tr><td><strong>Price:</strong></td><td>${price:,.2f}</td></tr>
<tr><td><strong>Total:</strong></td><td>${quantity * price:,.2f}</td></tr>
</table>
</body>
</html>
        """

        return await self.send_email(EmailMessage(
            to=[to_email],
            subject=subject,
            body=body,
            html_body=html_body
        ))


_email_service: Optional[EmailService] = None

def get_email_service() -> EmailService:
    """Get singleton email service instance."""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service
```

**Step 2: Add config settings**

Add to `backend/app/core/config.py` in the Settings class:

```python
# Email settings
SMTP_HOST: str = ""
SMTP_PORT: int = 587
SMTP_USER: str = ""
SMTP_PASSWORD: str = ""
EMAIL_FROM: str = "noreply@algo-trading.local"
```

**Step 3: Commit**

```bash
git add backend/app/services/email_service.py backend/app/core/config.py
git commit -m "feat: add email notification service"
```

---

### Task 3.2: Integrate Notifications with Signal Executor

**Step 1: Update SignalExecutor to send notifications**

Add to `backend/app/services/signal_executor.py`:

```python
from app.services.email_service import get_email_service

# In execute_signal method, after successful order:
if exec_result.success and exec_result.order_id:
    # Send notification
    email_service = get_email_service()
    await email_service.send_trade_notification(
        to_email=user_email,  # Need to fetch from user
        symbol=symbol,
        side=signal_type.lower(),
        quantity=quantity,
        price=exec_result.execution_price or price,
        strategy_name=signal.get("strategy_name", "Unknown Strategy")
    )
```

**Step 2: Commit**

```bash
git add backend/app/services/signal_executor.py
git commit -m "feat: send email notifications on trade execution"
```

---

## Workstream 4: Data Persistence Fix

**Branch:** `feature/data-persistence`

**Problem:** Optimization jobs stored in memory, lost on restart.

**Files:**
- Modify: `backend/app/api/v1/optimizer.py`
- Create: `backend/app/models/optimization_job.py`

---

### Task 4.1: Create OptimizationJob Model

**Step 1: Create database model**

Create `backend/app/models/optimization_job.py`:

```python
"""
Optimization job persistence model.
"""
from sqlalchemy import Column, String, DateTime, JSON, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timezone
import uuid
import enum

from app.database import Base


class JobStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class OptimizationJob(Base):
    """Persisted optimization job."""
    __tablename__ = "optimization_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String, nullable=False, index=True)
    strategy_id = Column(String, nullable=False)
    status = Column(SQLEnum(JobStatus), default=JobStatus.PENDING)
    parameters = Column(JSON, default={})
    results = Column(JSON, nullable=True)
    error = Column(String, nullable=True)
    started_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime(timezone=True), nullable=True)

    def to_dict(self):
        return {
            "id": str(self.id),
            "user_id": self.user_id,
            "strategy_id": self.strategy_id,
            "status": self.status.value,
            "parameters": self.parameters,
            "results": self.results,
            "error": self.error,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }
```

**Step 2: Update optimizer.py to use database**

Replace in-memory dict with database queries in `backend/app/api/v1/optimizer.py`.

**Step 3: Create migration**

```bash
cd backend && poetry run alembic revision --autogenerate -m "Add optimization_jobs table"
cd backend && poetry run alembic upgrade head
```

**Step 4: Commit**

```bash
git add backend/app/models/optimization_job.py backend/app/api/v1/optimizer.py
git commit -m "feat: persist optimization jobs to database"
```

---

## Workstream 5: Audit Logging

**Branch:** `feature/audit-logging`

**Problem:** No comprehensive trade audit trail.

**Files:**
- Create: `backend/app/services/trade_audit.py`
- Modify: `backend/app/models/__init__.py`

---

### Task 5.1: Create Trade Audit Service

**Step 1: Create audit service**

Create `backend/app/services/trade_audit.py`:

```python
"""
Trade audit logging service.
Records all trading decisions, signals, and executions.
"""
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import Column, String, DateTime, JSON, Float
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.database import Base

logger = logging.getLogger(__name__)


class TradeAuditLog(Base):
    """Audit log for all trading activities."""
    __tablename__ = "trade_audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    user_id = Column(String, nullable=False, index=True)
    event_type = Column(String, nullable=False, index=True)  # signal, order, fill, error
    strategy_id = Column(String, nullable=True, index=True)
    symbol = Column(String, nullable=True, index=True)
    side = Column(String, nullable=True)  # buy, sell
    quantity = Column(Float, nullable=True)
    price = Column(Float, nullable=True)
    order_id = Column(String, nullable=True)
    details = Column(JSON, default={})


class TradeAuditService:
    """Service for recording trade audit logs."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def log_signal(
        self,
        user_id: str,
        strategy_id: str,
        symbol: str,
        signal_type: str,
        price: float,
        strength: float,
        indicators: Dict[str, Any]
    ):
        """Log a trading signal."""
        log = TradeAuditLog(
            user_id=user_id,
            event_type="signal",
            strategy_id=strategy_id,
            symbol=symbol,
            side=signal_type.lower() if signal_type in ["BUY", "SELL"] else None,
            price=price,
            details={
                "signal_type": signal_type,
                "strength": strength,
                "indicators": indicators
            }
        )
        self.db.add(log)
        await self.db.commit()
        logger.info(f"Audit: Signal {signal_type} for {symbol} @ {price}")

    async def log_order(
        self,
        user_id: str,
        strategy_id: str,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        order_id: str,
        order_type: str = "market"
    ):
        """Log an order placement."""
        log = TradeAuditLog(
            user_id=user_id,
            event_type="order",
            strategy_id=strategy_id,
            symbol=symbol,
            side=side,
            quantity=quantity,
            price=price,
            order_id=order_id,
            details={"order_type": order_type}
        )
        self.db.add(log)
        await self.db.commit()
        logger.info(f"Audit: Order {order_id} - {side} {quantity} {symbol}")

    async def log_error(
        self,
        user_id: str,
        error_type: str,
        error_message: str,
        strategy_id: Optional[str] = None,
        symbol: Optional[str] = None
    ):
        """Log an error event."""
        log = TradeAuditLog(
            user_id=user_id,
            event_type="error",
            strategy_id=strategy_id,
            symbol=symbol,
            details={
                "error_type": error_type,
                "error_message": error_message
            }
        )
        self.db.add(log)
        await self.db.commit()
        logger.error(f"Audit: Error - {error_type}: {error_message}")


def get_trade_audit_service(db: AsyncSession) -> TradeAuditService:
    """Get trade audit service instance."""
    return TradeAuditService(db)
```

**Step 2: Create migration**

```bash
cd backend && poetry run alembic revision --autogenerate -m "Add trade_audit_logs table"
cd backend && poetry run alembic upgrade head
```

**Step 3: Commit**

```bash
git add backend/app/services/trade_audit.py
git commit -m "feat: add trade audit logging service"
```

---

## Workstream 6: Frontend Status UI

**Branch:** `feature/frontend-status`

**Problem:** Can't see live execution status in UI.

**Files:**
- Create: `frontend/src/lib/api/execution.ts`
- Create: `frontend/src/lib/hooks/use-execution.ts`
- Modify: `frontend/src/app/dashboard/strategies/page.tsx`

---

### Task 6.1: Create Execution Status API Client

**Step 1: Create API directory and client**

```bash
mkdir -p frontend/src/lib/api frontend/src/lib/hooks
```

Create `frontend/src/lib/api/execution.ts`:

```typescript
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface ExecutionStatus {
  strategy_id: string;
  is_active: boolean;
  state: string;
  trades_today: number;
  last_signal_at: string | null;
  last_trade_at: string | null;
  error_count: number;
  last_error: string | null;
}

export async function getExecutionStatus(
  strategyId: string,
  token: string
): Promise<ExecutionStatus> {
  const response = await fetch(
    `${API_URL}/api/v1/strategies/execution/${strategyId}/status`,
    {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );

  if (!response.ok) {
    throw new Error('Failed to fetch execution status');
  }

  const data = await response.json();
  return data.data;
}

export async function startExecution(
  strategyId: string,
  token: string
): Promise<void> {
  const response = await fetch(
    `${API_URL}/api/v1/strategies/execution/${strategyId}/start`,
    {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );

  if (!response.ok) {
    throw new Error('Failed to start execution');
  }
}

export async function stopExecution(
  strategyId: string,
  token: string
): Promise<void> {
  const response = await fetch(
    `${API_URL}/api/v1/strategies/execution/${strategyId}/stop`,
    {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );

  if (!response.ok) {
    throw new Error('Failed to stop execution');
  }
}
```

**Step 2: Create React hook**

Create `frontend/src/lib/hooks/use-execution.ts`:

```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getExecutionStatus, startExecution, stopExecution, ExecutionStatus } from '../api/execution';

export function useExecutionStatus(strategyId: string) {
  const token = typeof window !== 'undefined'
    ? localStorage.getItem('access_token')
    : null;

  return useQuery<ExecutionStatus>({
    queryKey: ['execution', strategyId],
    queryFn: () => getExecutionStatus(strategyId, token!),
    enabled: !!token && !!strategyId,
    refetchInterval: 5000, // Poll every 5 seconds
  });
}

export function useStartExecution() {
  const queryClient = useQueryClient();
  const token = typeof window !== 'undefined'
    ? localStorage.getItem('access_token')
    : null;

  return useMutation({
    mutationFn: (strategyId: string) => startExecution(strategyId, token!),
    onSuccess: (_, strategyId) => {
      queryClient.invalidateQueries({ queryKey: ['execution', strategyId] });
    },
  });
}

export function useStopExecution() {
  const queryClient = useQueryClient();
  const token = typeof window !== 'undefined'
    ? localStorage.getItem('access_token')
    : null;

  return useMutation({
    mutationFn: (strategyId: string) => stopExecution(strategyId, token!),
    onSuccess: (_, strategyId) => {
      queryClient.invalidateQueries({ queryKey: ['execution', strategyId] });
    },
  });
}
```

**Step 3: Commit**

```bash
git add frontend/src/lib/
git commit -m "feat: add execution status API and hooks"
```

---

## Merge Strategy

After all workstreams complete:

```bash
# From main branch
git checkout main
git pull

# Merge each feature branch
git merge feature/signal-execution
git merge feature/market-data-fix
git merge feature/notifications
git merge feature/data-persistence
git merge feature/audit-logging
git merge feature/frontend-status

# Or create PRs for each branch
```

---

## Testing Checklist

After merge, verify:

- [ ] Strategy signals auto-execute orders
- [ ] Market data fetches without SIP errors
- [ ] Email notifications send on trade
- [ ] Optimization jobs persist across restart
- [ ] Audit logs record all trades
- [ ] Frontend shows execution status

---

## Estimated Total Time

| Phase | Time |
|-------|------|
| Setup worktrees | 15 min |
| Parallel development (6 streams) | 3-4 hours |
| Integration testing | 1 hour |
| **Total** | **4-5 hours** |
