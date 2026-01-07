# Comprehensive Testing Plan

## Executive Summary

This document outlines a complete testing strategy for the algo-trading-app. Current coverage analysis reveals:

| Layer | Current Coverage | Target Coverage |
|-------|------------------|-----------------|
| Frontend Unit Tests | 26% pages, 83% hooks, 75% API clients | 90%+ |
| Backend Unit Tests | 100% models, 23% routes, 26% services | 85%+ |
| E2E Tests | 65% critical flows | 95%+ |

---

## Phase 1: Critical Path Testing (Priority: HIGH)

### 1.1 Backend Route Tests

These endpoints handle money and orders - highest priority.

#### Orders API (`/api/v1/orders.py`) - 7 endpoints
```
File: backend/tests/test_orders_api.py
Tests needed:
- [ ] POST /orders - Place market/limit order
- [ ] POST /orders/bracket - Place bracket order with stop-loss/take-profit
- [ ] DELETE /orders/{id} - Cancel specific order
- [ ] PUT /orders/{id} - Modify pending order
- [ ] DELETE /orders - Cancel all orders
- [ ] POST /positions/{symbol}/close - Close specific position
- [ ] POST /positions/close-all - Close all positions
```

#### Broker API (`/api/v1/broker.py`) - 9 endpoints
```
File: backend/tests/test_broker_api.py
Tests needed:
- [ ] GET /broker/account - Get account balance and status
- [ ] GET /broker/positions - Get current positions
- [ ] GET /broker/orders - Get active orders
- [ ] DELETE /broker/cache - Clear market data cache
- [ ] GET /broker/quotes - Get real-time quotes
- [ ] GET /broker/trades - Get executed trades
- [ ] GET /broker/bars - Get historical price bars
- [ ] GET /broker/snapshot - Get market snapshot
- [ ] WebSocket /broker/stream - Market data streaming
```

#### Strategy Execution API (`/api/v1/strategy_execution.py`) - 7 endpoints
```
File: backend/tests/test_strategy_execution_api.py
Tests needed:
- [ ] POST /strategies/{id}/execution/start - Start strategy
- [ ] POST /strategies/{id}/execution/stop - Stop strategy
- [ ] GET /strategies/{id}/execution/status - Get execution status
- [ ] GET /strategies/{id}/signals - Get strategy signals
- [ ] GET /strategies/{id}/performance - Get performance metrics
- [ ] POST /strategies/{id}/test - Test strategy in sandbox
- [ ] POST /strategies/{id}/reset - Reset strategy state
```

#### Risk Rules API (`/api/v1/risk_rules.py`) - 7 endpoints
```
File: backend/tests/test_risk_rules_api.py
Tests needed:
- [ ] POST /risk-rules - Create risk rule
- [ ] GET /risk-rules - List all rules
- [ ] GET /risk-rules/portfolio - Get portfolio risk metrics
- [ ] GET /risk-rules/{id} - Get specific rule
- [ ] PUT /risk-rules/{id} - Update rule
- [ ] DELETE /risk-rules/{id} - Delete rule
- [ ] POST /risk-rules/{id}/test - Test rule against portfolio
```

### 1.2 Backend Service Tests

Critical business logic services.

#### Live Trading Service (`live_trading_service.py`)
```
File: backend/tests/test_live_trading_service.py
Tests needed:
- [ ] start_live_strategy() - Start live trading
- [ ] stop_live_strategy() - Stop gracefully
- [ ] update_strategy_position() - Position tracking
- [ ] process_signal() - Signal to order conversion
- [ ] handle_order_fill() - Fill processing
- [ ] handle_error() - Error recovery
```

#### Risk Manager Service (`risk_manager.py`)
```
File: backend/tests/test_risk_manager_service.py
Tests needed:
- [ ] evaluate_rules() - Check all rules
- [ ] calculate_position_size() - Position sizing
- [ ] check_max_drawdown() - Drawdown limits
- [ ] check_daily_loss_limit() - Daily P&L limits
- [ ] check_position_concentration() - Concentration risk
- [ ] block_trade() - Trade blocking logic
```

#### Order Validation Service (`order_validation.py`)
```
File: backend/tests/test_order_validation_service.py
Tests needed:
- [ ] validate_order() - Full order validation
- [ ] check_buying_power() - Capital availability
- [ ] check_symbol_tradeable() - Symbol validation
- [ ] check_market_hours() - Trading hours
- [ ] validate_quantity() - Quantity limits
```

#### Portfolio Analytics Service (`portfolio_analytics.py`)
```
File: backend/tests/test_portfolio_analytics_service.py
Tests needed:
- [ ] calculate_portfolio_summary() - Portfolio metrics
- [ ] calculate_returns() - Return calculations
- [ ] calculate_sharpe_ratio() - Risk-adjusted returns
- [ ] calculate_max_drawdown() - Drawdown analysis
- [ ] generate_equity_curve() - Equity data
```

---

## Phase 2: Frontend Unit Tests (Priority: HIGH)

### 2.1 Untested Pages (14 pages)

Each page needs rendering, interaction, and error state tests.

#### Dashboard Pages
```
File: frontend/src/app/dashboard/trades/__tests__/page.test.tsx
- [ ] Trades list renders
- [ ] Filter by date works
- [ ] Pagination works
- [ ] Empty state displays
- [ ] Loading state displays
- [ ] Error state displays

File: frontend/src/app/dashboard/strategies/__tests__/page.test.tsx
- [ ] Strategies grid renders
- [ ] Create button navigates
- [ ] Strategy cards display correctly
- [ ] Delete confirmation works

File: frontend/src/app/dashboard/optimizer/__tests__/page.test.tsx
- [ ] Optimizer form renders
- [ ] Symbol selection works
- [ ] Date range picker works
- [ ] Analyze button submits
- [ ] Results table displays
- [ ] Execute actions work

File: frontend/src/app/dashboard/live-trading/new/__tests__/page.test.tsx
- [ ] Form renders all fields
- [ ] Validation messages display
- [ ] Submit creates session
- [ ] Cancel navigates back

File: frontend/src/app/dashboard/strategies/[id]/execution/__tests__/page.test.tsx
- [ ] Execution status displays
- [ ] Start/stop buttons work
- [ ] Performance metrics display
- [ ] Signals list renders

File: frontend/src/app/dashboard/strategies/new/__tests__/page.test.tsx
- [ ] Form renders all fields
- [ ] Ticker selection works
- [ ] Parameter configuration works
- [ ] Validation messages display
- [ ] Submit creates strategy

File: frontend/src/app/dashboard/watchlist/__tests__/page.test.tsx
- [ ] Watchlists display
- [ ] Add symbol works
- [ ] Remove symbol works
- [ ] Create watchlist works
- [ ] Delete watchlist works

File: frontend/src/app/dashboard/live-trading/__tests__/page.test.tsx
- [ ] Sessions list renders
- [ ] Status indicators work
- [ ] Filter controls work

File: frontend/src/app/dashboard/notifications/__tests__/page.test.tsx
- [ ] Notifications list renders
- [ ] Mark read works
- [ ] Delete notification works
- [ ] Filter by status works
- [ ] Empty state displays

File: frontend/src/app/dashboard/portfolio/__tests__/page.test.tsx
- [ ] Summary cards render
- [ ] Period selector works
- [ ] Metrics calculate correctly
- [ ] Charts render

File: frontend/src/app/dashboard/risk-rules/__tests__/page.test.tsx
- [ ] Rules list renders
- [ ] Create rule form works
- [ ] Edit rule works
- [ ] Delete rule confirms

File: frontend/src/app/dashboard/backtests/[id]/__tests__/page.test.tsx
- [ ] Results load correctly
- [ ] Metrics display
- [ ] Trades table renders
- [ ] Charts render

File: frontend/src/app/dashboard/backtests/new/__tests__/page.test.tsx
- [ ] Form renders
- [ ] Strategy selection works
- [ ] Date range picker works
- [ ] Submit creates backtest

File: frontend/src/app/dashboard/backtests/__tests__/page.test.tsx
- [ ] Backtests list renders
- [ ] Status indicators work
- [ ] Delete confirmation works
```

### 2.2 Untested Hooks (1 hook)

```
File: frontend/src/lib/hooks/__tests__/use-execution.test.tsx
Tests needed:
- [ ] useExecutionStatus() - Fetches status correctly
- [ ] useSignals() - Fetches signals with polling
- [ ] usePerformance() - Fetches performance data
- [ ] useStartExecution() - Mutation works
- [ ] useStopExecution() - Mutation works
- [ ] useResetExecution() - Mutation and cache invalidation
```

### 2.3 Untested API Clients (2 clients)

```
File: frontend/src/lib/api/__tests__/optimizer.test.ts
Tests needed:
- [ ] analyzeStrategies() - POST request with params
- [ ] getJobStatus() - Polling endpoint
- [ ] getOptimizationResults() - Results fetching
- [ ] executeOptimalStrategies() - Execution request

File: frontend/src/lib/api/__tests__/execution.test.ts
Tests needed:
- [ ] getExecutionStatus() - GET status
- [ ] startExecution() - POST start
- [ ] stopExecution() - POST stop
- [ ] resetExecution() - POST reset
- [ ] getSignals() - GET signals with pagination
- [ ] getPerformance() - GET performance metrics
```

### 2.4 Layout Component Tests (Optional - shadcn components are pre-tested)

```
File: frontend/src/components/layout/__tests__/header.test.tsx
- [ ] Logo renders
- [ ] Navigation links work
- [ ] User menu displays when authenticated
- [ ] Logout button works

File: frontend/src/components/layout/__tests__/sidebar.test.tsx
- [ ] All nav items render
- [ ] Active state highlights
- [ ] Navigation works
- [ ] Collapse/expand works (if applicable)
```

---

## Phase 3: E2E Test Expansion (Priority: MEDIUM)

### 3.1 New E2E Test Files

#### Portfolio Analytics E2E
```
File: frontend/e2e/portfolio.spec.ts
Tests needed:
- [ ] Load portfolio page
- [ ] Verify summary cards (equity, cash, P&L)
- [ ] Switch time periods (daily, weekly, monthly)
- [ ] Verify equity curve renders
- [ ] Test refresh functionality
```

#### Strategy Optimizer E2E
```
File: frontend/e2e/optimizer.spec.ts
Tests needed:
- [ ] Navigate to optimizer
- [ ] Configure optimization (symbols, dates, strategies)
- [ ] Start optimization job
- [ ] Poll for completion
- [ ] View results table
- [ ] Execute single strategy
- [ ] Execute all strategies
- [ ] Handle risk rule blocks
```

#### Strategy Execution E2E
```
File: frontend/e2e/strategy-execution.spec.ts
Tests needed:
- [ ] Navigate to execution page
- [ ] View execution status
- [ ] Start strategy execution
- [ ] Monitor live signals
- [ ] Stop execution
- [ ] View execution history
```

#### Watchlist Management E2E
```
File: frontend/e2e/watchlist.spec.ts
Tests needed:
- [ ] Create watchlist
- [ ] Add symbols
- [ ] View price updates
- [ ] Remove symbols
- [ ] Delete watchlist
```

#### Notifications E2E
```
File: frontend/e2e/notifications.spec.ts
Tests needed:
- [ ] View notifications
- [ ] Filter by status
- [ ] Mark as read
- [ ] Mark all as read
- [ ] Delete notification
```

#### Backtest Details E2E
```
File: frontend/e2e/backtest-details.spec.ts
Tests needed:
- [ ] Navigate to backtest results
- [ ] View summary metrics
- [ ] View equity curve
- [ ] View trades list
- [ ] Export results
```

### 3.2 Test Utility Enhancements

Add to `frontend/e2e/test-utils.ts`:

```typescript
// New Selectors
export const selectors = {
  // ... existing selectors ...

  // Portfolio
  portfolioSummary: '[data-testid="portfolio-summary"]',
  equityCurve: '[data-testid="equity-curve"]',
  periodSelector: '[data-testid="period-selector"]',

  // Watchlist
  watchlistCard: '[data-testid="watchlist-card"]',
  addSymbolButton: '[data-testid="add-symbol-button"]',
  symbolInput: '[data-testid="symbol-input"]',

  // Notifications
  notificationsList: '[data-testid="notifications-list"]',
  markAllReadButton: '[data-testid="mark-all-read-button"]',
  notificationItem: '[data-testid="notification-item"]',

  // Optimizer
  optimizerForm: '[data-testid="optimizer-form"]',
  analyzeButton: '[data-testid="analyze-button"]',
  resultsTable: '[data-testid="optimizer-results"]',
  executeButton: '[data-testid="execute-button"]',

  // Execution
  executionStatus: '[data-testid="execution-status"]',
  startExecutionButton: '[data-testid="start-execution"]',
  stopExecutionButton: '[data-testid="stop-execution"]',
  signalsList: '[data-testid="signals-list"]',
};
```

### 3.3 Missing data-testid Attributes

Add these test IDs to components:

| Page | Component | testid |
|------|-----------|--------|
| portfolio/page.tsx | Summary container | `portfolio-summary` |
| portfolio/page.tsx | Period tabs | `period-selector` |
| watchlist/page.tsx | Watchlist card | `watchlist-card` |
| watchlist/page.tsx | Add button | `add-symbol-button` |
| notifications/page.tsx | List container | `notifications-list` |
| notifications/page.tsx | Mark all read | `mark-all-read-button` |
| optimizer/page.tsx | Form container | `optimizer-form` |
| optimizer/page.tsx | Analyze button | `analyze-button` |
| optimizer/page.tsx | Results table | `optimizer-results` |
| strategies/[id]/execution | Status container | `execution-status` |
| strategies/[id]/execution | Start button | `start-execution` |
| strategies/[id]/execution | Stop button | `stop-execution` |

---

## Phase 4: Backend Additional Tests (Priority: MEDIUM)

### 4.1 Remaining Route Tests

```
File: backend/tests/test_paper_trading_api.py
- [ ] GET /paper/account
- [ ] POST /paper/orders
- [ ] GET /paper/orders
- [ ] GET /paper/positions
- [ ] GET /paper/trades
- [ ] POST /paper/reset

File: backend/tests/test_optimizer_api.py
- [ ] POST /optimizer/analyze
- [ ] GET /optimizer/status/{job_id}
- [ ] GET /optimizer/results/{job_id}
- [ ] POST /optimizer/execute
- [ ] GET /optimizer/history
- [ ] DELETE /optimizer/results/{job_id}

File: backend/tests/test_notifications_api.py
- [ ] GET /notifications
- [ ] POST /notifications
- [ ] PUT /notifications/{id}/read
- [ ] PUT /notifications/read-all
- [ ] DELETE /notifications/{id}
- [ ] GET /notifications/preferences
- [ ] PUT /notifications/preferences

File: backend/tests/test_api_keys_api.py
- [ ] POST /api-keys
- [ ] GET /api-keys
- [ ] GET /api-keys/{id}
- [ ] PUT /api-keys/{id}
- [ ] DELETE /api-keys/{id}
- [ ] POST /api-keys/{id}/rotate
- [ ] POST /api-keys/verify

File: backend/tests/test_watchlist_api.py
- [ ] GET /watchlists
- [ ] POST /watchlists
- [ ] GET /watchlists/{id}
- [ ] PUT /watchlists/{id}
- [ ] DELETE /watchlists/{id}
- [ ] POST /watchlists/{id}/symbols
- [ ] DELETE /watchlists/{id}/symbols/{symbol}
- [ ] GET /price-alerts
- [ ] POST /price-alerts

File: backend/tests/test_portfolio_api.py
- [ ] GET /portfolio/summary
- [ ] GET /portfolio/equity-curve
- [ ] GET /portfolio/metrics
- [ ] GET /portfolio/returns

File: backend/tests/test_trades_api.py
- [ ] GET /trades
- [ ] POST /trades
- [ ] GET /trades/{id}
- [ ] GET /trades/positions
- [ ] GET /trades/statistics

File: backend/tests/test_users_api.py
- [ ] GET /users/me
- [ ] PUT /users/me
- [ ] PUT /users/me/password
- [ ] DELETE /users/me
```

### 4.2 Remaining Service Tests

```
File: backend/tests/test_strategy_optimizer_service.py
- [ ] optimize_strategy()
- [ ] grid_search()
- [ ] rank_results()
- [ ] save_results()

File: backend/tests/test_strategy_scheduler_service.py
- [ ] schedule_strategy()
- [ ] unschedule_strategy()
- [ ] get_scheduled_strategies()
- [ ] execute_scheduled()

File: backend/tests/test_signal_executor_service.py
- [ ] execute_signal()
- [ ] validate_signal()
- [ ] convert_to_order()
- [ ] handle_execution_error()

File: backend/tests/test_notification_service.py
- [ ] send_notification()
- [ ] get_user_preferences()
- [ ] format_notification()

File: backend/tests/test_order_sync_service.py
- [ ] sync_orders()
- [ ] reconcile_positions()
- [ ] handle_fill()

File: backend/tests/test_trade_audit_service.py
- [ ] log_trade()
- [ ] get_audit_trail()
- [ ] generate_report()
```

---

## Phase 5: Security & Edge Case Tests (Priority: LOW)

### 5.1 Security Tests

```
File: backend/tests/test_security.py
- [ ] JWT token expiration
- [ ] Token refresh edge cases
- [ ] Invalid token handling
- [ ] Password hashing verification
- [ ] Rate limiting
- [ ] SQL injection prevention
- [ ] XSS prevention in inputs

File: backend/tests/test_authorization.py
- [ ] User can only access own resources
- [ ] Admin privileges work correctly
- [ ] API key scoping
- [ ] Session invalidation
```

### 5.2 Error Handling Tests

```
File: backend/tests/test_error_handling.py
- [ ] Database connection failures
- [ ] External API timeouts
- [ ] Invalid input handling
- [ ] Rate limit exceeded
- [ ] Service unavailable handling
```

### 5.3 Core Utility Tests

```
File: backend/tests/test_core_security.py
- [ ] create_access_token()
- [ ] verify_token()
- [ ] get_password_hash()
- [ ] verify_password()

File: backend/tests/test_core_config.py
- [ ] Environment variable loading
- [ ] Default value handling
- [ ] Validation of required configs
```

---

## Implementation Order

### Sprint 1: Critical Backend Tests (Week 1-2)
1. Orders API tests
2. Broker API tests
3. Risk Rules API tests
4. Live Trading Service tests
5. Risk Manager Service tests
6. Order Validation Service tests

### Sprint 2: Frontend Page Tests (Week 2-3)
1. Trades page tests
2. Strategies page tests
3. Optimizer page tests
4. Portfolio page tests
5. use-execution hook tests
6. Optimizer API client tests
7. Execution API client tests

### Sprint 3: E2E Expansion (Week 3-4)
1. Add missing data-testid attributes
2. Portfolio E2E tests
3. Optimizer E2E tests
4. Strategy Execution E2E tests
5. Watchlist E2E tests
6. Notifications E2E tests

### Sprint 4: Remaining Backend Tests (Week 4-5)
1. Paper Trading API tests
2. Notifications API tests
3. Watchlist API tests
4. Portfolio API tests
5. Remaining service tests

### Sprint 5: Polish & Security (Week 5-6)
1. Security tests
2. Error handling tests
3. Core utility tests
4. Documentation updates
5. CI/CD integration

---

## Test Commands Quick Reference

```bash
# Backend
cd backend
poetry run pytest                                    # All tests
poetry run pytest tests/test_orders_api.py           # Single file
poetry run pytest -k "test_place_order"              # Pattern match
poetry run pytest --cov=app --cov-report=html        # Coverage report
poetry run pytest -m integration                     # Integration only

# Frontend Unit Tests
cd frontend
npm test                                             # All tests
npm test -- --testPathPattern="optimizer"            # Pattern match
npm test -- --coverage                               # Coverage report

# Frontend E2E Tests
cd frontend
npm run test:e2e                                     # All E2E tests
npm run test:e2e -- --grep "portfolio"               # Pattern match
npm run test:e2e:ui                                  # Interactive UI
npx playwright test e2e/portfolio.spec.ts            # Single file
```

---

## Coverage Targets

| Category | Current | Target | Tests Needed |
|----------|---------|--------|--------------|
| Backend Routes | 23% | 90% | ~80 tests |
| Backend Services | 26% | 85% | ~50 tests |
| Frontend Pages | 26% | 90% | ~70 tests |
| Frontend Hooks | 83% | 100% | ~10 tests |
| Frontend API Clients | 75% | 100% | ~15 tests |
| E2E Critical Flows | 65% | 95% | ~6 test files |

**Total Estimated Tests to Add: ~225+ test cases**

---

## Notes

1. **Prioritize by risk**: Order handling and risk management are highest priority
2. **Use existing patterns**: Follow test patterns already in codebase
3. **Mock external services**: Alpaca API, email services, etc.
4. **Test both happy path and error cases**: ~30% of tests should be error/edge cases
5. **Keep tests fast**: Unit tests should complete in < 100ms each
6. **E2E tests need backend**: Ensure Docker services are running for E2E
