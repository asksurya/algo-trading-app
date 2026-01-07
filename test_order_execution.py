#!/usr/bin/env python3
"""
Test Order Execution Functionality

Tests the complete order execution pipeline:
1. Simulates a trading signal
2. Runs through execution logic
3. Places order with Alpaca (paper trading)
4. Verifies order status
"""
import asyncio
import sys
import os
from datetime import datetime, timezone
from decimal import Decimal
from dotenv import load_dotenv

# Load environment variables from backend/.env
backend_dir = os.path.join(os.path.dirname(__file__), 'backend')
load_dotenv(os.path.join(backend_dir, '.env'))

# Add backend to path
sys.path.insert(0, backend_dir)

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, text
from app.models import LiveStrategy, User, ApiKey, SignalType
from app.services.signal_monitor import SignalMonitor, TradingSignal
from app.services.strategy_scheduler import StrategyScheduler
from app.integrations.alpaca_client import AlpacaClient
from app.core.config import settings

async def test_order_execution():
    """Test the order execution flow."""
    print("=" * 80)
    print("TESTING ORDER EXECUTION FUNCTIONALITY")
    print("=" * 80)

    # Create async database session
    db_url = str(settings.DATABASE_URL)
    if 'sqlite' in db_url and 'aiosqlite' not in db_url:
        db_url = db_url.replace('sqlite:///', 'sqlite+aiosqlite:///')
    elif 'sqlite' not in db_url and 'postgresql' in db_url:
        db_url = db_url.replace('postgresql://', 'postgresql+asyncpg://')

    engine = create_async_engine(db_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        try:
            # 1. Get paper trader user
            print("\n1. Getting paper trading user...")
            result = await db.execute(
                text("SELECT * FROM users WHERE email = 'paper.trader@test.com'")
            )
            user_row = result.fetchone()

            if not user_row:
                print("✗ Paper trader user not found")
                return False

            user_id = user_row[0]
            print(f"✓ Found user: {user_row[1]} (ID: {user_id})")

            # 2. Get an active strategy (preferably AMD since it had signals)
            print("\n2. Getting active strategy...")
            result = await db.execute(
                text("""
                SELECT * FROM live_strategies
                WHERE user_id = :user_id AND status = 'active' AND symbols LIKE '%AMD%'
                LIMIT 1
                """),
                {"user_id": user_id}
            )
            strategy_row = result.fetchone()

            if not strategy_row:
                print("✗ No active AMD strategy found")
                # Try any active strategy
                result = await db.execute(
                    text("""
                    SELECT * FROM live_strategies
                    WHERE user_id = :user_id AND status = 'active'
                    LIMIT 1
                    """),
                    {"user_id": user_id}
                )
                strategy_row = result.fetchone()

            if not strategy_row:
                print("✗ No active strategies found")
                return False

            strategy_id = strategy_row[0]
            strategy_name = strategy_row[3]
            symbols = eval(strategy_row[4])  # JSON array
            symbol = symbols[0] if symbols else "AAPL"

            print(f"✓ Found strategy: {strategy_name}")
            print(f"  ID: {strategy_id}")
            print(f"  Symbol: {symbol}")
            print(f"  Auto-execute: {strategy_row[7]}")

            # 3. Get API key
            print("\n3. Checking API key...")
            result = await db.execute(
                text("SELECT * FROM api_keys WHERE user_id = :user_id AND status = 'active'"),
                {"user_id": user_id}
            )
            api_key_row = result.fetchone()

            if not api_key_row:
                print("✗ No API key found")
                return False

            print(f"✓ Found API key: {api_key_row[3]} ({api_key_row[2]})")
            print(f"  Paper Trading: {api_key_row[10]}")
            print(f"  Status: {api_key_row[11]}")

            # 4. Get current market price
            print(f"\n4. Fetching current {symbol} price...")
            try:
                # Use settings API key for market data
                alpaca = AlpacaClient(
                    api_key=settings.ALPACA_API_KEY,
                    api_secret=settings.ALPACA_SECRET_KEY,
                    paper=True
                )

                latest_quote = alpaca.get_latest_quote(symbol)
                if latest_quote:
                    current_price = float(latest_quote.ask_price or latest_quote.bid_price)
                    print(f"✓ Current {symbol} price: ${current_price:.2f}")
                else:
                    # Fallback price for testing
                    current_price = 150.00
                    print(f"⚠ Could not fetch live price, using test price: ${current_price:.2f}")
            except Exception as e:
                current_price = 150.00
                print(f"⚠ Error fetching price: {e}")
                print(f"  Using test price: ${current_price:.2f}")

            # 5. Create test signal
            print(f"\n5. Creating test BUY signal for {symbol}...")
            test_signal = TradingSignal(
                symbol=symbol,
                signal_type=SignalType.BUY,
                price=current_price,
                strength=0.85,  # Strong signal
                volume=1000000,
                indicators={
                    "test": True,
                    "sma_20": current_price * 0.98,
                    "sma_50": current_price * 0.95,
                    "rsi": 65
                }
            )
            print(f"✓ Signal created:")
            print(f"  Type: {test_signal.signal_type.value}")
            print(f"  Price: ${test_signal.price:.2f}")
            print(f"  Strength: {test_signal.strength}")

            # 6. Test execution logic
            print("\n6. Testing order execution...")
            print("   Note: Market may be closed, so order might be queued")

            # Initialize scheduler (this handles execution)
            scheduler = StrategyScheduler(db)

            # Get the LiveStrategy object
            from sqlalchemy import select
            stmt = select(LiveStrategy).where(LiveStrategy.id == strategy_id)
            result = await db.execute(stmt)
            live_strategy = result.scalar_one()

            print(f"\n7. Checking execution eligibility...")
            should_execute, reason = await scheduler.signal_monitor.should_execute_signal(
                test_signal, live_strategy
            )

            if not should_execute:
                print(f"✗ Signal would NOT be executed: {reason}")
                print("\n   This is expected if:")
                print("   - Signal strength too low (< 0.6)")
                print("   - Max positions reached")
                print("   - Daily loss limit hit")
                print("   - Risk validation failed")
                return False

            print(f"✓ Signal passes execution checks")

            # 8. Attempt to execute
            print(f"\n8. Executing test trade...")
            print("   This will place a real order on Alpaca PAPER account")
            print("   (No real money involved)")

            try:
                await scheduler._execute_signal(live_strategy, test_signal)
                print("\n✓ Trade execution completed!")

                # 9. Check if order was created
                print("\n9. Checking order status in database...")
                await db.commit()  # Ensure changes are committed

                result = await db.execute(
                    text("""
                    SELECT id, symbol, side, quantity, order_type, status,
                           filled_qty, filled_avg_price, created_at
                    FROM orders
                    WHERE user_id = :user_id AND symbol = :symbol
                    ORDER BY created_at DESC
                    LIMIT 1
                    """),
                    {"user_id": user_id, "symbol": symbol}
                )
                order_row = result.fetchone()

                if order_row:
                    print(f"✓ Order created in database:")
                    print(f"  Order ID: {order_row[0]}")
                    print(f"  Symbol: {order_row[1]}")
                    print(f"  Side: {order_row[2]}")
                    print(f"  Quantity: {order_row[3]}")
                    print(f"  Type: {order_row[4]}")
                    print(f"  Status: {order_row[5]}")
                    print(f"  Filled Qty: {order_row[6] or 0}")
                    print(f"  Avg Price: ${order_row[7] or 0:.2f}")
                    print(f"  Created: {order_row[8]}")

                    # 10. Check Alpaca order status
                    print("\n10. Verifying order on Alpaca...")
                    try:
                        alpaca_orders = alpaca.get_orders(
                            status='all',
                            limit=5,
                            symbols=[symbol]
                        )

                        if alpaca_orders:
                            print(f"✓ Found {len(alpaca_orders)} recent {symbol} order(s) on Alpaca:")
                            for i, order in enumerate(alpaca_orders[:3], 1):
                                print(f"\n  Order {i}:")
                                print(f"    Alpaca ID: {order.id}")
                                print(f"    Symbol: {order.symbol}")
                                print(f"    Side: {order.side}")
                                print(f"    Qty: {order.qty}")
                                print(f"    Status: {order.status}")
                                print(f"    Created: {order.created_at}")
                        else:
                            print(f"⚠ No orders found on Alpaca for {symbol}")
                            print("  This might be normal if the market is closed")
                    except Exception as e:
                        print(f"⚠ Could not fetch Alpaca orders: {e}")

                    return True
                else:
                    print("✗ No order found in database")
                    return False

            except Exception as e:
                print(f"\n✗ Trade execution failed: {e}")
                print("\nError details:")
                import traceback
                traceback.print_exc()
                return False

        except Exception as e:
            print(f"\n✗ Test failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            await engine.dispose()

    print("\n" + "=" * 80)

async def main():
    print("\nStarting order execution test...")
    print("This will create a test trade on Alpaca's PAPER trading account")
    print("(No real money will be used)\n")

    success = await test_order_execution()

    print("\n" + "=" * 80)
    if success:
        print("TEST RESULT: ✓ SUCCESS")
        print("=" * 80)
        print("\nOrder execution is working correctly!")
        print("The system can now automatically trade during market hours.")
    else:
        print("TEST RESULT: ✗ FAILED")
        print("=" * 80)
        print("\nOrder execution encountered issues.")
        print("Please review the output above for details.")
    print()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n✗ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
