---
date: 2024-12-24T20:15:00-08:00
researcher: claude
git_commit: ff63e54a990737296b34d5dd612260c16bb38256
branch: main
repository: algo-trading-app
topic: "Implementation Research: Frontend /lib/, Database Migrations, Settings, WebSocket, Charts"
tags: [research, codebase, frontend, backend, migrations, websocket, recharts, zustand]
status: complete
last_updated: 2024-12-24
---

# Research: Implementation Requirements for Missing Features

**Date**: 2024-12-24T20:15:00-08:00
**Git Commit**: ff63e54a990737296b34d5dd612260c16bb38256
**Branch**: main
**Repository**: algo-trading-app

## Research Question

How to implement: Frontend /lib/ files, Create missing database migrations, Enable settings page features, Add WebSocket real-time updates, Integrate charts with recharts

## Summary

This research covers five implementation areas:

1. **Frontend /lib/** - 10+ missing files imported but not existing; 2 files exist as templates
2. **Database Migrations** - 4 models without migrations, 1 duplicate migration conflict
3. **Settings Page** - All sections disabled; backend APIs fully ready
4. **WebSocket** - Backend fully implemented; frontend has no WebSocket code
5. **Charts** - recharts installed but unused; placeholder exists in portfolio page

---

## Detailed Findings

### 1. Frontend /lib/ Directory

#### Existing Files (2)
| File | Exports |
|------|---------|
| `/lib/api/execution.ts` | `getExecutionStatus()`, `startExecution()`, `stopExecution()` |
| `/lib/hooks/use-execution.ts` | `useExecutionStatus()`, `useStartExecution()`, `useStopExecution()` |

#### Missing Files (10+)

| File | Expected Exports | Referenced By |
|------|-----------------|---------------|
| `/lib/utils.ts` | `cn()` - className utility | 16 UI components |
| `/lib/stores/auth-store.ts` | `useAuthStore`, `AuthState` | 6 files |
| `/lib/api/query-client.ts` | `queryClient` | `providers.tsx` |
| `/lib/hooks/use-broker.ts` | `useAccount`, `usePositions`, `useBrokerOrders` | `dashboard/page.tsx` |
| `/lib/hooks/use-strategies.ts` | `useStrategies`, `useCreateStrategy`, `useUpdateStrategy`, `useDeleteStrategy` | 4 files |
| `/lib/hooks/use-trades.ts` | `useTrades`, `useTradingStatistics`, `useCurrentPositions` | 2 files |
| `/lib/hooks/use-backtests.ts` | `useBacktests`, `useBacktest`, `useCreateBacktest`, `useDeleteBacktest` | 3 files |
| `/lib/api/live-trading.ts` | `LiveTradingAPI` class | 2 files |
| `/lib/api/optimizer.ts` | `analyzeStrategies`, `getJobStatus`, `getOptimizationResults`, `executeOptimalStrategies` | 1 file |
| `/lib/api/strategies.ts` | `strategiesApi.list()` | 1 file |

#### Missing Exports in Existing File
`/lib/hooks/use-execution.ts` missing: `useSignals()`, `usePerformance()`, `useResetExecution()`

#### Code Patterns

**API Client Pattern:**
```typescript
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function fetchData(params, token: string) {
  const response = await fetch(`${API_URL}/api/v1/endpoint`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) throw new Error('Failed');
  return response.json();
}
```

**React Query Hook Pattern:**
```typescript
export function useResource(id: string) {
  const token = localStorage.getItem('access_token');
  return useQuery({
    queryKey: ['resource', id],
    queryFn: () => fetchResource(id, token!),
    enabled: !!token && !!id,
    refetchInterval: 5000, // optional polling
  });
}
```

**Zustand Store Pattern (expected):**
```typescript
interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => void;
  checkAuth: () => Promise<void>;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({ /* implementation */ }),
    { name: 'auth-storage' }
  )
);
```

---

### 2. Database Migrations

#### Models WITHOUT Migrations (4)

| Model | File | Table Name |
|-------|------|------------|
| `Watchlist` | `/models/watchlist.py:15-42` | `watchlists` |
| `WatchlistItem` | `/models/watchlist.py:45-66` | `watchlist_items` |
| `PriceAlert` | `/models/watchlist.py:69-94` | `price_alerts` |
| `AuditLog` | `/models/audit_log.py:12-28` | `audit_logs` |

**Issue:** These models are also NOT exported in `/models/__init__.py`

#### Migration Conflict

Two paper trading migrations have the same `down_revision`:
- `003_paper_trading.py` → down: `002_constraints_soft_delete`
- `add_paper_trading_tables.py` → down: `002_constraints_soft_delete`

This creates an Alembic branch conflict.

#### Schema Mismatches

**PaperPosition:**
- Migration has: `market_value`, `unrealized_pnl`
- Model has: `stop_loss_price`, `take_profit_price`

**LiveStrategy:**
- Migration has: `daily_pnl`, `started_at`, `stopped_at`
- Model has: `win_rate` (not in migration)

#### Required Migration Commands
```bash
# Add missing models to __init__.py first
# Then generate migration:
cd backend
alembic revision --autogenerate -m "add_watchlist_and_audit_tables"
alembic upgrade head
```

---

### 3. Settings Page

#### Current State
File: `/frontend/src/app/dashboard/settings/page.tsx`

| Section | Lines | Status |
|---------|-------|--------|
| Account Info | 26-55 | Display only |
| Trading Config (API Keys) | 57-90 | Disabled - "Coming Soon" |
| Risk Management | 92-131 | Disabled - "Coming Soon" |
| Notifications | 133-175 | Disabled - "Coming Soon" |

#### Backend APIs Ready

**API Keys** (`/api/v1/api-keys`):
- `POST /` - Create encrypted API key
- `GET /` - List API keys (masked)
- `DELETE /{id}` - Revoke key
- `POST /{id}/rotate` - Rotate credentials
- `POST /{id}/verify` - Test with broker

**Notification Preferences** (`/api/v1/notifications/preferences`):
- `GET /` - List preferences
- `POST /` - Create preference
- `PUT /{id}` - Update preference
- `POST /set-defaults` - Initialize defaults

**Risk Rules** (`/api/v1/risk-rules`):
- Full CRUD already connected at `/dashboard/risk-rules` page
- Settings page just needs link + summary

**User Profile** (`/api/v1/users/me`):
- `PUT /` - Update profile
- `POST /password` - Change password

#### Missing UI Component
Switch/Toggle component not in `/components/ui/` - needs to be added for notification toggles

---

### 4. WebSocket Implementation

#### Backend Status: FULLY IMPLEMENTED

**Endpoint:** `ws://localhost:8000/api/v1/broker/stream`

**Connection:**
```
ws://localhost:8000/api/v1/broker/stream?token=JWT&symbols=AAPL,MSFT&streams=trades,quotes
```

**Query Parameters:**
- `token` - JWT authentication (required)
- `symbols` - Comma-separated symbols
- `streams` - "bars", "quotes", "trades"

**Message Format (Server → Client):**
```json
{
  "type": "trade",
  "data": {
    "symbol": "AAPL",
    "price": 150.25,
    "size": 100,
    "timestamp": "2025-01-20T14:30:00Z"
  }
}
```

**Client Commands:**
```json
{"action": "subscribe", "symbols": ["TSLA"]}
{"action": "unsubscribe", "symbols": ["AAPL"]}
{"action": "ping"}
```

**Key Backend Files:**
- `/backend/app/api/v1/broker.py:265-436` - WebSocket endpoint
- `/backend/app/integrations/market_data_ws.py` - Alpaca stream client
- `/backend/app/core/security.py:124-167` - WebSocket token verification

#### Frontend Status: NOT IMPLEMENTED

- `socket.io-client@4.8.0` installed but unused
- **Note:** FastAPI uses native WebSocket, not Socket.IO protocol
- Should use browser's native `WebSocket` API instead

**Current Polling Intervals:**
- Execution status: 5 seconds
- Notifications: 30 seconds
- Live trading: 5 seconds

#### Frontend Implementation Pattern
```typescript
// Use native WebSocket, NOT socket.io-client
const ws = new WebSocket(
  `${WS_URL}/api/v1/broker/stream?token=${token}&symbols=AAPL&streams=trades,quotes`
);

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  // Handle data.type: 'trade', 'quote', 'bar'
};
```

---

### 5. Charts with Recharts

#### Installation Status
- **Package:** `recharts@2.12.7` in `package.json:37`
- **Usage:** No imports found - completely unused

#### Placeholder Location
`/frontend/src/app/dashboard/portfolio/page.tsx:249-259`
```tsx
<Card>
  <CardContent>
    <div className="h-64 flex items-center justify-center text-muted-foreground">
      Chart Component (integrate with lightweight-charts or recharts)
    </div>
  </CardContent>
</Card>
```

#### Backend API Data

**Equity Curve API:** `GET /api/v1/portfolio/equity-curve`
```json
{
  "data_points": [
    {"date": "2024-01-01T00:00:00Z", "equity": 100000.0, "daily_return": 0.5}
  ],
  "start_date": "...",
  "end_date": "...",
  "total_points": 30
}
```

**Backtest Equity Curve:** In `backtest.results.equity_curve`
```json
{"2024-01-01": 100000, "2024-01-02": 100500}
```

#### Recharts Implementation Pattern
```tsx
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

function EquityCurveChart({ data }: { data: EquityCurvePoint[] }) {
  return (
    <ResponsiveContainer width="100%" height={256}>
      <LineChart data={data}>
        <XAxis dataKey="date" />
        <YAxis />
        <Tooltip />
        <Line type="monotone" dataKey="equity" stroke="#22c55e" />
      </LineChart>
    </ResponsiveContainer>
  );
}
```

#### Data Transformation (for backtest)
```typescript
const chartData = Object.entries(backtest.results.equity_curve).map(([date, value]) => ({
  date,
  equity: value
}));
```

---

## Code References

### Frontend /lib/
- `frontend/src/lib/api/execution.ts:1-71` - Existing API client pattern
- `frontend/src/lib/hooks/use-execution.ts:1-44` - Existing React Query pattern
- `frontend/src/app/(auth)/login/page.tsx:10,16,26` - Auth store usage
- `frontend/src/components/providers.tsx:4,10` - Query client import

### Database
- `backend/app/models/watchlist.py:15-94` - Missing model definitions
- `backend/app/models/audit_log.py:12-28` - Missing model definition
- `backend/app/models/__init__.py` - Needs exports added
- `backend/migrations/versions/003_paper_trading.py` - Conflicting migration

### Settings
- `frontend/src/app/dashboard/settings/page.tsx:57-175` - Disabled sections
- `backend/app/api/v1/api_keys.py:50-526` - Full API implementation
- `backend/app/api/v1/notifications.py:207-399` - Preferences API
- `backend/app/api/v1/users.py:29-107` - Profile/password APIs

### WebSocket
- `backend/app/api/v1/broker.py:265-436` - WebSocket endpoint
- `backend/app/integrations/market_data_ws.py:1-320` - Alpaca streaming
- `backend/app/core/security.py:124-167` - Token verification

### Charts
- `frontend/src/app/dashboard/portfolio/page.tsx:249-259` - Placeholder
- `backend/app/services/portfolio_analytics.py:54-88` - Equity curve service
- `backend/app/schemas/portfolio.py:24-38` - Response schema

---

## Architecture Insights

1. **Token Storage Inconsistency:** Some pages use `'access_token'`, others use `'token'` as localStorage key

2. **API URL Inconsistency:** Mix of `process.env.NEXT_PUBLIC_API_URL`, hardcoded `http://localhost:8000`, and relative paths

3. **WebSocket Protocol Mismatch:** `socket.io-client` installed but FastAPI uses native WebSocket

4. **Migration Branch Conflict:** Two paper trading migrations with same parent revision

5. **Model/Migration Drift:** Several fields in models don't match migration definitions

---

## Implementation Priority

### Phase 1: Critical (2-3 days)
1. Create `/lib/utils.ts` with `cn()` function
2. Create `/lib/stores/auth-store.ts` with Zustand
3. Create `/lib/api/query-client.ts`
4. Create all missing hooks and API clients
5. Standardize token storage to `'access_token'`

### Phase 2: Database (1 day)
1. Export missing models in `__init__.py`
2. Delete duplicate paper trading migration
3. Generate migration for watchlist/audit tables
4. Fix schema mismatches

### Phase 3: Settings (1 day)
1. Add Switch component to UI
2. Connect API key management
3. Connect notification preferences
4. Add profile edit/password change

### Phase 4: Real-time (1-2 days)
1. Create WebSocket hook with native WebSocket API
2. Add real-time price updates to dashboard
3. Replace polling with WebSocket where applicable

### Phase 5: Charts (1 day)
1. Create reusable chart components
2. Implement equity curve in portfolio page
3. Add charts to backtest results

---

## Open Questions

1. Should we keep `socket.io-client` or remove it since FastAPI uses native WebSocket?
2. Should we migrate to axios for consistent API client or keep fetch?
3. Should paper trading data (market_value, unrealized_pnl) be calculated at query time or stored?
