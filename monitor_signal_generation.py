#!/usr/bin/env python3
"""
Signal Generation Monitor
=========================

Monitors paper trading strategies for signal generation issues, bugs, and anomalies.

Features:
- Monitors active strategy health
- Detects signal generation failures
- Tracks market data fetch issues
- Logs anomalies and errors
- Generates health reports
"""

import asyncio
import json
import requests
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from collections import defaultdict
import time

# ============================================================================
# Configuration
# ============================================================================

BACKEND_URL = "http://localhost:8000/api/v1"
CHECK_INTERVAL = 60  # Check every 60 seconds
LOG_FILE = "signal_monitor.log"
REPORT_FILE = "signal_monitor_report.json"

# Thresholds for anomaly detection
MAX_TIME_SINCE_SIGNAL_CHECK = 600  # 10 minutes (2x the check interval)
MAX_CONSECUTIVE_ERRORS = 3
MIN_EXPECTED_SIGNALS_PER_DAY = 0  # At least some activity expected

# Authentication
AUTH_TOKEN = None

# ============================================================================
# Logging and Reporting
# ============================================================================

def log_message(message: str, level: str = "INFO"):
    """Log message with timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] [{level}] {message}"
    print(log_entry)

    with open(LOG_FILE, 'a') as f:
        f.write(log_entry + "\n")


def save_report(report: Dict[str, Any]):
    """Save monitoring report to file."""
    with open(REPORT_FILE, 'w') as f:
        json.dump(report, f, indent=2, default=str)


# ============================================================================
# API Client
# ============================================================================

def get_auth_token() -> str:
    """Get authentication token."""
    global AUTH_TOKEN

    if AUTH_TOKEN:
        return AUTH_TOKEN

    try:
        # Login with paper trading account
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
            AUTH_TOKEN = response.json()["access_token"]
            log_message("✓ Authenticated successfully")
            return AUTH_TOKEN
        else:
            log_message(f"✗ Authentication failed: {response.status_code}", "ERROR")
            return None

    except Exception as e:
        log_message(f"✗ Authentication error: {e}", "ERROR")
        return None


def get_headers() -> Dict[str, str]:
    """Get request headers with auth token."""
    token = get_auth_token()
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}


def api_get(endpoint: str) -> Optional[Dict[str, Any]]:
    """Make authenticated GET request to API."""
    try:
        response = requests.get(
            f"{BACKEND_URL}/{endpoint}",
            headers=get_headers(),
            timeout=10
        )

        if response.status_code == 200:
            return response.json()
        else:
            log_message(f"✗ API error on {endpoint}: {response.status_code}", "ERROR")
            return None

    except Exception as e:
        log_message(f"✗ API request error on {endpoint}: {e}", "ERROR")
        return None


# ============================================================================
# Strategy Monitoring
# ============================================================================

def get_active_strategies() -> List[Dict[str, Any]]:
    """Get all active strategies."""
    data = api_get("live-trading/strategies")
    if data:
        return [s for s in data if s.get("status") == "active"]
    return []


def get_signals_today() -> List[Dict[str, Any]]:
    """Get signals detected today."""
    data = api_get("live-trading/signals")
    if data:
        # Filter for today
        today = datetime.now().date()
        return [s for s in data if datetime.fromisoformat(s["created_at"].replace('Z', '+00:00')).date() == today]
    return []


def get_recent_errors() -> List[Dict[str, Any]]:
    """Check backend logs for recent errors."""
    # This would need backend support - for now return empty
    return []


# ============================================================================
# Anomaly Detection
# ============================================================================

def check_strategy_health(strategy: Dict[str, Any]) -> Dict[str, Any]:
    """Check individual strategy health."""
    issues = []

    # Check if strategy is stuck (last check time too old)
    if "last_check_time" in strategy:
        try:
            last_check = datetime.fromisoformat(strategy["last_check_time"].replace('Z', '+00:00'))
            time_since_check = (datetime.now(last_check.tzinfo) - last_check).total_seconds()

            if time_since_check > MAX_TIME_SINCE_SIGNAL_CHECK:
                issues.append(f"No signal check for {time_since_check:.0f} seconds (max: {MAX_TIME_SINCE_SIGNAL_CHECK})")
        except Exception as e:
            issues.append(f"Cannot parse last_check_time: {e}")

    # Check for error count
    error_count = strategy.get("consecutive_errors", 0)
    if error_count >= MAX_CONSECUTIVE_ERRORS:
        issues.append(f"High error count: {error_count} consecutive errors")

    # Check if monitoring is active but no symbols
    symbols = strategy.get("symbols", [])
    if not symbols:
        issues.append("No symbols being monitored")

    return {
        "strategy_id": strategy.get("id"),
        "strategy_name": strategy.get("name"),
        "status": "healthy" if not issues else "unhealthy",
        "issues": issues
    }


def analyze_signal_patterns(strategies: List[Dict[str, Any]], signals: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze signal generation patterns for anomalies."""
    analysis = {
        "total_strategies": len(strategies),
        "total_signals_today": len(signals),
        "strategies_with_signals": len(set(s["strategy_id"] for s in signals)),
        "strategies_without_signals": [],
        "anomalies": []
    }

    # Find strategies that haven't generated any signals
    strategies_with_signals = set(s["strategy_id"] for s in signals)
    for strategy in strategies:
        if strategy["id"] not in strategies_with_signals:
            analysis["strategies_without_signals"].append({
                "id": strategy["id"],
                "name": strategy.get("name"),
                "symbols": strategy.get("symbols", [])
            })

    # Check if we're during market hours but have zero signals across all strategies
    now = datetime.now()
    if 9 <= now.hour < 16 and now.weekday() < 5:  # Market hours
        if len(signals) == 0 and len(strategies) > 0:
            analysis["anomalies"].append({
                "type": "NO_SIGNALS_DURING_MARKET_HOURS",
                "severity": "HIGH",
                "message": f"Market is open but no signals detected from {len(strategies)} active strategies"
            })

    return analysis


# ============================================================================
# Main Monitoring Loop
# ============================================================================

def run_health_check() -> Dict[str, Any]:
    """Run a complete health check."""
    log_message("=" * 80)
    log_message("Running health check...")

    # Get data
    strategies = get_active_strategies()
    signals = get_signals_today()

    log_message(f"Active strategies: {len(strategies)}")
    log_message(f"Signals today: {len(signals)}")

    # Check each strategy
    strategy_health = []
    unhealthy_count = 0

    for strategy in strategies:
        health = check_strategy_health(strategy)
        strategy_health.append(health)

        if health["status"] == "unhealthy":
            unhealthy_count += 1
            log_message(f"⚠ UNHEALTHY: {health['strategy_name']}", "WARNING")
            for issue in health["issues"]:
                log_message(f"  - {issue}", "WARNING")

    # Analyze signal patterns
    signal_analysis = analyze_signal_patterns(strategies, signals)

    # Report anomalies
    if signal_analysis["anomalies"]:
        for anomaly in signal_analysis["anomalies"]:
            log_message(f"🚨 ANOMALY [{anomaly['severity']}]: {anomaly['message']}", "WARNING")

    # Generate report
    report = {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total_strategies": len(strategies),
            "healthy_strategies": len(strategies) - unhealthy_count,
            "unhealthy_strategies": unhealthy_count,
            "signals_today": len(signals),
            "anomalies_detected": len(signal_analysis["anomalies"])
        },
        "strategy_health": strategy_health,
        "signal_analysis": signal_analysis
    }

    save_report(report)

    log_message(f"Health check complete: {len(strategies) - unhealthy_count}/{len(strategies)} healthy")
    log_message("=" * 80)

    return report


def monitor_loop():
    """Main monitoring loop."""
    log_message("\n" + "=" * 80)
    log_message("SIGNAL GENERATION MONITOR STARTED")
    log_message("=" * 80)
    log_message(f"Monitoring interval: {CHECK_INTERVAL} seconds")
    log_message(f"Log file: {LOG_FILE}")
    log_message(f"Report file: {REPORT_FILE}")
    log_message("")

    iteration = 0

    try:
        while True:
            iteration += 1
            log_message(f"\n--- Check #{iteration} ---")

            # Run health check
            report = run_health_check()

            # Alert if critical issues
            if report["summary"]["unhealthy_strategies"] > 0:
                log_message(f"⚠ {report['summary']['unhealthy_strategies']} strategies need attention!", "WARNING")

            if report["summary"]["anomalies_detected"] > 0:
                log_message(f"🚨 {report['summary']['anomalies_detected']} anomalies detected!", "ERROR")

            # Wait for next check
            log_message(f"Next check in {CHECK_INTERVAL} seconds...")
            time.sleep(CHECK_INTERVAL)

    except KeyboardInterrupt:
        log_message("\n" + "=" * 80)
        log_message("Monitor stopped by user")
        log_message("=" * 80)
    except Exception as e:
        log_message(f"Monitor crashed: {e}", "ERROR")
        raise


# ============================================================================
# Entry Point
# ============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("SIGNAL GENERATION MONITOR")
    print("=" * 80)
    print(f"Backend: {BACKEND_URL}")
    print(f"Check interval: {CHECK_INTERVAL} seconds")
    print(f"Log file: {LOG_FILE}")
    print(f"Report file: {REPORT_FILE}")
    print("\nPress Ctrl+C to stop")
    print("=" * 80 + "\n")

    try:
        monitor_loop()
    except Exception as e:
        print(f"\n✗ Monitor error: {e}")
        sys.exit(1)
