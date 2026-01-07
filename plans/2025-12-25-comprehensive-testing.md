# Comprehensive Testing Implementation Plan

## Overview

Implement complete test coverage for the algo-trading-app based on the gaps identified in TESTING_PLAN.md. This plan uses parallel haiku sub-agents for efficient test file generation.

## Current State Analysis

### Backend (23% routes, 26% services tested)
- **Tested**: Auth routes, database models, paper trading service, news service
- **Untested**: Orders, Broker, Strategy Execution, Risk Rules routes; Live Trading, Risk Manager, Order Validation, Portfolio Analytics services

### Frontend (26% pages, 83% hooks, 75% API clients tested)
- **Tested**: Login, Register, Dashboard, Settings pages; most hooks and API clients
- **Untested**: 14 pages (trades, strategies, optimizer, portfolio, etc.); use-execution hook; optimizer and execution API clients

### Key Discoveries:
- Backend uses `@pytest.mark.asyncio` with `AsyncMock` for services (`backend/tests/test_paper_trading_service.py:14-56`)
- Frontend uses `renderHook` with QueryClient wrapper (`frontend/src/lib/hooks/__tests__/use-strategies.test.tsx:1-150`)
- Fixtures in `backend/tests/conftest.py:34-128` provide `client`, `db`, `auth_headers`
- Frontend fixtures in `frontend/src/lib/__tests__/fixtures.ts` provide mock data

## Desired End State

- Backend route coverage: 90%+ (all critical endpoints tested)
- Backend service coverage: 85%+ (all business logic tested)
- Frontend page coverage: 90%+ (all pages have unit tests)
- Frontend hooks/API clients: 100% (complete coverage)
- All tests passing with `npm test` and `poetry run pytest`

## What We're NOT Doing

- Performance/load testing
- Security penetration testing
- WebSocket real-time streaming tests (complex infrastructure)
- Full E2E test expansion (covered in separate plan)
- shadcn/ui component tests (pre-tested library)

## Implementation Approach

Use parallel haiku sub-agents to write tests efficiently. Each phase spawns 2-4 agents working on independent test files simultaneously.

---

## Phase 1: Backend Critical Route Tests

### Overview
Create API route tests for the 4 highest-priority endpoints that handle orders and trading.

### Changes Required:

#### 1. Orders API Tests
**File**: `backend/tests/test_orders_api.py`

```python
# Template structure based on test_auth.py patterns
import pytest
from fastapi import status
from unittest.mock import AsyncMock, patch, MagicMock

class TestOrdersAPI:
    """Test orders API endpoints."""

    async def test_place_market_order(self, client, auth_headers):
        """Test placing a market order."""
        with patch('app.api.v1.orders.get_order_executor') as mock_executor:
            mock_executor.return_value.place_order = AsyncMock(return_value={
                "id": "order-123",
                "symbol": "AAPL",
                "qty": 10,
                "side": "buy",
                "status": "accepted"
            })

            response = await client.post(
                "/api/v1/orders",
                json={"symbol": "AAPL", "qty": 10, "side": "buy", "type": "market"},
                headers=auth_headers
            )
            assert response.status_code == status.HTTP_201_CREATED

    async def test_place_order_unauthorized(self, client):
        """Test order placement without auth."""
        response = await client.post("/api/v1/orders", json={})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # Additional tests for: bracket orders, cancel, modify, close position
```

**Tests needed**:
- `test_place_market_order` - POST /orders with market order
- `test_place_limit_order` - POST /orders with limit order
- `test_place_bracket_order` - POST /orders/bracket
- `test_cancel_order` - DELETE /orders/{id}
- `test_modify_order` - PATCH /orders/{id}
- `test_cancel_all_orders` - DELETE /orders
- `test_close_position` - POST /positions/{symbol}/close
- `test_close_all_positions` - DELETE /positions
- `test_order_risk_check_blocked` - Order blocked by risk rules
- `test_order_validation_failure` - Invalid order parameters

#### 2. Broker API Tests
**File**: `backend/tests/test_broker_api.py`

**Tests needed**:
- `test_get_account` - GET /broker/account
- `test_get_positions` - GET /broker/positions
- `test_get_orders` - GET /broker/orders with filters
- `test_invalidate_cache` - POST /broker/cache/invalidate
- `test_get_quote` - GET /broker/market/quote/{symbol}
- `test_get_quotes_multiple` - GET /broker/market/quotes
- `test_get_bars` - GET /broker/market/bars/{symbol}
- `test_get_snapshot` - GET /broker/market/snapshot/{symbol}
- `test_broker_api_error_handling` - Alpaca API failures

#### 3. Strategy Execution API Tests
**File**: `backend/tests/test_strategy_execution_api.py`

**Tests needed**:
- `test_start_execution` - POST /strategies/{id}/execution/start
- `test_stop_execution` - POST /strategies/{id}/execution/stop
- `test_get_execution_status` - GET /strategies/{id}/execution/status
- `test_get_signals` - GET /strategies/{id}/signals
- `test_get_performance` - GET /strategies/{id}/performance
- `test_test_execution` - POST /strategies/{id}/test (dry run)
- `test_reset_execution` - POST /strategies/{id}/reset
- `test_scheduler_status` - GET /scheduler/status
- `test_execution_not_found` - 404 for missing strategy

#### 4. Risk Rules API Tests
**File**: `backend/tests/test_risk_rules_api.py`

**Tests needed**:
- `test_create_risk_rule` - POST /risk-rules
- `test_list_risk_rules` - GET /risk-rules
- `test_get_portfolio_risk` - GET /risk-rules/portfolio-risk
- `test_get_risk_rule` - GET /risk-rules/{id}
- `test_update_risk_rule` - PUT /risk-rules/{id}
- `test_delete_risk_rule` - DELETE /risk-rules/{id}
- `test_test_risk_rule` - POST /risk-rules/test
- `test_calculate_position_size` - POST /risk-rules/calculate-position-size

### Success Criteria:

#### Automated Verification:
- [ ] All 4 test files created and importable
- [ ] Tests pass: `cd backend && poetry run pytest tests/test_orders_api.py tests/test_broker_api.py tests/test_strategy_execution_api.py tests/test_risk_rules_api.py -v`
- [ ] No import errors or syntax issues
- [ ] At least 8 tests per file (32+ total new tests)

#### Manual Verification:
- [ ] Review test coverage for edge cases
- [ ] Verify mocking patterns match existing codebase style

**Implementation Note**: Spawn 4 haiku sub-agents in parallel, one for each test file.

---

## Phase 2: Backend Critical Service Tests

### Overview
Create service layer tests for the 4 critical business logic services.

### Changes Required:

#### 1. Live Trading Service Tests
**File**: `backend/tests/test_live_trading_service_unit.py`

```python
# Template based on test_paper_trading_service.py patterns
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.live_trading_service import LiveTradingService

@pytest.fixture
def mock_session():
    return AsyncMock()

@pytest.mark.asyncio
async def test_get_system_status(mock_session):
    with patch('app.services.live_trading_service.AlpacaClient') as MockClient:
        mock_client = AsyncMock()
        MockClient.return_value = mock_client
        mock_client.get_account.return_value = {"status": "ACTIVE"}

        service = LiveTradingService(mock_session)
        status = await service.get_system_status()

        assert status["account_status"] == "ACTIVE"
```

**Tests needed**:
- `test_get_system_status` - System status retrieval
- `test_get_portfolio` - Portfolio details with positions
- `test_perform_action_reset` - Reset action
- `test_perform_action_pause` - Pause strategies
- `test_perform_action_resume` - Resume strategies
- `test_get_active_strategies` - List active strategy IDs
- `test_execute_order` - Order execution

#### 2. Risk Manager Service Tests
**File**: `backend/tests/test_risk_manager_service.py`

**Tests needed**:
- `test_evaluate_rules_no_breach` - Rules pass
- `test_evaluate_rules_breach_block` - Rule breach blocks trade
- `test_evaluate_rules_breach_warn` - Rule breach warns
- `test_check_max_position_size` - Position size rule
- `test_check_max_daily_loss` - Daily loss limit
- `test_check_max_drawdown` - Drawdown check
- `test_check_position_limit` - Position count limit
- `test_check_max_leverage` - Leverage limit
- `test_calculate_position_size` - Position sizing
- `test_get_portfolio_risk_metrics` - Risk metrics

#### 3. Order Validation Service Tests
**File**: `backend/tests/test_order_validation_service.py`

**Tests needed**:
- `test_validate_order_success` - Valid order passes
- `test_validate_quantity_zero` - Zero quantity fails
- `test_validate_symbol_invalid` - Invalid symbol fails
- `test_validate_order_type_prices` - Limit order needs price
- `test_validate_market_hours` - Extended hours check
- `test_validate_buying_power` - Insufficient funds
- `test_validate_price_reasonability` - Price too far from market
- `test_check_pattern_day_trader` - PDT check
- `test_generate_recommendations` - Improvement suggestions

#### 4. Portfolio Analytics Service Tests
**File**: `backend/tests/test_portfolio_analytics_service.py`

**Tests needed**:
- `test_get_portfolio_summary` - Summary with positions
- `test_get_equity_curve` - Historical equity data
- `test_calculate_performance_metrics` - All metrics
- `test_calculate_sharpe_ratio` - Sharpe calculation
- `test_calculate_sortino_ratio` - Sortino calculation
- `test_calculate_max_drawdown` - Drawdown tracking
- `test_get_returns_analysis` - Returns breakdown
- `test_empty_portfolio` - No positions case

### Success Criteria:

#### Automated Verification:
- [ ] All 4 test files created
- [ ] Tests pass: `cd backend && poetry run pytest tests/test_live_trading_service_unit.py tests/test_risk_manager_service.py tests/test_order_validation_service.py tests/test_portfolio_analytics_service.py -v`
- [ ] At least 7 tests per file (28+ total new tests)

#### Manual Verification:
- [ ] Mocking correctly isolates external dependencies
- [ ] Business logic edge cases covered

**Implementation Note**: Spawn 4 haiku sub-agents in parallel, one for each service test file.

---

## Phase 3: Frontend Hooks & API Client Tests

### Overview
Complete frontend coverage for hooks and API clients.

### Changes Required:

#### 1. use-execution Hook Tests
**File**: `frontend/src/lib/hooks/__tests__/use-execution.test.tsx`

```typescript
// Template based on use-strategies.test.tsx patterns
import React from 'react';
import { renderHook, waitFor, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import {
  useExecutionStatus,
  useSignals,
  usePerformance,
  useStartExecution,
  useStopExecution,
  useResetExecution,
} from '../use-execution';

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

describe('useExecutionStatus', () => {
  it('fetches execution status', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ data: { state: 'ACTIVE' } }),
    });

    const { result } = renderHook(
      () => useExecutionStatus('strategy-123'),
      { wrapper: createWrapper() }
    );

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.state).toBe('ACTIVE');
  });
});
```

**Tests needed**:
- `useExecutionStatus` - Fetches status correctly
- `useExecutionStatus` - Disabled without token
- `useSignals` - Fetches signals with polling
- `usePerformance` - Fetches performance data
- `useStartExecution` - Mutation and cache invalidation
- `useStopExecution` - Mutation and cache invalidation
- `useResetExecution` - Mutation and cache invalidation

#### 2. Optimizer API Client Tests
**File**: `frontend/src/lib/api/__tests__/optimizer.test.ts`

```typescript
// Template based on strategies.test.ts patterns
import { analyzeStrategies, getJobStatus, getOptimizationResults, executeOptimalStrategies } from '../optimizer';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

describe('optimizer API', () => {
  const token = 'test-token';

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('analyzeStrategies', () => {
    it('posts optimization request', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ job_id: 'job-123' }),
      });

      const result = await analyzeStrategies({
        symbols: ['AAPL'],
        start_date: '2024-01-01',
        end_date: '2024-03-01',
      }, token);

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/optimizer/analyze'),
        expect.objectContaining({ method: 'POST' })
      );
    });
  });
});
```

**Tests needed**:
- `analyzeStrategies` - POST with params
- `getJobStatus` - GET job status
- `getOptimizationResults` - GET results
- `executeOptimalStrategies` - POST with object params
- `executeOptimalStrategies` - POST with array params (backward compat)
- Error handling for each function

#### 3. Execution API Client Tests
**File**: `frontend/src/lib/api/__tests__/execution.test.ts`

**Tests needed**:
- `getExecutionStatus` - GET status
- `startExecution` - POST start
- `stopExecution` - POST stop
- `resetExecution` - POST reset
- `getSignals` - GET signals
- `getPerformance` - GET performance
- Error handling for 401, 404, 500

### Success Criteria:

#### Automated Verification:
- [ ] All 3 test files created
- [ ] Tests pass: `cd frontend && npm test -- --testPathPattern="use-execution|optimizer|execution" --passWithNoTests`
- [ ] At least 6 tests per file (18+ total new tests)

#### Manual Verification:
- [ ] Mock patterns consistent with existing tests
- [ ] Edge cases covered (missing token, network errors)

**Implementation Note**: Spawn 3 haiku sub-agents in parallel.

---

## Phase 4: Frontend Page Tests

### Overview
Create unit tests for the 4 highest-priority untested pages.

### Changes Required:

#### 1. Trades Page Tests
**File**: `frontend/src/app/dashboard/trades/__tests__/page.test.tsx`

```typescript
// Template based on dashboard page test patterns
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import TradesPage from '../page';

jest.mock('next/navigation', () => ({
  useRouter: () => ({ push: jest.fn() }),
}));

jest.mock('@/lib/hooks/use-trades', () => ({
  useTrades: jest.fn(),
  useTradingStatistics: jest.fn(),
}));

const queryClient = new QueryClient();

describe('TradesPage', () => {
  it('renders loading state', () => {
    const { useTrades, useTradingStatistics } = require('@/lib/hooks/use-trades');
    useTrades.mockReturnValue({ data: null, isLoading: true });
    useTradingStatistics.mockReturnValue({ data: null, isLoading: true });

    render(
      <QueryClientProvider client={queryClient}>
        <TradesPage />
      </QueryClientProvider>
    );

    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });
});
```

**Tests needed**:
- Loading state renders
- Empty state with no trades
- Trades list renders correctly
- Statistics cards display
- Status badges render correctly
- Date formatting works
- Currency formatting works

#### 2. Strategies Page Tests
**File**: `frontend/src/app/dashboard/strategies/__tests__/page.test.tsx`

**Tests needed**:
- Loading state renders
- Empty state with no strategies
- Strategy cards render
- Create button present with correct testid
- Delete confirmation dialog
- Toggle active status
- P&L calculations display

#### 3. Optimizer Page Tests
**File**: `frontend/src/app/dashboard/optimizer/__tests__/page.test.tsx`

**Tests needed**:
- Form renders with default values
- Symbol input validation
- Date range validation
- Analyze button submits
- Loading/polling state
- Results tabs render
- Execute buttons work
- Error messages display

#### 4. Portfolio Page Tests
**File**: `frontend/src/app/dashboard/portfolio/__tests__/page.test.tsx`

**Tests needed**:
- Loading state renders
- Summary cards display
- Period tabs work
- Metrics display correctly
- Currency formatting
- Percentage formatting
- Empty metrics handling

### Success Criteria:

#### Automated Verification:
- [ ] All 4 test files created in correct `__tests__` directories
- [ ] Tests pass: `cd frontend && npm test -- --testPathPattern="trades/|strategies/|optimizer/|portfolio/" --passWithNoTests`
- [ ] At least 5 tests per file (20+ total new tests)

#### Manual Verification:
- [ ] All page states tested (loading, empty, data, error)
- [ ] User interactions tested where applicable

**Implementation Note**: Spawn 4 haiku sub-agents in parallel.

---

## Phase 5: Add Missing data-testid Attributes

### Overview
Add data-testid attributes to components needed for E2E testing.

### Changes Required:

#### 1. Portfolio Page
**File**: `frontend/src/app/dashboard/portfolio/page.tsx`

Add:
- `data-testid="portfolio-summary"` to summary container
- `data-testid="period-selector"` to period tabs
- `data-testid="equity-value"` to equity display

#### 2. Optimizer Page
**File**: `frontend/src/app/dashboard/optimizer/page.tsx`

Add:
- `data-testid="optimizer-form"` to form container
- `data-testid="analyze-button"` to analyze button
- `data-testid="optimizer-results"` to results container
- `data-testid="execute-button"` to execute buttons

#### 3. Notifications Page
**File**: `frontend/src/app/dashboard/notifications/page.tsx`

Add:
- `data-testid="notifications-list"` to list container
- `data-testid="mark-all-read-button"` to mark all button
- `data-testid="notification-item"` to each notification

#### 4. Watchlist Page
**File**: `frontend/src/app/dashboard/watchlist/page.tsx`

Add:
- `data-testid="watchlist-card"` to watchlist cards
- `data-testid="add-symbol-button"` to add button
- `data-testid="symbol-input"` to symbol input

### Success Criteria:

#### Automated Verification:
- [ ] TypeScript compiles: `cd frontend && npm run type-check`
- [ ] Build succeeds: `cd frontend && npm run build`
- [ ] Existing tests still pass: `cd frontend && npm test`

#### Manual Verification:
- [ ] data-testid attributes visible in browser dev tools
- [ ] No visual regressions

**Implementation Note**: Can be done sequentially or spawn 4 haiku agents for parallel edits.

---

## Testing Strategy

### Unit Tests:
- Mock external dependencies (Alpaca API, database)
- Test business logic in isolation
- Cover happy path and error cases
- Aim for 80%+ code coverage per file

### Integration Tests (existing):
- Keep existing E2E tests working
- Backend integration tests for database operations
- Frontend integration via React Query

### Test Data:
- Use existing fixtures where available
- Create new fixtures matching existing patterns
- Use realistic but deterministic data

## Test Commands Quick Reference

```bash
# Backend - run specific test files
cd backend
poetry run pytest tests/test_orders_api.py -v
poetry run pytest tests/test_risk_manager_service.py -v
poetry run pytest -k "test_place_order" -v  # pattern match

# Frontend - run specific test files
cd frontend
npm test -- --testPathPattern="use-execution"
npm test -- --testPathPattern="optimizer"
npm test -- --coverage

# All tests
cd backend && poetry run pytest
cd frontend && npm test
```

## References

- Original testing plan: `TESTING_PLAN.md`
- Backend test patterns: `backend/tests/test_paper_trading_service.py`, `backend/tests/test_auth.py`
- Frontend test patterns: `frontend/src/lib/hooks/__tests__/use-strategies.test.tsx`
- Fixtures: `backend/tests/conftest.py`, `frontend/src/lib/__tests__/fixtures.ts`
