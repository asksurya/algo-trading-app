#!/usr/bin/env python3
"""
Comprehensive end-to-end test for Phase 7 implementation.
Tests all risk management, API key management, and notification endpoints.
"""
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

# Test results tracker
tests_passed = 0
tests_failed = 0
test_results = []

def log_test(test_name, passed, details=""):
    global tests_passed, tests_failed
    status = "✅ PASS" if passed else "❌ FAIL"
    result = f"{status}: {test_name}"
    if details:
        result += f" - {details}"
    test_results.append(result)
    print(result)
    
    if passed:
        tests_passed += 1
    else:
        tests_failed += 1


def test_endpoint(method, endpoint, expected_status, data=None, headers=None, test_name=None):
    """Generic endpoint testing function"""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, json=data, headers=headers)
        elif method == "PUT":
            response = requests.put(url, json=data, headers=headers)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers)
        else:
            log_test(test_name or endpoint, False, f"Unknown method: {method}")
            return None
        
        passed = response.status_code == expected_status
        details = f"Status: {response.status_code}"
        
        if not passed:
            try:
                error_detail = response.json()
                details += f" | Error: {error_detail}"
            except:
                details += f" | Response: {response.text[:100]}"
        
        log_test(test_name or f"{method} {endpoint}", passed, details)
        return response
        
    except Exception as e:
        log_test(test_name or endpoint, False, f"Exception: {str(e)}")
        return None


def main():
    print("=" * 80)
    print("PHASE 7 END-TO-END TESTING")
    print("=" * 80)
    print()
    
    # Step 1: Register a test user
    print("📋 Step 1: User Registration and Authentication")
    print("-" * 80)
    
    test_email = f"test_phase7_{datetime.now().timestamp()}@example.com"
    test_password = "Test123!@#"
    
    register_data = {
        "email": test_email,
        "password": test_password,
        "full_name": "Phase 7 Test User"
    }
    
    register_response = test_endpoint(
        "POST", "/api/v1/auth/register", 201, 
        data=register_data,
        test_name="Register test user"
    )
    
    if not register_response or register_response.status_code != 201:
        print("\n❌ Cannot proceed without user registration")
        return
    
    # Step 2: Login to get token
    login_data = {
        "email": test_email,
        "password": test_password
    }
    
    login_response = test_endpoint(
        "POST", "/api/v1/auth/login", 200,
        data=login_data,
        test_name="Login to get token"
    )
    
    if not login_response or login_response.status_code != 200:
        print("\n❌ Cannot proceed without authentication token")
        return
    
    token_data = login_response.json()
    token = token_data.get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    
    print(f"\n✅ Authentication successful! Token obtained.\n")
    
    # Step 3: Test Risk Rules API
    print("📋 Step 2: Risk Rules API Testing")
    print("-" * 80)
    
    # Create a risk rule
    risk_rule_data = {
        "name": "Test Max Daily Loss",
        "description": "Test rule for max daily loss",
        "rule_type": "max_daily_loss",
        "threshold_value": 500.0,
        "threshold_unit": "dollars",
        "action": "block",
        "is_active": True
    }
    
    create_rule_response = test_endpoint(
        "POST", "/api/v1/risk-rules", 201,
        data=risk_rule_data, headers=headers,
        test_name="Create risk rule"
    )
    
    rule_id = None
    if create_rule_response and create_rule_response.status_code == 201:
        rule_data = create_rule_response.json()
        rule_id = rule_data.get("data", {}).get("id") or rule_data.get("id")
    
    # List risk rules
    test_endpoint(
        "GET", "/api/v1/risk-rules", 200,
        headers=headers,
        test_name="List risk rules"
    )
    
    # Get single risk rule
    if rule_id:
        test_endpoint(
            "GET", f"/api/v1/risk-rules/{rule_id}", 200,
            headers=headers,
            test_name="Get single risk rule"
        )
        
        # Update risk rule
        update_data = {"threshold_value": 750.0}
        test_endpoint(
            "PUT", f"/api/v1/risk-rules/{rule_id}", 200,
            data=update_data, headers=headers,
            test_name="Update risk rule"
        )
    
    # Test risk rule - calculate position size
    position_calc_data = {
        "symbol": "AAPL",
        "entry_price": 150.0,
        "stop_loss": 145.0
    }
    test_endpoint(
        "POST", "/api/v1/risk-rules/calculate-position-size", 200,
        data=position_calc_data, headers=headers,
        test_name="Calculate position size"
    )
    
    # Get portfolio risk metrics
    test_endpoint(
        "GET", "/api/v1/risk-rules/portfolio-risk", 200,
        headers=headers,
        test_name="Get portfolio risk metrics"
    )
    
    print()
    
    # Step 4: Test API Key Management
    print("📋 Step 3: API Key Management Testing")
    print("-" * 80)
    
    # Create API key
    api_key_data = {
        "broker": "alpaca",
        "name": "Test Alpaca API Key",
        "description": "Test API key for Phase 7",
        "api_key": "test_key_12345",
        "api_secret": "test_secret_67890",
        "is_paper_trading": True,
        "is_default": False
    }
    
    create_key_response = test_endpoint(
        "POST", "/api/v1/api-keys", 201,
        data=api_key_data, headers=headers,
        test_name="Create API key"
    )
    
    api_key_id = None
    if create_key_response and create_key_response.status_code == 201:
        key_data = create_key_response.json()
        api_key_id = key_data.get("data", {}).get("id") or key_data.get("id")
    
    # List API keys
    test_endpoint(
        "GET", "/api/v1/api-keys", 200,
        headers=headers,
        test_name="List API keys"
    )
    
    # Get single API key
    if api_key_id:
        test_endpoint(
            "GET", f"/api/v1/api-keys/{api_key_id}", 200,
            headers=headers,
            test_name="Get single API key"
        )
        
        # Update API key
        update_key_data = {"name": "Updated Test Key"}
        test_endpoint(
            "PUT", f"/api/v1/api-keys/{api_key_id}", 200,
            data=update_key_data, headers=headers,
            test_name="Update API key"
        )
        
        # Get audit logs
        test_endpoint(
            "GET", f"/api/v1/api-keys/{api_key_id}/audit-logs", 200,
            headers=headers,
            test_name="Get API key audit logs"
        )
    
    print()
    
    # Step 5: Test Notifications API
    print("📋 Step 4: Notifications API Testing")
    print("-" * 80)
    
    # Create notification preference
    pref_data = {
        "notification_type": "order_filled",
        "channel": "in_app",
        "is_enabled": True
    }
    
    create_pref_response = test_endpoint(
        "POST", "/api/v1/notifications/preferences", 201,
        data=pref_data, headers=headers,
        test_name="Create notification preference"
    )
    
    pref_id = None
    if create_pref_response and create_pref_response.status_code == 201:
        pref_response_data = create_pref_response.json()
        pref_id = pref_response_data.get("data", {}).get("id") or pref_response_data.get("id")
    
    # List notification preferences
    test_endpoint(
        "GET", "/api/v1/notifications/preferences", 200,
        headers=headers,
        test_name="List notification preferences"
    )
    
    # List notifications
    test_endpoint(
        "GET", "/api/v1/notifications", 200,
        headers=headers,
        test_name="List notifications"
    )
    
    # Get notification stats
    test_endpoint(
        "GET", "/api/v1/notifications/stats", 200,
        headers=headers,
        test_name="Get notification stats"
    )
    
    print()
    
    # Step 6: Cleanup - Delete created resources
    print("📋 Step 5: Cleanup")
    print("-" * 80)
    
    if rule_id:
        test_endpoint(
            "DELETE", f"/api/v1/risk-rules/{rule_id}", 204,
            headers=headers,
            test_name="Delete risk rule"
        )
    
    if api_key_id:
        test_endpoint(
            "DELETE", f"/api/v1/api-keys/{api_key_id}", 204,
            headers=headers,
            test_name="Delete API key"
        )
    
    if pref_id:
        test_endpoint(
            "DELETE", f"/api/v1/notifications/preferences/{pref_id}", 204,
            headers=headers,
            test_name="Delete notification preference"
        )
    
    print()
    
    # Final Results
    print("=" * 80)
    print("TEST RESULTS SUMMARY")
    print("=" * 80)
    print(f"✅ Tests Passed: {tests_passed}")
    print(f"❌ Tests Failed: {tests_failed}")
    print(f"📊 Success Rate: {(tests_passed/(tests_passed+tests_failed)*100):.1f}%")
    print("=" * 80)
    
    if tests_failed > 0:
        print("\n⚠️  Some tests failed. Review the output above for details.")
        exit(1)
    else:
        print("\n🎉 All tests passed! Phase 7 implementation is working correctly.")
        exit(0)


if __name__ == "__main__":
    main()
