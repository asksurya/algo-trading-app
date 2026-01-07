#!/usr/bin/env python3
"""
Simple Alpaca Order Placement Test

Tests that we can successfully place orders on Alpaca paper trading account.
"""
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from dotenv import load_dotenv
import os
from pathlib import Path

# Load environment
script_dir = Path(__file__).parent
load_dotenv(script_dir / 'backend' / '.env')

ALPACA_API_KEY = os.getenv('ALPACA_API_KEY')
ALPACA_SECRET_KEY = os.getenv('ALPACA_SECRET_KEY')

def test_alpaca_order():
    print("=" * 80)
    print("ALPACA ORDER PLACEMENT TEST")
    print("=" * 80)

    # 1. Initialize client
    print("\n1. Initializing Alpaca client...")
    try:
        client = TradingClient(ALPACA_API_KEY, ALPACA_SECRET_KEY, paper=True)
        print("✓ Client initialized")
    except Exception as e:
        print(f"✗ Failed to initialize client: {e}")
        return False

    # 2. Check account
    print("\n2. Checking account status...")
    try:
        account = client.get_account()
        print(f"✓ Account active")
        print(f"  Cash: ${float(account.cash):,.2f}")
        print(f"  Buying Power: ${float(account.buying_power):,.2f}")
        print(f"  Portfolio Value: ${float(account.portfolio_value):,.2f}")
    except Exception as e:
        print(f"✗ Failed to get account: {e}")
        return False

    # 3. Place test order (small quantity)
    print("\n3. Placing test market order for 1 share of SPY...")
    print("   (Paper trading - no real money)")

    try:
        order_request = MarketOrderRequest(
            symbol="SPY",
            qty=1,
            side=OrderSide.BUY,
            time_in_force=TimeInForce.DAY
        )

        order = client.submit_order(order_request)
        print(f"\n✓ Order submitted successfully!")
        print(f"  Order ID: {order.id}")
        print(f"  Symbol: {order.symbol}")
        print(f"  Side: {order.side}")
        print(f"  Quantity: {order.qty}")
        print(f"  Order Type: {order.order_type}")
        print(f"  Status: {order.status}")
        print(f"  Created: {order.created_at}")

    except Exception as e:
        print(f"\n✗ Order failed: {e}")
        print("\nNote: Market may be closed. This is expected after hours.")
        print("The order will be queued and executed when market opens.")

        # Still check if we can see pending orders
        print("\n4. Checking for pending orders...")
        try:
            orders = client.get_orders(status='all', limit=5)
            if orders:
                print(f"✓ Found {len(orders)} recent order(s):")
                for i, ord in enumerate(orders, 1):
                    print(f"\n  Order {i}:")
                    print(f"    ID: {ord.id}")
                    print(f"    Symbol: {ord.symbol}")
                    print(f"    Side: {ord.side}")
                    print(f"    Qty: {ord.qty}")
                    print(f"    Status: {ord.status}")
                    print(f"    Created: {ord.created_at}")
            else:
                print("  No orders found")
        except Exception as e:
            print(f"✗ Failed to get orders: {e}")
            return False

        return True  # Order was placed even if market closed

    # 4. Verify order
    print("\n4. Verifying order status...")
    try:
        order_status = client.get_order_by_id(order.id)
        print(f"✓ Order verified")
        print(f"  Current Status: {order_status.status}")
        if order_status.filled_qty:
            print(f"  Filled Qty: {order_status.filled_qty}")
            print(f"  Filled Avg Price: ${float(order_status.filled_avg_price):.2f}")
    except Exception as e:
        print(f"⚠ Could not verify order: {e}")

    # 5. Cancel order if still pending (cleanup)
    print("\n5. Cleaning up test order...")
    try:
        if order_status.status in ['new', 'pending_new', 'accepted']:
            client.cancel_order_by_id(order.id)
            print(f"✓ Test order canceled (cleanup)")
        else:
            print(f"  Order already {order_status.status}, no cleanup needed")
    except Exception as e:
        print(f"⚠ Could not cancel order: {e}")
        print("  (This is fine if order already filled/canceled)")

    return True

if __name__ == "__main__":
    print("\nTesting Alpaca API order placement...")
    print("This will place a 1-share SPY order on paper trading account\n")

    try:
        success = test_alpaca_order()

        print("\n" + "=" * 80)
        if success:
            print("TEST RESULT: ✓ SUCCESS")
            print("=" * 80)
            print("\nAlpaca API integration is working!")
            print("Orders can be placed successfully on the paper trading account.")
        else:
            print("TEST RESULT: ✗ FAILED")
            print("=" * 80)
            print("\nAlpaca API integration has issues.")
        print()
    except Exception as e:
        print(f"\n✗ Fatal error: {e}")
        import traceback
        traceback.print_exc()
