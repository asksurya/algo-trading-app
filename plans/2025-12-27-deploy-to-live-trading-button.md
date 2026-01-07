# Deploy to Live Trading Button - Implementation Plan

## Overview

Add a "Deploy to Live Trading" button across all strategy analysis pages that instantly creates and starts a live trading strategy with sensible defaults. This enables users to quickly deploy a strategy for automated execution after analyzing its performance.

## Current State Analysis

### Existing Infrastructure
- **LiveStrategy model** (`backend/app/models/live_strategy.py:15-127`) - Complete with all required fields
- **StrategyScheduler** (`backend/app/services/strategy_scheduler.py:28-460`) - Fully functional monitoring loop
- **SignalMonitor** (`backend/app/services/signal_monitor.py:59-371`) - Signal detection working
- **Order Execution** (`backend/app/integrations/order_execution.py:150-596`) - Alpaca integration complete
- **LiveTradingAPI** (`frontend/src/lib/api/live-trading.ts`) - Frontend API client exists
- **Live Trading Service** (`backend/app/services/live_trading_service.py`) - Has `create_live_strategy` method

### Pages Requiring Button
1. **Strategies List** (`/dashboard/strategies`) - Strategy cards with "View Details" button
2. **Backtest Results** (`/dashboard/backtests/[id]`) - Detailed backtest performance
3. **Optimizer Results** (`/dashboard/optimizer`) - Strategy ranking and execution

## Desired End State

After implementation:
1. Users see a "Deploy to Live" button on strategy cards, backtest results, and optimizer results
2. Clicking the button instantly creates a `LiveStrategy` record with `auto_execute=true` and `status=ACTIVE`
3. The strategy immediately begins monitoring for signals and executing trades
4. User is redirected to the live trading dashboard to monitor
5. Toast notification confirms deployment

### Success Criteria
- Button appears on all 3 pages
- Click creates LiveStrategy and starts monitoring within 2 seconds
- User redirected to `/dashboard/live-trading` with success toast
- Strategy appears in live dashboard immediately

## What We're NOT Doing

- Not adding configuration dialogs (user requested quick deploy)
- Not modifying the scheduler or signal monitor logic
- Not changing how order execution works
- Not adding new order types (limit, bracket) in this phase
- Not adding stop-loss/take-profit configuration

## Implementation Approach

### Phase 1: Backend - Quick Deploy Endpoint

Create a streamlined endpoint for instant deployment that:
- Creates LiveStrategy with sensible defaults
- Immediately activates it
- Returns the created strategy

### Phase 2: Frontend - Reusable Deploy Button Component

Create a shared component that can be used across all pages.

### Phase 3: Integrate Button into Pages

Add the button to all three target pages.

---

## Phase 1: Backend - Quick Deploy Endpoint

### Overview
Add a new endpoint `POST /api/v1/live-trading/quick-deploy` that creates and activates a live strategy in one step.

### Changes Required:

#### 1. Add Quick Deploy Schema
**File**: `backend/app/schemas/live_trading.py`
**Changes**: Add request/response schema for quick deploy

```python
class QuickDeployRequest(BaseModel):
    """Request for quick deployment of a strategy to live trading."""
    strategy_id: str
    symbols: List[str]
    # Optional overrides (all have sensible defaults)
    name: Optional[str] = None  # Defaults to "Live - {strategy.name}"
    check_interval: int = 300  # 5 minutes default
    auto_execute: bool = True
    max_positions: int = 5
    position_size_pct: float = 0.02  # 2% of portfolio
    max_position_size: Optional[float] = None
    daily_loss_limit: Optional[float] = None

class QuickDeployResponse(BaseModel):
    """Response for quick deploy."""
    success: bool
    live_strategy_id: str
    name: str
    status: str
    message: str
```

#### 2. Add Quick Deploy Service Method
**File**: `backend/app/services/live_trading_service.py`
**Changes**: Add `quick_deploy` method

```python
async def quick_deploy(
    self,
    user_id: str,
    request: QuickDeployRequest
) -> LiveStrategy:
    """
    Quick deploy a strategy to live trading with sensible defaults.
    Creates the LiveStrategy and immediately activates it.
    """
    # 1. Get the base strategy
    strategy = await self.db.execute(
        select(Strategy).where(Strategy.id == request.strategy_id)
    )
    strategy = strategy.scalar_one_or_none()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")

    # 2. Generate name if not provided
    name = request.name or f"Live - {strategy.name}"

    # 3. Create LiveStrategy record
    live_strategy = LiveStrategy(
        user_id=user_id,
        strategy_id=request.strategy_id,
        name=name,
        symbols=request.symbols,
        status=LiveStrategyStatus.ACTIVE,  # Start immediately
        check_interval=request.check_interval,
        auto_execute=request.auto_execute,
        max_positions=request.max_positions,
        position_size_pct=request.position_size_pct,
        max_position_size=request.max_position_size,
        daily_loss_limit=request.daily_loss_limit,
        started_at=datetime.now(timezone.utc),
        state={},
    )

    self.db.add(live_strategy)
    await self.db.commit()
    await self.db.refresh(live_strategy)

    # 4. Send notification
    await self.notification_service.create_notification(
        user_id=user_id,
        notification_type=NotificationType.TRADE_EXECUTED,
        title=f"Live Trading Activated: {name}",
        message=f"Strategy deployed with auto-execute enabled. Monitoring {len(request.symbols)} symbols.",
        priority=NotificationPriority.HIGH,
        metadata={"live_strategy_id": live_strategy.id}
    )

    return live_strategy
```

#### 3. Add Quick Deploy Endpoint
**File**: `backend/app/api/v1/live_trading.py`
**Changes**: Add POST endpoint

```python
@router.post("/quick-deploy", response_model=QuickDeployResponse)
async def quick_deploy_strategy(
    request: QuickDeployRequest,
    live_trading_service: LiveTradingService = Depends(get_live_trading_service),
    current_user: User = Depends(get_current_user),
):
    """
    Quick deploy a strategy to live trading.

    Creates a live strategy with sensible defaults and immediately activates it.
    The strategy will begin monitoring markets and executing trades.
    """
    live_strategy = await live_trading_service.quick_deploy(
        user_id=current_user.id,
        request=request
    )

    return QuickDeployResponse(
        success=True,
        live_strategy_id=live_strategy.id,
        name=live_strategy.name,
        status=live_strategy.status.value,
        message=f"Strategy deployed successfully. Now monitoring {len(request.symbols)} symbols."
    )
```

### Success Criteria:

#### Automated Verification:
- [x] Backend server starts without errors: `cd backend && poetry run uvicorn app.main:app --reload`
- [x] API endpoint responds: `curl -X POST http://localhost:8000/api/v1/live-trading/quick-deploy -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{"strategy_id": "test-id", "symbols": ["AAPL"]}'`

#### Manual Verification:
- [x] LiveStrategy created in database with status=ACTIVE
- [x] Strategy appears in scheduler's active strategies list
- [x] Notification sent to user

**Implementation Note**: After completing this phase and automated verification passes, pause for manual confirmation before proceeding to Phase 2.

---

## Phase 2: Frontend - Deploy Button Component & API

### Overview
Create a reusable "Deploy to Live" button component and add the API method.

### Changes Required:

#### 1. Add Quick Deploy API Method
**File**: `frontend/src/lib/api/live-trading.ts`
**Changes**: Add `quickDeploy` method to LiveTradingAPI class

```typescript
export interface QuickDeployRequest {
  strategy_id: string;
  symbols: string[];
  name?: string;
  check_interval?: number;
  auto_execute?: boolean;
  max_positions?: number;
  position_size_pct?: number;
  max_position_size?: number;
  daily_loss_limit?: number;
}

export interface QuickDeployResponse {
  success: boolean;
  live_strategy_id: string;
  name: string;
  status: string;
  message: string;
}

// Add to LiveTradingAPI class:
async quickDeploy(request: QuickDeployRequest): Promise<QuickDeployResponse> {
  const response = await fetch(`${this.baseUrl}/quick-deploy`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${this.token}`,
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to deploy strategy');
  }

  return response.json();
}
```

#### 2. Create Deploy to Live Button Component
**File**: `frontend/src/components/deploy-to-live-button.tsx` (new file)
**Changes**: Create reusable button component

```tsx
'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Rocket, Loader2 } from 'lucide-react';
import LiveTradingAPI from '@/lib/api/live-trading';
import { toast } from 'sonner'; // or your toast library

interface DeployToLiveButtonProps {
  strategyId: string;
  strategyName: string;
  symbols: string[];
  variant?: 'default' | 'outline' | 'secondary';
  size?: 'default' | 'sm' | 'lg';
  className?: string;
}

export function DeployToLiveButton({
  strategyId,
  strategyName,
  symbols,
  variant = 'default',
  size = 'default',
  className,
}: DeployToLiveButtonProps) {
  const router = useRouter();
  const [deploying, setDeploying] = useState(false);

  const handleDeploy = async () => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      toast.error('Please log in to deploy strategies');
      router.push('/login');
      return;
    }

    if (symbols.length === 0) {
      toast.error('No symbols specified for trading');
      return;
    }

    setDeploying(true);

    try {
      const api = new LiveTradingAPI(token);
      const result = await api.quickDeploy({
        strategy_id: strategyId,
        symbols: symbols,
        name: `Live - ${strategyName}`,
        auto_execute: true,
        check_interval: 300, // 5 minutes
      });

      toast.success(`${result.name} deployed successfully!`, {
        description: `Now monitoring ${symbols.join(', ')}`,
      });

      router.push('/dashboard/live-trading');
    } catch (error) {
      toast.error('Failed to deploy strategy', {
        description: error instanceof Error ? error.message : 'Unknown error',
      });
    } finally {
      setDeploying(false);
    }
  };

  return (
    <Button
      variant={variant}
      size={size}
      onClick={handleDeploy}
      disabled={deploying || symbols.length === 0}
      className={className}
    >
      {deploying ? (
        <>
          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          Deploying...
        </>
      ) : (
        <>
          <Rocket className="mr-2 h-4 w-4" />
          Deploy to Live
        </>
      )}
    </Button>
  );
}
```

### Success Criteria:

#### Automated Verification:
- [x] TypeScript compilation passes: `cd frontend && npm run type-check`
- [x] No ESLint errors: `cd frontend && npm run lint`

#### Manual Verification:
- [ ] Button component renders correctly
- [ ] Loading state shows during deployment
- [ ] Redirect to live trading page works

**Implementation Note**: After completing this phase and automated verification passes, pause for manual confirmation before proceeding to Phase 3.

---

## Phase 3: Integrate Button into Pages

### Overview
Add the DeployToLiveButton to all three target pages.

### Changes Required:

#### 1. Strategies List Page
**File**: `frontend/src/app/dashboard/strategies/page.tsx`
**Changes**: Add deploy button to each strategy card

```tsx
// Add import at top:
import { DeployToLiveButton } from '@/components/deploy-to-live-button';

// In the strategy card, after the existing buttons (around line 141-160):
<div className="flex gap-2 mt-4">
  <Link href={`/dashboard/strategies/${strategy.id}`} className="flex-1">
    <Button className="w-full" variant="outline">
      View Details
    </Button>
  </Link>
  <DeployToLiveButton
    strategyId={strategy.id}
    strategyName={strategy.name}
    symbols={strategy.symbols || ['AAPL']} // Use strategy's configured symbols or default
    variant="default"
    size="default"
  />
  <Button
    variant="outline"
    size="icon"
    onClick={() => handleDelete(strategy.id, strategy.name)}
    disabled={deleteStrategy.isPending}
  >
    {/* ... existing delete button ... */}
  </Button>
</div>
```

#### 2. Backtest Results Page
**File**: `frontend/src/app/dashboard/backtests/[id]/page.tsx`
**Changes**: Add deploy button in header section

```tsx
// Add import at top:
import { DeployToLiveButton } from '@/components/deploy-to-live-button';

// In the header section (around line 32-56), add button after Badge:
<div className="flex items-center gap-4">
  <Link href="/dashboard/backtests">
    <Button variant="ghost" size="icon">
      <ArrowLeft className="h-4 w-4" />
    </Button>
  </Link>
  <div className="flex-1">
    <h1 className="text-3xl font-bold">{backtest.name}</h1>
    <p className="text-muted-foreground">
      {new Date(backtest.start_date).toLocaleDateString()} -{' '}
      {new Date(backtest.end_date).toLocaleDateString()}
    </p>
  </div>
  <Badge
    variant={/* ... existing badge ... */}
  >
    {backtest.status}
  </Badge>
  {backtest.status === 'completed' && results && results.total_return_pct > 0 && (
    <DeployToLiveButton
      strategyId={backtest.strategy_id}
      strategyName={backtest.name}
      symbols={backtest.symbols || [backtest.symbol]}
      variant="default"
      size="lg"
    />
  )}
</div>
```

#### 3. Optimizer Results Page
**File**: `frontend/src/app/dashboard/optimizer/page.tsx`
**Changes**: Add deploy button for each strategy result

```tsx
// Add import at top:
import { DeployToLiveButton } from '@/components/deploy-to-live-button';

// In the results table (around line 510-528), add Deploy column:
<TableHeader>
  <TableRow>
    <TableHead>Rank</TableHead>
    <TableHead>Strategy</TableHead>
    <TableHead className="text-right">Score</TableHead>
    <TableHead className="text-right">Return</TableHead>
    <TableHead className="text-right">Sharpe</TableHead>
    <TableHead className="text-right">Max DD</TableHead>
    <TableHead className="text-right">Win Rate</TableHead>
    <TableHead className="text-right">Trades</TableHead>
    <TableHead>Action</TableHead>  {/* NEW COLUMN */}
  </TableRow>
</TableHeader>
<TableBody>
  {(result.all_performances ?? []).map((perf) => (
    <TableRow key={perf.strategy_id} className={perf.rank === 1 ? 'bg-green-50' : ''}>
      {/* ... existing cells ... */}
      <TableCell>
        <DeployToLiveButton
          strategyId={String(perf.strategy_id)}
          strategyName={perf.strategy_name}
          symbols={[symbol]}  // symbol from the tab context
          variant="outline"
          size="sm"
        />
      </TableCell>
    </TableRow>
  ))}
</TableBody>
```

### Success Criteria:

#### Automated Verification:
- [x] TypeScript compilation passes: `cd frontend && npm run type-check`
- [x] No ESLint errors: `cd frontend && npm run lint`
- [x] Frontend builds successfully: `cd frontend && npm run build`

#### Manual Verification:
- [ ] Button appears on Strategies page for each strategy card
- [ ] Button appears on Backtest results page (only for profitable completed backtests)
- [ ] Button appears on Optimizer results page for each strategy row
- [ ] Clicking any button creates LiveStrategy and redirects to live trading page
- [ ] Strategy is actively monitoring after deployment

**Implementation Note**: After completing this phase and all verification passes, the feature is complete.

---

## Testing Strategy

### Unit Tests:
- Test QuickDeployRequest schema validation
- Test LiveTradingService.quick_deploy creates correct LiveStrategy
- Test DeployToLiveButton component renders correctly

### Integration Tests:
- Test POST /api/v1/live-trading/quick-deploy endpoint
- Test full deployment flow from frontend to backend

### Manual Testing Steps:
1. Go to /dashboard/strategies, click "Deploy to Live" on any strategy
2. Verify redirect to /dashboard/live-trading
3. Verify new strategy appears with status ACTIVE
4. Wait for check_interval (5 minutes) and verify signals are being checked
5. Repeat for backtest results page
6. Repeat for optimizer results page

## Performance Considerations

- Quick deploy should complete within 2 seconds
- No polling or WebSocket needed - simple request/response
- Scheduler already running in background picks up new strategies automatically

## Migration Notes

No database migrations required - using existing LiveStrategy table.

## References

- Existing live trading API: `backend/app/api/v1/live_trading.py`
- LiveStrategy model: `backend/app/models/live_strategy.py`
- Strategy scheduler: `backend/app/services/strategy_scheduler.py`
- Frontend live trading page: `frontend/src/app/dashboard/live-trading/page.tsx`
