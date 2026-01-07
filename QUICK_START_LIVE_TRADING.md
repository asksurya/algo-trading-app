# Live Trading Quick Start Guide

## Current Status
- **9 strategies deployed** ✓
- **Paper trading active** ✓
- **Backend running** ✓
- **$90,000 capital allocated** (paper money)

## Quick Commands

### Monitor Status
```bash
# Real-time dashboard
python3 monitor_live_trading.py

# View status file
cat live_trading_status.json
```

### View Strategies
```bash
# Get auth token first
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"paper.trader@test.com","password":"TestPassword123!"}' \
  | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

# List all strategies
curl -s -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/live-trading/strategies | python3 -m json.tool

# System status
curl -s -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/live-trading/status | python3 -m json.tool

# Portfolio
curl -s -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/live-trading/portfolio | python3 -m json.tool
```

### Control Trading

```bash
# Pause all trading
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  http://localhost:8000/api/v1/live-trading/action \
  -d '{"action":"pause"}'

# Resume all trading
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  http://localhost:8000/api/v1/live-trading/action \
  -d '{"action":"resume"}'

# Stop specific strategy
STRATEGY_ID="c9cb23ac-5193-474f-a63f-c3dcbebbdd6a"
curl -X POST -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/live-trading/strategies/$STRATEGY_ID/stop
```

## Active Strategies

### AAPL (3 strategies)
- Keltner Channel - Breakout (28.97% return, Sharpe 1.77)
- Keltner Channel - Wider Bands (24.48% return, Sharpe 1.73)
- Donchian Channel - System 2 (24.48% return, Sharpe 1.73)

### AMD (3 strategies)
- Keltner Channel - Wider Bands (90.84% return, Sharpe 1.63)
- Keltner Channel - Mean Reversion (82.68% return, Sharpe 1.65)
- Ichimoku Cloud - Faster (96.20% return, Sharpe 1.73)

### NVDA (3 strategies)
- Keltner Channel - Breakout (53.08% return, Sharpe 1.78)
- Keltner Channel - Wider Bands (44.93% return, Sharpe 1.60)
- Ichimoku Cloud - Slower (53.44% return, Sharpe 1.77)

## Important Notes

### ⚠️ Signal Monitoring
**Background monitoring NOT running automatically yet!**

Strategies are created and ACTIVE but won't generate signals automatically. Need to implement background service.

See: `LIVE_TRADING_DEPLOYMENT_REPORT.md` for implementation details.

### Paper Trading
- No real money at risk
- Alpaca paper trading API
- $100,000 starting balance

### Market Hours
- Trading: 9:30 AM - 4:00 PM ET (Mon-Fri)
- Check interval: Every 5 minutes
- Auto-execute: Enabled

## Files & Documentation

- **LIVE_TRADING_DEPLOYMENT_REPORT.md** - Complete deployment details
- **LIVE_TRADING_SUMMARY.md** - Operational guide
- **live_trading_status.json** - Current status snapshot
- **start_live_trading_sessions.py** - Deployment script
- **monitor_live_trading.py** - Monitoring dashboard

## Troubleshooting

### Backend not responding
```bash
docker-compose restart api
```

### Check logs
```bash
docker-compose logs -f api
```

### Reset paper account
```bash
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  http://localhost:8000/api/v1/live-trading/action \
  -d '{"action":"reset"}'
```

## Next Steps

1. Implement background signal monitoring
2. Test signal generation manually
3. Verify order execution
4. Monitor first trades
5. Track P&L updates

---

**Paper Trading Only - No Real Money at Risk!**
