#!/usr/bin/env python3
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def login():
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={"email": "testtrader@example.com", "password": "TestPass123!"}
    )
    if response.status_code == 200:
        return response.json().get("access_token")
    return None

def start_strategy(token, strategy_id):
    headers = {"Authorization": f"Bearer {token}"}
    # Correct path: /strategies/execution/{id}/start
    response = requests.post(
        f"{BASE_URL}/strategies/execution/{strategy_id}/start",
        headers=headers
    )
    return response

def main():
    print("=" * 60)
    print("STARTING ALL OPTIMIZED STRATEGIES")
    print("=" * 60)
    
    token = login()
    if not token:
        print("Login failed!")
        return
    print("Login successful!\n")
    
    with open("strategy_ids.json") as f:
        strategies = json.load(f)
    
    started = []
    for s in strategies:
        print(f"  Starting {s['name']}...", end=" ")
        response = start_strategy(token, s["strategy_id"])
        if response.status_code == 200:
            data = response.json()
            started.append(s)
            print(f"OK")
        else:
            print(f"FAILED ({response.status_code}): {response.text[:150]}")
    
    print(f"\n{'='*60}")
    print(f"STARTED {len(started)}/12 STRATEGIES FOR 2-WEEK PAPER TRADING")
    print("=" * 60)

if __name__ == "__main__":
    main()
