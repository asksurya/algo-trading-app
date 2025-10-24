#!/usr/bin/env python3
"""
API Integration Test Script
Tests all main API endpoints with real data to verify frontend integration
"""

import requests
import json
from typing import Optional

API_BASE = "http://localhost:8000"
API_V1 = f"{API_BASE}/api/v1"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_success(message: str):
    print(f"{Colors.GREEN}✓{Colors.END} {message}")

def print_error(message: str):
    print(f"{Colors.RED}✗{Colors.END} {message}")

def print_info(message: str):
    print(f"{Colors.BLUE}ℹ{Colors.END} {message}")

def print_section(message: str):
    print(f"\n{Colors.YELLOW}{'='*60}{Colors.END}")
    print(f"{Colors.YELLOW}{message}{Colors.END}")
    print(f"{Colors.YELLOW}{'='*60}{Colors.END}")

class APITester:
    def __init__(self):
        self.token: Optional[str] = None
        self.headers = {"Content-Type": "application/json"}
        self.test_user = {
            "email": "apitest@example.com",
            "password": "TestPass123!"
        }
        self.created_strategy_id: Optional[str] = None

    def set_auth_token(self, token: str):
        self.token = token
        self.headers["Authorization"] = f"Bearer {token}"

    def test_register_or_login(self) -> bool:
        print_section("Testing Authentication")
        
        # Try to login first
        try:
            response = requests.post(
                f"{API_V1}/auth/login",
                json=self.test_user
            )
            
            if response.status_code == 200:
                data = response.json()
                self.set_auth_token(data["access_token"])
                print_success(f"Login successful for {self.test_user['email']}")
                return True
            elif response.status_code == 401:
                # User doesn't exist, try to register
                print_info("User not found, attempting registration...")
                register_data = {
                    **self.test_user,
                    "full_name": "Test User"
                }
                response = requests.post(
                    f"{API_V1}/auth/register",
                    json=register_data
                )
                
                if response.status_code == 201:
                    print_success("User registered successfully")
                    # Now login
                    response = requests.post(
                        f"{API_V1}/auth/login",
                        json=self.test_user
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        self.set_auth_token(data["access_token"])
                        print_success(f"Login successful for {self.test_user['email']}")
                        return True
                
                print_error(f"Registration/Login failed: {response.status_code} - {response.text}")
                return False
            else:
                print_error(f"Login failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print_error(f"Authentication error: {str(e)}")
            return False

    def test_portfolio_summary(self) -> bool:
        print_section("Testing Portfolio Summary")
        try:
            response = requests.get(
                f"{API_V1}/trades/portfolio/summary",
                headers=self.headers
            )
            
            if response.status_code == 200:
                data = response.json()
                print_success("Portfolio summary retrieved")
                print_info(f"  Total Value: ${data['total_value']}")
                print_info(f"  Cash Balance: ${data['cash_balance']}")
                print_info(f"  Positions Value: ${data['positions_value']}")
                print_info(f"  Total P&L: ${data['total_pnl']}")
                print_info(f"  Active Strategies: {data['active_strategies']}")
                print_info(f"  Positions Count: {data['positions_count']}")
                return True
            else:
                print_error(f"Failed to get portfolio: {response.status_code}")
                return False
        except Exception as e:
            print_error(f"Portfolio error: {str(e)}")
            return False

    def test_list_strategies(self) -> bool:
        print_section("Testing List Strategies")
        try:
            response = requests.get(
                f"{API_V1}/strategies",
                headers=self.headers
            )
            
            if response.status_code == 200:
                data = response.json()
                print_success(f"Listed {len(data)} strategies")
                for strategy in data[:3]:  # Show first 3
                    print_info(f"  - {strategy['name']} ({strategy['strategy_type']}) - {'Active' if strategy['is_active'] else 'Inactive'}")
                return True
            else:
                print_error(f"Failed to list strategies: {response.status_code}")
                return False
        except Exception as e:
            print_error(f"List strategies error: {str(e)}")
            return False

    def test_create_strategy(self) -> bool:
        print_section("Testing Create Strategy")
        try:
            new_strategy = {
                "name": "Test API Integration Strategy",
                "description": "Created via API integration test",
                "strategy_type": "momentum",
                "parameters": {
                    "lookback_period": 20,
                    "threshold": 0.02
                },
                "tickers": ["AAPL", "MSFT", "GOOGL"]
            }
            
            response = requests.post(
                f"{API_V1}/strategies",
                headers=self.headers,
                json=new_strategy
            )
            
            if response.status_code == 201:
                data = response.json()
                self.created_strategy_id = data['id']
                print_success(f"Strategy created with ID: {self.created_strategy_id}")
                print_info(f"  Name: {data['name']}")
                print_info(f"  Type: {data['strategy_type']}")
                print_info(f"  Active: {data['is_active']}")
                return True
            else:
                print_error(f"Failed to create strategy: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print_error(f"Create strategy error: {str(e)}")
            return False

    def test_update_strategy(self) -> bool:
        if not self.created_strategy_id:
            print_error("No strategy ID to update")
            return False
            
        print_section("Testing Update Strategy")
        try:
            update_data = {
                "description": "Updated description via API test",
                "is_active": True
            }
            
            response = requests.put(
                f"{API_V1}/strategies/{self.created_strategy_id}",
                headers=self.headers,
                json=update_data
            )
            
            if response.status_code == 200:
                data = response.json()
                print_success("Strategy updated successfully")
                print_info(f"  Description: {data['description']}")
                print_info(f"  Active: {data['is_active']}")
                return True
            else:
                print_error(f"Failed to update strategy: {response.status_code}")
                return False
        except Exception as e:
            print_error(f"Update strategy error: {str(e)}")
            return False

    def test_list_trades(self) -> bool:
        print_section("Testing List Trades")
        try:
            response = requests.get(
                f"{API_V1}/trades",
                headers=self.headers
            )
            
            if response.status_code == 200:
                data = response.json()
                print_success(f"Listed {len(data)} trades")
                for trade in data[:3]:  # Show first 3
                    print_info(f"  - {trade['ticker']} {trade['trade_type'].upper()} {trade['quantity']} @ {trade.get('price', 'Market')} - {trade['status']}")
                return True
            else:
                print_error(f"Failed to list trades: {response.status_code}")
                return False
        except Exception as e:
            print_error(f"List trades error: {str(e)}")
            return False

    def test_trading_statistics(self) -> bool:
        print_section("Testing Trading Statistics")
        try:
            response = requests.get(
                f"{API_V1}/trades/statistics/summary",
                headers=self.headers
            )
            
            if response.status_code == 200:
                data = response.json()
                print_success("Trading statistics retrieved")
                print_info(f"  Total Trades: {data['total_trades']}")
                print_info(f"  Winning Trades: {data['winning_trades']}")
                print_info(f"  Losing Trades: {data['losing_trades']}")
                print_info(f"  Win Rate: {data['win_rate']:.2f}%")
                print_info(f"  Total P&L: ${data['total_pnl']}")
                return True
            else:
                print_error(f"Failed to get statistics: {response.status_code}")
                return False
        except Exception as e:
            print_error(f"Statistics error: {str(e)}")
            return False

    def test_current_positions(self) -> bool:
        print_section("Testing Current Positions")
        try:
            response = requests.get(
                f"{API_V1}/trades/positions/current",
                headers=self.headers
            )
            
            if response.status_code == 200:
                data = response.json()
                print_success(f"Listed {len(data)} open positions")
                for position in data[:3]:  # Show first 3
                    print_info(f"  - {position['ticker']}: {position['quantity']} shares @ ${position['avg_entry_price']}")
                return True
            else:
                print_error(f"Failed to get positions: {response.status_code}")
                return False
        except Exception as e:
            print_error(f"Positions error: {str(e)}")
            return False

    def test_delete_strategy(self) -> bool:
        if not self.created_strategy_id:
            print_error("No strategy ID to delete")
            return False
            
        print_section("Testing Delete Strategy")
        try:
            response = requests.delete(
                f"{API_V1}/strategies/{self.created_strategy_id}",
                headers=self.headers
            )
            
            if response.status_code == 204:
                print_success("Strategy deleted successfully")
                return True
            else:
                print_error(f"Failed to delete strategy: {response.status_code}")
                return False
        except Exception as e:
            print_error(f"Delete strategy error: {str(e)}")
            return False

    def run_all_tests(self):
        print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
        print(f"{Colors.BLUE}API Integration Test Suite{Colors.END}")
        print(f"{Colors.BLUE}{'='*60}{Colors.END}")
        
        results = []
        
        # Authentication
        if not self.test_register_or_login():
            print_error("\nAuthentication failed. Cannot continue tests.")
            return
        
        # Portfolio & Dashboard
        results.append(("Portfolio Summary", self.test_portfolio_summary()))
        
        # Strategies
        results.append(("List Strategies", self.test_list_strategies()))
        results.append(("Create Strategy", self.test_create_strategy()))
        results.append(("Update Strategy", self.test_update_strategy()))
        
        # Trades & Statistics
        results.append(("List Trades", self.test_list_trades()))
        results.append(("Trading Statistics", self.test_trading_statistics()))
        results.append(("Current Positions", self.test_current_positions()))
        
        # Cleanup
        results.append(("Delete Strategy", self.test_delete_strategy()))
        
        # Summary
        print_section("Test Results Summary")
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for test_name, result in results:
            status = f"{Colors.GREEN}PASS{Colors.END}" if result else f"{Colors.RED}FAIL{Colors.END}"
            print(f"  {status} - {test_name}")
        
        print(f"\n{Colors.BLUE}Overall: {passed}/{total} tests passed{Colors.END}")
        
        if passed == total:
            print(f"{Colors.GREEN}✓ All tests passed! API integration is working correctly.{Colors.END}\n")
        else:
            print(f"{Colors.YELLOW}⚠ Some tests failed. Review the errors above.{Colors.END}\n")

if __name__ == "__main__":
    tester = APITester()
    tester.run_all_tests()
