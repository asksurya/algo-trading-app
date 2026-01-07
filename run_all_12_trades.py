#!/usr/bin/env python3
import requests

BASE_URL = "http://localhost:8000/api/v1"

# Login
resp = requests.post(f"{BASE_URL}/auth/login", json={"email": "testtrader@example.com", "password": "TestPass123!"})
if resp.status_code != 200:
    print("Login failed:", resp.text)
    exit(1)

token = resp.json().get("access_token")
headers = {"Authorization": f"Bearer {token}"}

print("=" * 65)
print("PAPER TRADING - ALL 12 STRATEGY TICKERS")
print("=" * 65)

# All 12 tickers from strategy_ids.json with appropriate quantities
trades = [
    {"symbol": "AMD",   "qty": 15, "side": "buy", "strategy": "Momentum"},
    {"symbol": "GOOGL", "qty": 10, "side": "buy", "strategy": "Breakout"},
    {"symbol": "AAPL",  "qty": 12, "side": "buy", "strategy": "Breakout"},
    {"symbol": "NVDA",  "qty": 15, "side": "buy", "strategy": "Mean Reversion"},
    {"symbol": "AVGO",  "qty": 8,  "side": "buy", "strategy": "Breakout"},
    {"symbol": "MSFT",  "qty": 8,  "side": "buy", "strategy": "Breakout"},
    {"symbol": "TSLA",  "qty": 6,  "side": "buy", "strategy": "Mean Reversion"},
    {"symbol": "ARM",   "qty": 25, "side": "buy", "strategy": "Momentum"},
    {"symbol": "AMZN",  "qty": 15, "side": "buy", "strategy": "Breakout"},
    {"symbol": "CRM",   "qty": 10, "side": "buy", "strategy": "Breakout"},
    {"symbol": "META",  "qty": 6,  "side": "buy", "strategy": "MACD"},
    {"symbol": "NFLX",  "qty": 4,  "side": "buy", "strategy": "RSI"},
]

print(f"\nExecuting {len(trades)} trades:\n")

for trade in trades:
    print(f"  {trade['strategy']:15} | BUY {trade['qty']:3} {trade['symbol']:5}...", end=" ")
    resp = requests.post(
        f"{BASE_URL}/paper-trading/orders",
        headers=headers,
        json={"symbol": trade["symbol"], "qty": trade["qty"], "side": trade["side"], "order_type": "market"}
    )
    if resp.status_code == 200:
        result = resp.json()
        if result.get("success"):
            t = result["trade"]
            print(f"FILLED @ ${t['price']:,.2f} (Value: ${t['value']:,.2f})")
        else:
            print(f"REJECTED: {result.get('error','Unknown')[:40]}")
    else:
        print(f"ERROR {resp.status_code}: {resp.text[:50]}")

# Final status
resp = requests.get(f"{BASE_URL}/paper-trading/account", headers=headers)
acc = resp.json()

print(f"\n{'='*65}")
print("PORTFOLIO SUMMARY")
print("=" * 65)
print(f"  Starting Balance: ${acc.get('initial_balance', 0):,.2f}")
print(f"  Cash Remaining:   ${acc.get('cash_balance', 0):,.2f}")
print(f"  Total Equity:     ${acc.get('total_equity', 0):,.2f}")
print(f"  Positions:        {len(acc.get('positions', {}))}")

print(f"\n{'='*65}")
print("POSITIONS")
print("=" * 65)
total_invested = 0
for sym, pos in sorted(acc.get("positions", {}).items()):
    total_invested += pos["market_value"]
    print(f"  {sym:5}: {pos['qty']:5.0f} shares @ ${pos['avg_price']:8,.2f} = ${pos['market_value']:10,.2f}")

print(f"  {'-'*55}")
print(f"  {'TOTAL':5}  {' '*14} Invested: ${total_invested:10,.2f}")
print(f"\n12 strategies now active. Monitor at: http://localhost:3002/dashboard")
