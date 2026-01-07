#!/usr/bin/env python3
"""
Monitor Live Trading Sessions
==============================

This script monitors active live paper trading sessions and displays
real-time status updates.

Features:
- Display all active sessions and their status
- Show recent signals and trades
- Monitor P&L and portfolio value
- Display system health
"""

import json
import requests
import sys
import time
from datetime import datetime
from typing import Dict, Any


# ============================================================================
# Configuration
# ============================================================================

BACKEND_URL = "http://localhost:8000/api/v1"
STATUS_FILE = "live_trading_status.json"


# ============================================================================
# Helper Functions
# ============================================================================

def load_status_file() -> Dict[str, Any]:
    """Load the status file to get session info."""
    try:
        with open(STATUS_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: Status file {STATUS_FILE} not found")
        print("Have you run start_live_trading_sessions.py yet?")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {STATUS_FILE}: {e}")
        sys.exit(1)


def get_auth_token() -> str:
    """Get authentication token."""
    try:
        login_data = {
            "email": "paper.trader@test.com",
            "password": "TestPassword123!"
        }
        response = requests.post(
            f"{BACKEND_URL}/auth/login",
            json=login_data,
            timeout=10
        )
        if response.status_code == 200:
            return response.json()["access_token"]
        else:
            print(f"Error logging in: {response.status_code}")
            sys.exit(1)
    except Exception as e:
        print(f"Error during authentication: {e}")
        sys.exit(1)


def get_system_status(token: str) -> Dict[str, Any]:
    """Get live trading system status."""
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.get(
            f"{BACKEND_URL}/live-trading/status",
            headers=headers,
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"Status code: {response.status_code}"}
    except Exception as e:
        return {"error": str(e)}


def get_portfolio(token: str) -> Dict[str, Any]:
    """Get current portfolio."""
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.get(
            f"{BACKEND_URL}/live-trading/portfolio",
            headers=headers,
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"Status code: {response.status_code}"}
    except Exception as e:
        return {"error": str(e)}


def get_live_strategies(token: str) -> list:
    """Get all live strategies."""
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.get(
            f"{BACKEND_URL}/live-trading/strategies",
            headers=headers,
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        else:
            return []
    except Exception as e:
        print(f"Error getting strategies: {e}")
        return []


def get_recent_orders(token: str, limit: int = 20) -> list:
    """Get recent orders."""
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.get(
            f"{BACKEND_URL}/live-trading/orders?limit={limit}",
            headers=headers,
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        else:
            return []
    except Exception as e:
        print(f"Error getting orders: {e}")
        return []


def format_timestamp(ts_str):
    """Format timestamp for display."""
    if not ts_str:
        return "Never"
    try:
        ts = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
        return ts.strftime('%Y-%m-%d %H:%M:%S')
    except:
        return str(ts_str)


def display_status(status_data: Dict[str, Any], system_status: Dict[str, Any],
                   portfolio: Dict[str, Any], strategies: list, orders: list):
    """Display comprehensive status."""

    print("\n" + "="*100)
    print("LIVE PAPER TRADING - STATUS DASHBOARD")
    print("="*100)
    print(f"Current Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Started: {format_timestamp(status_data.get('created_at'))}")

    # System Status
    print("\n" + "-"*100)
    print("SYSTEM STATUS")
    print("-"*100)
    print(f"Running: {'✓ YES' if system_status.get('is_running') else '✗ NO'}")
    print(f"Active Strategies: {system_status.get('active_strategies', 0)}")

    try:
        total_pnl = float(system_status.get('total_pnl', 0))
        pnl_color = "+" if total_pnl >= 0 else ""
        print(f"Total P&L: {pnl_color}${total_pnl:.2f}")
    except:
        print(f"Total P&L: {system_status.get('total_pnl', 0)}")

    last_trade = system_status.get('last_trade_at')
    print(f"Last Trade: {format_timestamp(last_trade)}")
    print(f"Paper Trading Mode: {'✓ ENABLED' if system_status.get('paper_trading_mode') else '✗ DISABLED'}")

    # Portfolio
    print("\n" + "-"*100)
    print("PORTFOLIO")
    print("-"*100)

    try:
        total_value = float(portfolio.get('total_value', 0))
        cash = float(portfolio.get('cash', 0))
        buying_power = float(portfolio.get('buying_power', 0))
        total_pnl_portfolio = float(portfolio.get('total_pnl', 0))
        total_return_pct = float(portfolio.get('total_return_pct', 0))

        print(f"Total Value: ${total_value:,.2f}")
        print(f"Cash: ${cash:,.2f}")
        print(f"Buying Power: ${buying_power:,.2f}")
        print(f"Total P&L: ${total_pnl_portfolio:,.2f} ({total_return_pct:+.2f}%)")
    except:
        print(f"Total Value: {portfolio.get('total_value', 0)}")
        print(f"Cash: {portfolio.get('cash', 0)}")

    positions = portfolio.get('positions', [])
    print(f"Open Positions: {len(positions)}")

    if positions:
        print("\nPositions:")
        print(f"  {'Symbol':<10} {'Qty':<10} {'Avg Price':<12} {'Current':<12} {'P&L':<12} {'% Change':<10}")
        print(f"  {'-'*10} {'-'*10} {'-'*12} {'-'*12} {'-'*12} {'-'*10}")
        for pos in positions:
            try:
                qty = float(pos.get('qty', 0))
                avg_price = float(pos.get('avg_price', 0))
                current_price = float(pos.get('current_price', 0))
                unrealized_pnl = float(pos.get('unrealized_pnl', 0))
                pct_change = ((current_price - avg_price) / avg_price * 100) if avg_price > 0 else 0

                pnl_str = f"${unrealized_pnl:+.2f}"
                pct_str = f"{pct_change:+.2f}%"

                print(f"  {pos.get('symbol', 'N/A'):<10} {qty:<10.2f} ${avg_price:<11.2f} "
                      f"${current_price:<11.2f} {pnl_str:<12} {pct_str:<10}")
            except:
                continue

    # Active Strategies
    print("\n" + "-"*100)
    print("ACTIVE STRATEGIES")
    print("-"*100)

    # Group by ticker
    from collections import defaultdict
    by_ticker = defaultdict(list)

    for strat in strategies:
        if strat.get('status') == 'active':
            symbols = strat.get('symbols', [])
            ticker = symbols[0] if symbols else 'Unknown'
            by_ticker[ticker].append(strat)

    for ticker in sorted(by_ticker.keys()):
        print(f"\n{ticker} ({len(by_ticker[ticker])} strategies):")
        for strat in by_ticker[ticker]:
            name = strat.get('name', 'Unknown')
            last_check = format_timestamp(strat.get('last_check'))
            last_signal = format_timestamp(strat.get('last_signal'))
            total_signals = strat.get('total_signals', 0)
            executed_trades = strat.get('executed_trades', 0)
            current_positions = strat.get('current_positions', 0)

            try:
                strat_pnl = float(strat.get('total_pnl', 0))
                win_rate = float(strat.get('win_rate', 0) or 0)
                print(f"  • {name}")
                print(f"    Status: {strat.get('status', 'unknown').upper()} | "
                      f"Signals: {total_signals} | Trades: {executed_trades} | "
                      f"Positions: {current_positions}")
                print(f"    P&L: ${strat_pnl:+.2f} | Win Rate: {win_rate:.1f}%")
                print(f"    Last Check: {last_check} | Last Signal: {last_signal}")
            except:
                print(f"  • {name}")
                print(f"    Status: {strat.get('status', 'unknown').upper()}")

    # Recent Orders
    print("\n" + "-"*100)
    print("RECENT ORDERS (Last 10)")
    print("-"*100)

    if orders:
        print(f"  {'Time':<20} {'Symbol':<8} {'Side':<6} {'Qty':<8} {'Price':<10} {'Status':<10}")
        print(f"  {'-'*20} {'-'*8} {'-'*6} {'-'*8} {'-'*10} {'-'*10}")

        for order in orders[:10]:
            timestamp = format_timestamp(order.get('submitted_at') or order.get('filled_at'))
            symbol = order.get('symbol', 'N/A')
            side = order.get('side', 'N/A').upper()
            qty = order.get('qty', 0)
            price = order.get('filled_avg_price', 0)
            status = order.get('status', 'unknown').upper()

            try:
                price_str = f"${float(price):.2f}"
            except:
                price_str = str(price)

            print(f"  {timestamp:<20} {symbol:<8} {side:<6} {qty:<8} {price_str:<10} {status:<10}")
    else:
        print("  No orders yet")

    print("\n" + "="*100)


def monitor_continuous():
    """Continuously monitor and display status."""

    print("Starting continuous monitoring (Press Ctrl+C to stop)...")

    # Load initial status
    status_data = load_status_file()

    # Get token
    token = get_auth_token()

    try:
        while True:
            # Clear screen (platform-independent)
            print("\033[2J\033[H")  # ANSI escape codes

            # Get latest data
            system_status = get_system_status(token)
            portfolio = get_portfolio(token)
            strategies = get_live_strategies(token)
            orders = get_recent_orders(token, limit=20)

            # Display
            display_status(status_data, system_status, portfolio, strategies, orders)

            print("\nRefreshing in 30 seconds... (Ctrl+C to stop)")
            time.sleep(30)

    except KeyboardInterrupt:
        print("\n\nMonitoring stopped by user")


def main():
    """Main entry point."""

    # Check backend
    try:
        response = requests.get(
            f"{BACKEND_URL.replace('/api/v1', '')}/health",
            timeout=5
        )
        if response.status_code != 200:
            print("Error: Backend is not responding")
            sys.exit(1)
    except:
        print("Error: Cannot connect to backend")
        print("Please ensure backend is running on port 8000")
        sys.exit(1)

    # Load status
    status_data = load_status_file()

    # Get token
    token = get_auth_token()

    # Get data
    system_status = get_system_status(token)
    portfolio = get_portfolio(token)
    strategies = get_live_strategies(token)
    orders = get_recent_orders(token, limit=20)

    # Display once
    display_status(status_data, system_status, portfolio, strategies, orders)

    # Ask if user wants continuous monitoring
    print("\nOptions:")
    print("  1. Exit")
    print("  2. Start continuous monitoring (refresh every 30s)")

    choice = input("\nSelect option (1 or 2): ").strip()

    if choice == "2":
        monitor_continuous()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
