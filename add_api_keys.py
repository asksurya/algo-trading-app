#!/usr/bin/env python3
"""
Add Alpaca API keys to paper trading account
"""
import requests
import json
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('backend/.env')

BACKEND_URL = "http://localhost:8000/api/v1"

# Login credentials
EMAIL = "paper.trader@test.com"
PASSWORD = "TestPassword123!"

# API credentials from .env
ALPACA_API_KEY = os.getenv('ALPACA_API_KEY')
ALPACA_SECRET_KEY = os.getenv('ALPACA_SECRET_KEY')
ALPACA_BASE_URL = os.getenv('ALPACA_BASE_URL', 'https://paper-api.alpaca.markets')

def main():
    print("=" * 80)
    print("Adding Alpaca API Keys to Paper Trading Account")
    print("=" * 80)

    # 1. Login
    print("\n1. Logging in...")
    login_response = requests.post(
        f"{BACKEND_URL}/auth/login",
        json={"email": EMAIL, "password": PASSWORD},
        timeout=10
    )

    if login_response.status_code != 200:
        print(f"✗ Login failed: {login_response.status_code}")
        print(login_response.text)
        sys.exit(1)

    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✓ Logged in successfully")

    # 2. Add API keys
    print("\n2. Adding Alpaca API keys...")
    api_key_data = {
        "name": "Alpaca Paper Trading",
        "broker": "alpaca",
        "api_key": ALPACA_API_KEY,
        "api_secret": ALPACA_SECRET_KEY,
        "base_url": ALPACA_BASE_URL,
        "is_paper_trading": True,
        "is_default": True
    }

    add_key_response = requests.post(
        f"{BACKEND_URL}/api-keys",
        json=api_key_data,
        headers=headers,
        timeout=10
    )

    if add_key_response.status_code in [200, 201]:
        print("✓ API keys added successfully!")
        api_key_info = add_key_response.json()
        print(f"\nAPI Key ID: {api_key_info.get('id')}")
        print(f"Broker: {api_key_info.get('broker')}")
        print(f"Paper Trading: {api_key_info.get('is_paper_trading')}")
        print(f"Status: {api_key_info.get('status')}")
    else:
        print(f"✗ Failed to add API keys: {add_key_response.status_code}")
        print(add_key_response.text)
        sys.exit(1)

    # 3. Verify
    print("\n3. Verifying API keys...")
    verify_response = requests.get(
        f"{BACKEND_URL}/api-keys",
        headers=headers,
        timeout=10
    )

    if verify_response.status_code == 200:
        keys = verify_response.json()
        print(f"✓ Total API keys configured: {len(keys)}")
        for key in keys:
            print(f"  - {key.get('name')} ({key.get('broker')}) - {key.get('status')}")

    print("\n" + "=" * 80)
    print("API Keys Setup Complete!")
    print("=" * 80)
    print("\nThe paper trading strategies can now execute trades automatically.")
    print("Trades will be placed on Alpaca's paper trading account.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n✗ Error: {e}")
        sys.exit(1)
