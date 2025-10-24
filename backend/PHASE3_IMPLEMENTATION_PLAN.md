# Phase 3: Market Data & Order Execution - Implementation Plan

## Overview
Build on Phase 2 foundation to add complete market data fetching and order execution capabilities, including database persistence and enhanced security.

## Objectives
1. Implement historical market data fetching (bars, quotes, trades)
2. Implement full order execution functionality (place, cancel, modify)
3. Add database models for order history persistence
4. Implement WebSocket authentication for streaming
5. Add order validation and risk checks
6. Create comprehensive integration tests

## Phase 3A: Market Data Implementation

### 1. Historical Market Data Service
**File**: `backend/app/integrations/market_data.py` (expand stub)

**Features to Implement**:
- `get_latest_quote(symbol)` - Latest bid/ask
- `get_latest_trade(symbol)` - Latest trade price
- `get_bars(symbol, timeframe, start, end, limit)` - OHLCV data
- `get_snapshot(symbol)` - Complete market snapshot
- `get_multi_quotes(symbols)` - Batch quote fetching
- `get_multi_trades(symbols)` - Batch trade fetching

**Caching Strategy**:
- Latest quotes: 1-second TTL
- Latest trades: 1-second TTL
- Historical bars: 5-minute TTL
- Snapshots: 2-second TTL

**API Endpoints to Add**:
- `GET /api/v1/broker/market/quote/{symbol}` - Single quote
- `GET /api/v1/broker/market/quotes` - Multiple quotes (query param: symbols)
- `GET /api/v1/broker/market/trade/{symbol}` - Latest trade
- `GET /api/v1/broker/market/bars/{symbol}` - Historical bars
- `GET /api/v1/broker/market/snapshot/{symbol}` - Market snapshot

### 2. Market Data Response Schemas
**File**: `backend/app/schemas/market_data.py` (new)

**Schemas**:
- `QuoteResponse` - Bid/ask with sizes
- `TradeResponse` - Price, size, timestamp
- `BarResponse` - OHLCV data
- `SnapshotResponse` - Complete market view
- `MultiQuoteResponse` - Batch quotes

## Phase 3B: Order Execution Implementation

### 1. Order Execution Service
**File**: `backend/app/integrations/order_execution.py` (expand stub)

**Methods to Implement**:
- `place_order(symbol, qty, side, order_type, ...)` - Place new order
- `cancel_order(order_id)` - Cancel pending order
- `replace_order(order_id, qty, limit_price, ...)` - Modify order
- `cancel_all_orders()` - Cancel all open orders
- `close_position(symbol)` - Close position at market
- `close_all_positions()` - Close all positions

**Validation**:
- Check buying power before market orders
- Validate limit/stop prices
- Check market hours for non-extended-hours orders
- Validate order quantities (fractional shares support)
- Check position existence before closing

**Error Handling**:
- Insufficient buying power
- Invalid order parameters
- Market closed (if not extended hours)
- Symbol not tradable
- Position not found

### 2. Order API Endpoints
**File**: `backend/app/api/v1/orders.py` (new)

**Endpoints**:
- `POST /api/v1/orders` - Place new order
- `DELETE /api/v1/orders/{order_id}` - Cancel order
- `PATCH /api/v1/orders/{order_id}` - Modify order
- `DELETE /api/v1/orders` - Cancel all orders
- `POST /api/v1/positions/{symbol}/close` - Close position
- `DELETE /api/v1/positions` - Close all positions

### 3. Order Request/Response Schemas
**File**: `backend/app/schemas/order.py` (new)

**Schemas**:
- `OrderRequest` - Place order payload
- `OrderUpdateRequest` - Modify order payload
- `OrderResponse` - Order details response
- `OrderListResponse` - Multiple orders
- `PositionCloseRequest` - Close position params

## Phase 3C: Database Persistence

### 1. Order History Model
**File**: `backend/app/models/order.py` (new)

**Fields**:
- id (UUID, primary key)
- user_id (foreign key to users)
- alpaca_order_id (string, indexed)
- symbol (string, indexed)
- side (enum: buy/sell)
- order_type (enum: market/limit/stop/stop_limit)
- qty (decimal)
- filled_qty (decimal)
- limit_price (decimal, nullable)
- stop_price (decimal, nullable)
- status (enum: new/filled/partially_filled/canceled/expired/rejected)
- submitted_at (timestamp)
- filled_at (timestamp, nullable)
- canceled_at (timestamp, nullable)
- filled_avg_price (decimal, nullable)
- time_in_force (string)
- extended_hours (boolean)
- created_at (timestamp)
- updated_at (timestamp)

**Indexes**:
- user_id, created_at
- alpaca_order_id (unique)
- symbol, created_at
- status, created_at

### 2. Position History Model
**File**: `backend/app/models/position.py` (new)

**Fields**:
- id (UUID, primary key)
- user_id (foreign key)
- symbol (string, indexed)
- qty (decimal)
- side (enum: long/short)
- avg_entry_price (decimal)
- market_value (decimal)
- cost_basis (decimal)
- unrealized_pl (decimal)
- unrealized_plpc (decimal)
- current_price (decimal)
- snapshot_at (timestamp)

**Purpose**: Track position snapshots for analytics

### 3. Database Migration
**File**: `backend/migrations/versions/002_order_tracking.py` (new)

Create tables for order and position history with proper indexes.

### 4. Order Sync Service
**File**: `backend/app/services/order_sync.py` (new)

**Features**:
- Sync orders from Alpaca to database on fetch
- Background task to sync open orders periodically
- Webhook handler for order updates (future)
- Conflict resolution (Alpaca as source of truth)

## Phase 3D: WebSocket Authentication

### 1. JWT Token Authentication for WebSocket
**File**: `backend/app/api/v1/broker.py` (update)

**Implementation**:
- Accept JWT token in query parameter or initial message
- Validate token before accepting connection
- Track user_id with WebSocket connection
- Implement per-user subscription limits

**Changes**:
```python
@router.websocket("/stream")
async def market_data_stream(
    websocket: WebSocket,
    token: str = Query(..., description="JWT authentication token"),
    symbols: str = Query(...),
    streams: str = Query("trades,quotes"),
):
    # Verify token first
    user = await verify_websocket_token(token)
    if not user:
        await websocket.close(code=1008, reason="Authentication failed")
        return
    
    # Continue with authenticated connection...
```

### 2. Token Verification Helper
**File**: `backend/app/core/security.py` (update)

Add function:
```python
async def verify_websocket_token(token: str) -> Optional[User]:
    """Verify JWT token for WebSocket authentication."""
```

## Phase 3E: Advanced Features

### 1. Bracket Orders
**File**: `backend/app/services/bracket_orders.py` (new)

**Features**:
- Place entry order with take-profit and stop-loss
- Automatic OCO (One-Cancels-Other) setup
- Track bracket order lifecycle
- Handle partial fills

### 2. Order Validation Service
**File**: `backend/app/services/order_validation.py` (new)

**Validations**:
- Buying power check
- Position size limits
- Price reasonability (no fat-finger trades)
- Symbol tradability check
- Market hours validation
- Day trading rules (pattern day trader)

### 3. Risk Management Rules
**File**: `backend/app/services/risk_manager.py` (new)

**Rules**:
- Maximum position size per symbol
- Maximum portfolio allocation per symbol
- Daily loss limits
- Maximum number of open positions
- Sector concentration limits

## Phase 3F: Testing

### 1. Unit Tests
**File**: `backend/tests/test_market_data.py` (new)

**Test Coverage**:
- Market data fetching with mocked responses
- Caching behavior
- Error handling
- Rate limiting

**File**: `backend/tests/test_order_execution.py` (new)

**Test Coverage**:
- Order placement with validation
- Order modification and cancellation
- Position closing
- Error scenarios
- Database persistence

### 2. Integration Tests
**File**: `backend/tests/integration/test_trading_workflow.py` (new)

**Scenarios**:
- Complete trading workflow (place → fill → close)
- WebSocket authentication and streaming
- Bracket order execution
- Risk limit enforcement
- Order sync with database

### 3. Load Tests
**File**: `backend/tests/load/test_api_performance.py` (new)

**Tests**:
- Concurrent order placement
- WebSocket connection scalability
- Cache performance under load
- Database query performance

## Implementation Order

### Week 1: Market Data & Database
1. Implement historical market data service
2. Add market data API endpoints
3. Create database models and migrations
4. Implement order sync service
5. Unit tests for market data

### Week 2: Order Execution
1. Implement order execution service
2. Add order validation logic
3. Create order API endpoints
4. Implement WebSocket authentication
5. Unit tests for order execution

### Week 3: Advanced Features & Testing
1. Implement bracket orders
2. Add risk management rules
3. Complete integration tests
4. Load testing and optimization
5. Documentation and deployment guide

## Technical Requirements

### Dependencies to Add
```toml
# Already have alpaca-py and tenacity
# No additional dependencies needed
```

### Database Schema Updates
```sql
-- Add new tables in migration
CREATE TABLE orders (...);
CREATE TABLE position_snapshots (...);
CREATE INDEX idx_orders_user_created ON orders(user_id, created_at);
```

### Environment Variables
```bash
# Order Limits (optional, defaults in code)
MAX_POSITION_SIZE=10000
MAX_DAILY_TRADES=50
MAX_OPEN_POSITIONS=20
ENABLE_EXTENDED_HOURS=true
```

## Success Criteria

### Functionality
- ✅ Can fetch real-time and historical market data
- ✅ Can place, modify, and cancel orders
- ✅ Orders persist in database
- ✅ WebSocket requires authentication
- ✅ Risk limits are enforced
- ✅ Bracket orders work correctly

### Performance
- Market data API: < 200ms response time
- Order placement: < 500ms response time
- WebSocket latency: < 100ms
- Database writes: < 50ms

### Testing
- Unit test coverage: > 85%
- Integration tests: All critical paths covered
- Load tests: Handle 100 concurrent users

### Security
- All endpoints require authentication
- WebSocket connections are authenticated
- Order validation prevents abuse
- Sensitive data is not logged

## Risk Mitigation

### Known Risks
1. **API Rate Limits**: Alpaca has strict limits
   - **Mitigation**: Aggressive caching, batch requests
   
2. **Order Execution Failures**: Network issues, invalid orders
   - **Mitigation**: Retry logic, comprehensive validation
   
3. **Database Performance**: High write volume
   - **Mitigation**: Batch inserts, async processing
   
4. **WebSocket Scalability**: Many concurrent connections
   - **Mitigation**: Connection pooling, load balancing

## Deliverables

### Code
- 8 new/updated Python files
- 1 database migration
- 3 test suites
- Updated API documentation

### Documentation
- Phase 3 implementation summary
- API endpoint documentation
- Database schema documentation
- Deployment guide updates

### Testing
- Unit tests for all new components
- Integration tests for critical workflows
- Load test results and optimization notes

## Timeline

**Estimated Duration**: 10-12 working days

- Market Data Implementation: 2-3 days
- Order Execution: 3-4 days
- Database & Sync: 2 days
- Advanced Features: 2-3 days
- Testing & Documentation: 2 days

## Questions for Approval

1. **Order Persistence**: Should we sync ALL orders or only successful ones?
2. **Risk Limits**: What default limits should we enforce?
3. **Extended Hours**: Enable by default or require explicit flag?
4. **Bracket Orders**: Include in Phase 3 or defer to Phase 4?
5. **Testing**: Do you want load testing or focus on functional tests?

---

**Ready to proceed?** Please review and approve this plan, or suggest modifications.