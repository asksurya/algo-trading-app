#!/usr/bin/env python3
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

STRATEGIES_CONFIG = [
    {"ticker": "AMD", "strategy": "momentum", "name": "AMD Momentum", "params": {"period": 20, "threshold": 0.0}},
    {"ticker": "GOOGL", "strategy": "breakout", "name": "GOOGL Breakout", "params": {"lookback_period": 20, "breakout_threshold": 0.02}},
    {"ticker": "AAPL", "strategy": "breakout", "name": "AAPL Breakout", "params": {"lookback_period": 20, "breakout_threshold": 0.02}},
    {"ticker": "NVDA", "strategy": "mean_reversion", "name": "NVDA Mean Reversion", "params": {"period": 20, "entry_threshold": 2.0, "exit_threshold": 0.5}},
    {"ticker": "AVGO", "strategy": "breakout", "name": "AVGO Breakout", "params": {"lookback_period": 20, "breakout_threshold": 0.02}},
    {"ticker": "MSFT", "strategy": "breakout", "name": "MSFT Breakout", "params": {"lookback_period": 20, "breakout_threshold": 0.02}},
    {"ticker": "TSLA", "strategy": "mean_reversion", "name": "TSLA Mean Reversion", "params": {"period": 20, "entry_threshold": 2.0, "exit_threshold": 0.5}},
    {"ticker": "ARM", "strategy": "momentum", "name": "ARM Momentum", "params": {"period": 20, "threshold": 0.0}},
    {"ticker": "AMZN", "strategy": "breakout", "name": "AMZN Breakout", "params": {"lookback_period": 20, "breakout_threshold": 0.02}},
    {"ticker": "CRM", "strategy": "breakout", "name": "CRM Breakout", "params": {"lookback_period": 20, "breakout_threshold": 0.02}},
    {"ticker": "META", "strategy": "macd", "name": "META MACD", "params": {"fast_period": 12, "slow_period": 26, "signal_period": 9}},
    {"ticker": "NFLX", "strategy": "rsi", "name": "NFLX RSI", "params": {"period": 14, "oversold": 30, "overbought": 70}},
]

def login():
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={"email": "testtrader@example.com", "password": "TestPass123!"}
    )
    if response.status_code == 200:
        return response.json().get("access_token")
    print(f"Login failed: {response.status_code} - {response.text}")
    return None

def create_strategy(token, config):
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {
        "name": config["name"],
        "description": f"Optimized {config['strategy']} strategy for {config['ticker']} (1-year backtest)",
        "strategy_type": config["strategy"],
        "parameters": config["params"],
        "tickers": [config["ticker"]]
    }
    return requests.post(f"{BASE_URL}/strategies", headers=headers, json=payload)

def main():
    print("=" * 60)
    print("CREATING OPTIMIZED STRATEGIES")
    print("=" * 60)
    
    token = login()
    if not token:
        return
    print("Login successful!\n")
    
    created = []
    for config in STRATEGIES_CONFIG:
        print(f"  Creating {config['name']}...", end=" ")
        response = create_strategy(token, config)
        if response.status_code in [200, 201]:
            data = response.json()
            created.append({"ticker": config["ticker"], "strategy_id": data.get("id"), "name": config["name"]})
            print(f"OK")
        else:
            print(f"FAILED ({response.status_code}): {response.text[:100]}")
    
    print(f"\n{'='*60}\nCreated {len(created)} strategies\n{'='*60}")
    for s in created:
        print(f"  {s['ticker']}: {s['name']}")
    
    with open("strategy_ids.json", "w") as f:
        json.dump(created, f, indent=2)
    print("\nSaved to strategy_ids.json")

if __name__ == "__main__":
    main()
