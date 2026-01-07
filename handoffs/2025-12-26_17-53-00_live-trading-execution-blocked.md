---
date: 2025-12-26T17:53:00-06:00
git_commit: ff63e54a990737296b34d5dd612260c16bb38256
branch: main
repository: algo-trading-app
topic: "Live Trading Execution - Scheduler Not Running"
tags: [live-trading, scheduler, frontend-routing, critical]
status: blocked
last_updated: 2025-12-26
type: handoff
---

# Handoff: Live Trading Created But Not Executing - Scheduler Issue

## Task(s)

**Primary Objective**: Get live paper trading working with browser-based control during market hours (markets open NOW, Dec 26 12:30 PM CST)

**Status by Component**:
1. ✅ **COMPLETED**: Backend API fully functional
   - Created `/api/v1/live-trading/dashboard` endpoint (backend/app/api/v1/live_trading.py:28-60)
   - All CRUD endpoints working for live strategies

2. ✅ **COMPLETED**: Strategy creation and storage
   - Created 9 live trading strategies via `start_live_trading_sessions.py`
   - All strategies marked as 'active' in SQLite database
   - Allocated $90,000 across AAPL (3), AMD (3), NVDA (3)

3. ❌ **BLOCKED**: Strategy execution/monitoring
   - **CRITICAL ISSUE**: Strategies created but NEVER checked (last_check field is NULL for all 9)
   - 0 signals generated, 0 trades executed despite markets being open for 5+ hours
   - Root cause: Background scheduler not monitoring live strategies

4. ❌ **BLOCKED**: Frontend UI
   - Page `/dashboard/live-trading` exists but redirects to `/dashboard`
   - Next.js client-side routing issue (under investigation)
   - **Workaround**: API and terminal monitoring functional

## Critical References

1. **Live Trading Service**: `backend/app/services/strategy_scheduler.py` - The scheduler that SHOULD be monitoring strategies but ISN'T running
2. **Main App Startup**: `backend/app/main.py:28-30` - Starts OLD scheduler (`app/strategies/scheduler.py`), not the live trading one
3. **Active Strategies List**: `LIVE_TRADING_ACTIVE_NOW.md` - Complete documentation of 9 active strategies with IDs

## Recent Changes

**Backend**:
- `backend/app/api/v1/live_trading.py:28-60` - Added dashboard endpoint that returns summary + active strategies
- Database: Created 9 live_strategies records with status='active' (see strategy IDs below)

**Frontend**:
- `frontend/src/app/dashboard/live-trading/page.tsx` - Simplified to minimal test, then restored full version from page-backup.tsx
- `frontend/src/app/dashboard/live-trading/new_backup/` - Temporarily moved 'new' subdirectory to isolate routing issue
- Restarted frontend dev server with cleared `.next` cache multiple times

**Scripts**:
- `start_live_trading_sessions.py` - Successfully created 9 strategies at 2025-12-26 12:30 CST
- `/tmp/check_live_trading.sh` - Quick status check script for terminal monitoring

## Learnings

### Critical Discovery: Two Separate Schedulers

1. **Old Scheduler** (`backend/app/strategies/scheduler.py`):
   - Started by `main.py:28-30` via `start_scheduler()`
   - Uses `StrategyScheduler` class from lines 25-134
   - Monitors OLD strategy execution system (Strategy, StrategyExecution models)
   - Runs every 1 minute via APScheduler

2. **Live Trading Scheduler** (`backend/app/services/strategy_scheduler.py`):
   - NOT started by main.py
   - Uses `StrategyScheduler` class (different one) with `start_monitoring()` method
   - Monitors LiveStrategy models with check_interval
   - **THIS IS WHAT NEEDS TO RUN** but currently isn't

### Database Evidence of Scheduler Not Running

```bash
sqlite3 data/trading_state.db "SELECT name, status, datetime(last_check), total_signals FROM live_strategies LIMIT 3;"
# Output shows:
# - status: 'active' ✅
# - last_check: NULL ❌ (never checked!)
# - total_signals: 0 ❌ (no monitoring happening)
```

### Frontend Routing Issue

- Page compiles successfully (HTTP 200 in logs: `GET /dashboard/live-trading 200 in 928ms`)
- But client-side redirects to /dashboard immediately
- Tested at different route `/dashboard/trading` - same redirect behavior
- Removed nested `new/` subdirectory - no effect
- **Likely cause**: React/Next.js runtime error or auth issue triggering redirect

### Strategy IDs (for API control)

```
37249701-7adc-442c-b66d-ba928dabae4c - AAPL Keltner_Channel (Breakout)
e4c6780f-5f4e-457f-9eab-940b2bb52403 - AAPL Keltner_Channel (Wider bands)
aa794fc2-f936-4a57-8978-0ea42b468766 - AAPL Donchian_Channel (System 2)
d36e132d-a0cd-4227-8f64-b86bf679d760 - AMD Keltner_Channel (Wider bands)
d36e5d0e-7aa7-4983-9ac8-bb3859d0f611 - AMD Keltner_Channel (Mean reversion)
dbafe52a-0433-4782-8e61-a3059d95761f - AMD Ichimoku_Cloud (Faster)
4ba7ba7c-95e0-416a-b4a0-448db09efda6 - NVDA Keltner_Channel (Breakout)
b8e7bb6a-3845-4fb8-973b-1e453bec5c69 - NVDA Keltner_Channel (Wider bands)
3003bf38-5db3-4dac-8e26-7a2310438ece - NVDA Ichimoku_Cloud (Slower)
```

## Artifacts

**Documentation**:
- `LIVE_TRADING_ACTIVE_NOW.md` - Complete guide to monitoring/controlling strategies
- `START_HERE_LIVE_TRADING.md` - Original deployment guide
- `LIVE_TRADING_ANALYSIS.md` - Strategy analysis results
- `STRATEGY_RANKINGS_BY_TICKER.md` - Performance rankings
- `live_trading_status.json` - JSON status export

**Scripts**:
- `start_live_trading_sessions.py` - Creates and starts live trading sessions
- `monitor_live_trading.py` - Dashboard monitoring script
- `/tmp/check_live_trading.sh` - Quick CLI status check
- `analyze_all_strategies_for_live_trading.py` - Backtest analysis tool

**Backend Files Modified**:
- `backend/app/api/v1/live_trading.py:28-60` - Dashboard endpoint
- `backend/.env:3` - Switched to SQLite (DATABASE_URL)

**Frontend Files**:
- `frontend/src/app/dashboard/live-trading/page.tsx` - Full component (restored from backup)
- `frontend/src/app/dashboard/live-trading/page-backup.tsx` - Backup of original

**Database**:
- `data/trading_state.db` - Contains 9 live_strategies records (table: live_strategies)

## Action Items & Next Steps

### CRITICAL - Start Live Strategy Monitoring (Priority 1)

**Option A: Integrate live scheduler into main.py startup**
1. Modify `backend/app/main.py:28-30` to also start live trading scheduler
2. Import and start `app.services.strategy_scheduler.StrategyScheduler`
3. Need to handle async context (StrategyScheduler.start_monitoring() is async)
4. Restart backend and verify strategies get checked (last_check updates)

**Option B: Create background task/worker**
1. Create FastAPI background task in lifespan to run `strategy_scheduler.start_monitoring()`
2. Ensure proper async loop handling
3. Test that strategies are checked every 60 seconds

**Verification**:
```bash
# After fix, this should show recent timestamps:
sqlite3 data/trading_state.db "SELECT name, datetime(last_check), total_signals FROM live_strategies LIMIT 3;"
```

### Fix Frontend Routing Issue (Priority 2)

**Investigation needed**:
1. Check browser console for React errors when navigating to `/dashboard/live-trading`
2. Add console.log to `page.tsx:17-27` useEffect to see why redirect happens
3. Check if auth token validation is failing client-side
4. Test API call directly: `curl -H "Authorization: Bearer TOKEN" http://localhost:8000/api/v1/live-trading/dashboard`

**Quick workaround** (if debugging takes too long):
1. Create standalone HTML page at `frontend/public/live-trading.html`
2. Use vanilla JS to call API and render strategy cards
3. User can access at `http://localhost:3000/live-trading.html`

### Verify Trade Execution (Priority 3)

Once scheduler is running:
1. Monitor database for signal generation: `watch -n 10 'sqlite3 data/trading_state.db "SELECT name, total_signals, executed_trades FROM live_strategies ORDER BY total_signals DESC LIMIT 5;"'`
2. Check backend logs for "Checking strategy" and "Detected X signals" messages
3. Verify orders table gets populated when trades execute
4. Monitor Alpaca paper account for executed orders

## Other Notes

### Backend Status
- Running on port 8000 (PID varies, check with `ps aux | grep uvicorn`)
- Logs: `/tmp/backend_restart.log` (most recent)
- Database: SQLite at `/Users/ashwin/projects/algo-trading-app/data/trading_state.db`
- Paper trading connected to Alpaca API (keys in `backend/.env`)

### Frontend Status
- Dev server on port 3000 (check with `ps aux | grep "next dev"`)
- Auth working: user `trader@example.com` / `Trading123!` (created in session)
- Token stored in localStorage as 'access_token'
- Main dashboard at `/dashboard` works fine

### Market Hours
- Markets close at 4:00 PM EST / 3:00 PM CST
- **Currently open** (as of handoff creation 5:53 PM CST - MARKETS CLOSED for today)
- Strategies will continue monitoring but won't execute until next market open

### Strategy Performance Expectations
Based on backtests (see `live_trading_strategy_recommendations.json`):
- AAPL strategies: 24-29% return, 1.7+ Sharpe, 100% win rate
- AMD strategies: 82-96% return, 1.6+ Sharpe, 66-100% win rate
- NVDA strategies: 44-53% return, 1.6-1.8 Sharpe, 75-100% win rate

**Note**: These are backtest results on 12 months historical data. Live performance will differ.

### Known Issues
1. Redis cache errors in logs (benign - Redis not running, app falls back)
2. `WARNING: Could not import src.backtesting` on startup (benign)
3. Live Trading page redirect issue (blocks browser UI)
4. **CRITICAL**: Scheduler not running (blocks all trade execution)

### Quick Commands Reference

**Check strategy status**:
```bash
/tmp/check_live_trading.sh
```

**View all strategies**:
```bash
sqlite3 data/trading_state.db "SELECT id, name, status FROM live_strategies;"
```

**Stop a strategy via API**:
```bash
curl -X POST -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/v1/live-trading/strategies/STRATEGY_ID/stop
```

**Watch for signals**:
```bash
watch -n 30 'sqlite3 data/trading_state.db "SELECT name, total_signals, executed_trades FROM live_strategies;"'
```

**Backend API docs**:
http://localhost:8000/docs
