import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

# Login
resp = requests.post(f"{BASE_URL}/auth/login", json={"email": "testtrader@example.com", "password": "TestPass123!"})
token = resp.json().get("access_token")
headers = {"Authorization": f"Bearer {token}"}

print("=" * 60)
print("PAPER TRADING - EXECUTING OPTIMIZED STRATEGIES")
print("=" * 60)

# Get account
resp = requests.get(f"{BASE_URL}/paper-trading/account", headers=headers)
data = resp.json()
acc = data.get("data", data)  # Handle both wrapped and unwrapped response

print(f"\nCurrent Account:")
print(f"  Cash: ${acc['cash_balance']:,.2f}")
print(f"  Equity: ${acc['total_equity']:,.2f}")
print(f"  Positions: {len(acc.get('positions', {}))}")

# Execute trades for the top performing tickers based on backtest
trades = [
    {"symbol": "GOOGL", "qty": 3, "side": "buy", "strategy": "Breakout"},
    {"symbol": "AMD", "qty": 10, "side": "buy", "strategy": "Momentum"},  
    {"symbol": "NVDA", "qty": 3, "side": "buy", "strategy": "Mean Reversion"},
    {"symbol": "AVGO", "qty": 2, "side": "buy", "strategy": "Breakout"},
    {"symbol": "ARM", "qty": 10, "side": "buy", "strategy": "Momentum"},
    {"symbol": "TSLA", "qty": 5, "side": "buy", "strategy": "Mean Reversion"},
]

print(f"\nExecuting {len(trades)} strategy-based trades:\n")

for trade in trades:
    print(f"  {trade['strategy']:15} | {trade['side'].upper()} {trade['qty']:3} {trade['symbol']:5}...", end=" ")
    resp = requests.post(
        f"{BASE_URL}/paper-trading/orders",
        headers=headers,
        json={"symbol": trade["symbol"], "qty": trade["qty"], "side": trade["side"], "order_type": "market"}
    )
    if resp.status_code == 200:
        result = resp.json()
        if result.get("success"):
            t = result["trade"]
            print(f"FILLED @ ${t['price']:,.2f}")
        else:
            print(f"REJECTED: {result.get('error','Unknown')[:40]}")
    else:
        print(f"ERROR {resp.status_code}")

# Final status
resp = requests.get(f"{BASE_URL}/paper-trading/account", headers=headers)
data = resp.json()
acc = data.get("data", data)

print(f"\n{'='*60}")
print("PORTFOLIO AFTER TRADES")
print("=" * 60)
print(f"  Cash: ${acc['cash_balance']:,.2f}")
print(f"  Equity: ${acc['total_equity']:,.2f}")
print(f"\nPositions:")
for sym, pos in acc.get('positions', {}).items():
    pnl = pos.get('unrealized_pnl', 0)
    pnl_str = f"+${pnl:,.2f}" if pnl >= 0 else f"-${abs(pnl):,.2f}"
    print(f"  {sym:5}: {pos['qty']:5.0f} shares @ ${pos['avg_price']:,.2f} = ${pos['market_value']:,.2f} ({pnl_str})")

print(f"\n{'='*60}")
print("STRATEGIES NOW ACTIVE FOR 2-WEEK PAPER TRADING")
print("=" * 60)
print("Monitor at: http://localhost:3002/dashboard")
