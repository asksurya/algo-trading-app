#!/usr/bin/env python3
"""
Create missing Strategy records for existing LiveStrategy references.

This script backfills the strategies table with the three strategy types
that are referenced by live_strategies but don't exist in the database.
"""
import sys
import json
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Strategy IDs from live_strategies table
STRATEGY_DEFINITIONS = [
    {
        "id": "11c2c8c4-6226-4ca3-aaf3-48031fd35d6f",
        "user_id": "a372c823-b8c5-4733-9763-73721763c4df",
        "name": "Keltner Channel Strategy",
        "description": "Keltner Channel breakout and mean reversion strategy using ATR-based bands",
        "strategy_type": "Keltner_Channel",
        "parameters": {
            "ema_period": 20,
            "atr_period": 10,
            "atr_multiplier": 2.0,
            "mode": "breakout"
        },
        "is_active": True,
        "is_backtested": True
    },
    {
        "id": "20cf3a9c-ac65-487a-9bdd-d27246b963ea",
        "user_id": "a372c823-b8c5-4733-9763-73721763c4df",
        "name": "Donchian Channel Strategy",
        "description": "Donchian Channel breakout strategy using price highs/lows",
        "strategy_type": "Donchian_Channel",
        "parameters": {
            "channel_period": 20,
            "exit_period": 10,
            "mode": "breakout"
        },
        "is_active": True,
        "is_backtested": True
    },
    {
        "id": "cce38db3-605f-4462-83fe-a3a31fba10ae",
        "user_id": "a372c823-b8c5-4733-9763-73721763c4df",
        "name": "Ichimoku Cloud Strategy",
        "description": "Ichimoku Cloud trend-following strategy with multiple timeframes",
        "strategy_type": "Ichimoku_Cloud",
        "parameters": {
            "tenkan_period": 9,
            "kijun_period": 26,
            "senkou_b_period": 52,
            "mode": "trend_following"
        },
        "is_active": True,
        "is_backtested": True
    }
]


def main():
    # Connect to database
    db_url = "sqlite:///../data/trading_state.db"
    engine = create_engine(db_url)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    try:
        print("Creating missing Strategy records...")
        print("=" * 80)

        for strategy_def in STRATEGY_DEFINITIONS:
            # Check if strategy already exists
            result = session.execute(
                text("SELECT COUNT(*) FROM strategies WHERE id = :id"),
                {"id": strategy_def["id"]}
            )
            count = result.scalar()

            if count > 0:
                print(f"✓ Strategy {strategy_def['name']} already exists (ID: {strategy_def['id']})")
                continue

            # Insert strategy
            now = datetime.utcnow().isoformat()
            session.execute(
                text("""
                    INSERT INTO strategies (
                        id, user_id, name, description, strategy_type,
                        parameters, is_active, is_backtested,
                        created_at, updated_at
                    ) VALUES (
                        :id, :user_id, :name, :description, :strategy_type,
                        :parameters, :is_active, :is_backtested,
                        :created_at, :updated_at
                    )
                """),
                {
                    "id": strategy_def["id"],
                    "user_id": strategy_def["user_id"],
                    "name": strategy_def["name"],
                    "description": strategy_def["description"],
                    "strategy_type": strategy_def["strategy_type"],
                    "parameters": json.dumps(strategy_def["parameters"]),
                    "is_active": strategy_def["is_active"],
                    "is_backtested": strategy_def["is_backtested"],
                    "created_at": now,
                    "updated_at": now
                }
            )
            print(f"✓ Created Strategy: {strategy_def['name']} (ID: {strategy_def['id']})")

        session.commit()
        print("=" * 80)
        print("✅ Successfully created all missing Strategy records")
        print("\nVerification:")

        result = session.execute(text("SELECT COUNT(*) FROM strategies"))
        count = result.scalar()
        print(f"  Total strategies in database: {count}")

        return 0

    except Exception as e:
        print(f"❌ Error: {e}")
        session.rollback()
        return 1
    finally:
        session.close()


if __name__ == "__main__":
    sys.exit(main())
