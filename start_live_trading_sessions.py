#!/usr/bin/env python3
"""
Start Live Paper Trading Sessions
==================================

This script creates and starts live paper trading sessions for the best
performing strategies based on comprehensive backtest analysis.

Features:
- Analyzes backtest results to find top performers per ticker
- Creates live trading sessions via backend API
- Configures risk management and position sizing
- Monitors session startup and status
- Generates status report

Requirements:
- Backend must be running on localhost:8000
- Valid authentication token
- Alpaca paper trading credentials configured
"""

import json
import requests
import sys
from datetime import datetime
from typing import List, Dict, Any, Optional
from collections import defaultdict


# ============================================================================
# Configuration
# ============================================================================

BACKEND_URL = "http://localhost:8000/api/v1"
BACKTEST_RESULTS_FILE = "backtest_results_five_new_strategies.json"
STRATEGY_IDS_FILE = "strategy_ids.json"
OUTPUT_STATUS_FILE = "live_trading_status.json"

# Session Configuration
INITIAL_CAPITAL = 10000  # Paper money per session
POSITION_SIZE_PCT = 0.15  # 15% of capital per position
MAX_POSITIONS = 5  # Max concurrent positions per strategy
DAILY_LOSS_LIMIT = 500  # Stop trading if daily loss exceeds this
MAX_POSITION_SIZE = 5000  # Max $ per position
CHECK_INTERVAL = 300  # Check for signals every 5 minutes
AUTO_EXECUTE = True  # Automatically execute trades (paper mode)

# Selection Criteria
MIN_SHARPE_RATIO = 0.5  # Minimum Sharpe ratio
MIN_WIN_RATE = 40  # Minimum win rate %
MIN_RETURN = 5  # Minimum total return %
TOP_N_PER_TICKER = 3  # Select top N strategies per ticker


# ============================================================================
# Helper Functions
# ============================================================================

def load_json_file(filename: str) -> Dict[str, Any]:
    """Load JSON file."""
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: File {filename} not found")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {filename}: {e}")
        sys.exit(1)


def save_json_file(filename: str, data: Dict[str, Any]):
    """Save data to JSON file."""
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2, default=str)
    print(f"\nSaved status to {filename}")


def get_auth_token() -> str:
    """Get authentication token (for now, using a test approach)."""
    # TODO: In production, use proper authentication
    # For now, we'll need to create a user and get a token
    print("\nNote: Authentication required for API calls")
    print("This script assumes you have a valid token or will create a test user")

    # Try to register/login a test user for paper trading
    try:
        # Try to register
        register_data = {
            "email": "paper.trader@test.com",
            "password": "TestPassword123!",
            "full_name": "Paper Trading Bot"
        }

        response = requests.post(
            f"{BACKEND_URL}/auth/register",
            json=register_data,
            timeout=10
        )

        if response.status_code in [200, 201]:
            # User created, now login to get token
            print("✓ Created test user for paper trading, logging in...")
            login_data = {
                "email": register_data["email"],
                "password": register_data["password"]
            }
            response = requests.post(
                f"{BACKEND_URL}/auth/login",
                json=login_data,
                timeout=10
            )
            if response.status_code == 200:
                print("✓ Logged in successfully")
                return response.json()["access_token"]
            else:
                print(f"Error logging in after registration: {response.status_code}")
                print(response.text)
                sys.exit(1)
        elif response.status_code == 400:
            # User exists, try login
            login_data = {
                "email": register_data["email"],
                "password": register_data["password"]
            }
            response = requests.post(
                f"{BACKEND_URL}/auth/login",
                json=login_data,
                timeout=10
            )
            if response.status_code == 200:
                print("✓ Logged in as test user")
                return response.json()["access_token"]
            else:
                print(f"Error logging in: {response.status_code}")
                print(response.text)
                sys.exit(1)
        else:
            print(f"Error with auth: {response.status_code}")
            print(response.text)
            sys.exit(1)
    except Exception as e:
        print(f"Error during authentication: {e}")
        sys.exit(1)


def analyze_backtest_results(results: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Analyze backtest results and select top strategies per ticker.

    Returns:
        Dict mapping ticker to list of top strategies with their metrics
    """
    print("\n" + "="*80)
    print("ANALYZING BACKTEST RESULTS")
    print("="*80)

    all_results = results.get("all_results", [])

    # Group results by symbol
    by_symbol = defaultdict(list)
    for result in all_results:
        if result.get("success") and result.get("symbol"):
            symbol = result["symbol"]

            # Apply filters
            sharpe = result.get("sharpe_ratio", 0)
            win_rate = result.get("win_rate_pct", 0)
            total_return = result.get("total_return_pct", 0)

            if (sharpe >= MIN_SHARPE_RATIO and
                win_rate >= MIN_WIN_RATE and
                total_return >= MIN_RETURN):

                by_symbol[symbol].append({
                    "strategy": result["strategy"],
                    "description": result.get("description", ""),
                    "total_return_pct": total_return,
                    "sharpe_ratio": sharpe,
                    "win_rate_pct": win_rate,
                    "max_drawdown_pct": result.get("max_drawdown_pct", 0),
                    "profit_factor": result.get("profit_factor", 0),
                    "total_trades": result.get("total_trades", 0),
                })

    # Select top N per symbol
    top_strategies = {}
    for symbol, strategies in by_symbol.items():
        # Sort by a composite score: Sharpe * Win Rate * Return
        sorted_strategies = sorted(
            strategies,
            key=lambda x: x["sharpe_ratio"] * x["win_rate_pct"] * x["total_return_pct"],
            reverse=True
        )

        top_strategies[symbol] = sorted_strategies[:TOP_N_PER_TICKER]

        print(f"\n{symbol}: Selected {len(top_strategies[symbol])} strategies")
        for i, strat in enumerate(top_strategies[symbol], 1):
            print(f"  {i}. {strat['strategy']} - {strat['description']}")
            print(f"     Return: {strat['total_return_pct']:.2f}%, "
                  f"Sharpe: {strat['sharpe_ratio']:.2f}, "
                  f"Win Rate: {strat['win_rate_pct']:.1f}%")

    return top_strategies


def get_strategy_id_for_ticker(ticker: str, strategy_ids: List[Dict[str, str]]) -> Optional[str]:
    """Get the strategy ID for a ticker from strategy_ids.json."""
    for entry in strategy_ids:
        if entry.get("ticker") == ticker:
            return entry.get("strategy_id")
    return None


def create_live_strategy(
    token: str,
    strategy_id: str,
    name: str,
    symbols: List[str],
) -> Optional[Dict[str, Any]]:
    """
    Create a live trading strategy via API.

    Args:
        token: Authentication token
        strategy_id: Base strategy ID
        name: Name for the live strategy
        symbols: List of symbols to trade

    Returns:
        Created strategy response or None if failed
    """
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    payload = {
        "name": name,
        "strategy_id": strategy_id,
        "symbols": symbols,
        "check_interval": CHECK_INTERVAL,
        "auto_execute": AUTO_EXECUTE,
        "max_positions": MAX_POSITIONS,
        "daily_loss_limit": DAILY_LOSS_LIMIT,
        "position_size_pct": POSITION_SIZE_PCT,
        "max_position_size": MAX_POSITION_SIZE,
    }

    try:
        response = requests.post(
            f"{BACKEND_URL}/live-trading/strategies",
            headers=headers,
            json=payload,
            timeout=10
        )

        if response.status_code == 201:
            return response.json()
        else:
            print(f"  ✗ Failed to create strategy: {response.status_code}")
            print(f"    {response.text}")
            return None
    except Exception as e:
        print(f"  ✗ Error creating strategy: {e}")
        return None


def start_live_strategy(token: str, live_strategy_id: str) -> bool:
    """
    Start a live trading strategy via API.

    Args:
        token: Authentication token
        live_strategy_id: Live strategy ID to start

    Returns:
        True if started successfully, False otherwise
    """
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(
            f"{BACKEND_URL}/live-trading/strategies/{live_strategy_id}/start",
            headers=headers,
            timeout=10
        )

        if response.status_code == 200:
            return True
        else:
            print(f"  ✗ Failed to start strategy: {response.status_code}")
            return False
    except Exception as e:
        print(f"  ✗ Error starting strategy: {e}")
        return False


def get_live_strategies(token: str) -> List[Dict[str, Any]]:
    """Get all live strategies."""
    headers = {
        "Authorization": f"Bearer {token}"
    }

    try:
        response = requests.get(
            f"{BACKEND_URL}/live-trading/strategies",
            headers=headers,
            timeout=10
        )

        if response.status_code == 200:
            return response.json()
        else:
            print(f"Warning: Failed to get strategies: {response.status_code}")
            return []
    except Exception as e:
        print(f"Warning: Error getting strategies: {e}")
        return []


def get_system_status(token: str) -> Dict[str, Any]:
    """Get live trading system status."""
    headers = {
        "Authorization": f"Bearer {token}"
    }

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


# ============================================================================
# Main Execution
# ============================================================================

def main():
    print("="*80)
    print("LIVE PAPER TRADING SESSION STARTER")
    print("="*80)
    print(f"Started at: {datetime.now().isoformat()}")

    # Check backend connectivity
    print("\n1. Checking backend connectivity...")
    try:
        response = requests.get(f"{BACKEND_URL.replace('/api/v1', '')}/health", timeout=5)
        if response.status_code == 200:
            print("   ✓ Backend is running")
        else:
            print(f"   ✗ Backend returned status code: {response.status_code}")
            sys.exit(1)
    except Exception as e:
        print(f"   ✗ Cannot connect to backend: {e}")
        print("   Please ensure backend is running on port 8000")
        sys.exit(1)

    # Authenticate
    print("\n2. Authenticating...")
    token = get_auth_token()

    # Load backtest results
    print("\n3. Loading backtest results...")
    backtest_results = load_json_file(BACKTEST_RESULTS_FILE)
    print(f"   ✓ Loaded {len(backtest_results.get('all_results', []))} backtest results")

    # Load strategy IDs
    print("\n4. Loading strategy IDs...")
    strategy_ids = load_json_file(STRATEGY_IDS_FILE)
    print(f"   ✓ Loaded {len(strategy_ids)} strategy IDs")

    # Analyze results
    print("\n5. Analyzing backtest results...")
    top_strategies = analyze_backtest_results(backtest_results)

    if not top_strategies:
        print("\n✗ No strategies met the selection criteria")
        print(f"   Criteria: Sharpe >= {MIN_SHARPE_RATIO}, Win Rate >= {MIN_WIN_RATE}%, Return >= {MIN_RETURN}%")
        sys.exit(1)

    # Create live trading sessions
    print("\n" + "="*80)
    print("CREATING LIVE TRADING SESSIONS")
    print("="*80)

    created_sessions = []
    failed_sessions = []

    for symbol, strategies in top_strategies.items():
        print(f"\n{symbol}:")

        # Get strategy ID for this ticker
        base_strategy_id = get_strategy_id_for_ticker(symbol, strategy_ids)

        if not base_strategy_id:
            print(f"  ✗ No base strategy ID found for {symbol}, skipping...")
            failed_sessions.append({
                "symbol": symbol,
                "error": "No base strategy ID found"
            })
            continue

        for i, strat in enumerate(strategies, 1):
            strategy_name = f"{symbol} {strat['strategy']} - {strat['description']}"
            print(f"\n  Creating session {i}/{len(strategies)}: {strategy_name}")

            # Create the live strategy
            live_strategy = create_live_strategy(
                token=token,
                strategy_id=base_strategy_id,
                name=strategy_name,
                symbols=[symbol]
            )

            if live_strategy:
                print(f"    ✓ Created live strategy: {live_strategy['id']}")

                # Start the strategy
                print(f"    Starting strategy...")
                if start_live_strategy(token, live_strategy['id']):
                    print(f"    ✓ Strategy started successfully")
                    created_sessions.append({
                        "id": live_strategy["id"],
                        "symbol": symbol,
                        "strategy": strat["strategy"],
                        "description": strat["description"],
                        "metrics": {
                            "return_pct": strat["total_return_pct"],
                            "sharpe": strat["sharpe_ratio"],
                            "win_rate": strat["win_rate_pct"],
                        },
                        "status": "active"
                    })
                else:
                    print(f"    ✗ Failed to start strategy")
                    failed_sessions.append({
                        "symbol": symbol,
                        "strategy": strat["strategy"],
                        "error": "Failed to start"
                    })
            else:
                failed_sessions.append({
                    "symbol": symbol,
                    "strategy": strat["strategy"],
                    "error": "Failed to create"
                })

    # Get final status
    print("\n" + "="*80)
    print("CHECKING FINAL STATUS")
    print("="*80)

    all_live_strategies = get_live_strategies(token)
    system_status = get_system_status(token)

    print(f"\nTotal live strategies: {len(all_live_strategies)}")
    print(f"Active strategies: {system_status.get('active_strategies', 0)}")

    # Handle total_pnl which might be a Decimal or string
    try:
        total_pnl = float(system_status.get('total_pnl', 0))
        print(f"Total P&L: ${total_pnl:.2f}")
    except (ValueError, TypeError):
        print(f"Total P&L: {system_status.get('total_pnl', 0)}")

    # Create status report
    status_report = {
        "created_at": datetime.now().isoformat(),
        "summary": {
            "sessions_created": len(created_sessions),
            "sessions_active": len([s for s in created_sessions if s.get("status") == "active"]),
            "sessions_failed": len(failed_sessions),
            "tickers": list(top_strategies.keys()),
            "total_capital_allocated": len(created_sessions) * INITIAL_CAPITAL,
        },
        "configuration": {
            "initial_capital_per_session": INITIAL_CAPITAL,
            "position_size_pct": POSITION_SIZE_PCT,
            "max_positions": MAX_POSITIONS,
            "daily_loss_limit": DAILY_LOSS_LIMIT,
            "max_position_size": MAX_POSITION_SIZE,
            "check_interval": CHECK_INTERVAL,
            "auto_execute": AUTO_EXECUTE,
        },
        "selection_criteria": {
            "min_sharpe_ratio": MIN_SHARPE_RATIO,
            "min_win_rate": MIN_WIN_RATE,
            "min_return": MIN_RETURN,
            "top_n_per_ticker": TOP_N_PER_TICKER,
        },
        "sessions": created_sessions,
        "failed_sessions": failed_sessions,
        "system_status": system_status,
    }

    # Save status report
    save_json_file(OUTPUT_STATUS_FILE, status_report)

    # Print summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"✓ Successfully created: {len(created_sessions)} sessions")
    print(f"✗ Failed: {len(failed_sessions)} sessions")
    print(f"Total capital allocated: ${len(created_sessions) * INITIAL_CAPITAL:,}")
    print(f"\nTickers trading: {', '.join(top_strategies.keys())}")

    if created_sessions:
        print("\nActive Trading Sessions:")
        by_ticker = defaultdict(list)
        for session in created_sessions:
            by_ticker[session["symbol"]].append(session)

        for ticker in sorted(by_ticker.keys()):
            print(f"\n  {ticker}:")
            for session in by_ticker[ticker]:
                print(f"    - {session['strategy']} ({session['description']})")
                print(f"      Return: {session['metrics']['return_pct']:.2f}%, "
                      f"Sharpe: {session['metrics']['sharpe']:.2f}, "
                      f"Win Rate: {session['metrics']['win_rate']:.1f}%")

    if failed_sessions:
        print("\nFailed Sessions:")
        for failure in failed_sessions:
            print(f"  - {failure.get('symbol', 'Unknown')}: {failure.get('strategy', 'Unknown')} - {failure.get('error', 'Unknown error')}")

    print("\n" + "="*80)
    print("MONITORING INSTRUCTIONS")
    print("="*80)
    print("\nTo monitor ongoing trading:")
    print("  1. Check status file: cat live_trading_status.json")
    print("  2. View backend logs: docker-compose logs -f api")
    print("  3. Access API: curl -H 'Authorization: Bearer <token>' http://localhost:8000/api/v1/live-trading/status")
    print("  4. View dashboard: http://localhost:3000/dashboard/live-trading")

    print("\nTo stop all trading:")
    print("  curl -X POST -H 'Authorization: Bearer <token>' http://localhost:8000/api/v1/live-trading/action -d '{\"action\":\"pause\"}'")

    print("\nPaper Trading Mode: ENABLED")
    print("No real money will be used - this is simulation only!")

    print("\n" + "="*80)
    print(f"Completed at: {datetime.now().isoformat()}")
    print("="*80)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nFatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
