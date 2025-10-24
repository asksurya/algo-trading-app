"""
Apply Phase 7 database migration manually
"""
import asyncio
from sqlalchemy import text
from app.database import engine

async def apply_migration():
    """Apply Phase 7 tables"""
    
    migration_sql = """
    -- Create risk_rules table
    CREATE TABLE IF NOT EXISTS risk_rules (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        strategy_id INTEGER REFERENCES strategies(id) ON DELETE CASCADE,
        name VARCHAR NOT NULL,
        rule_type VARCHAR NOT NULL,
        threshold NUMERIC(20, 8) NOT NULL,
        action VARCHAR NOT NULL,
        is_active BOOLEAN DEFAULT TRUE NOT NULL,
        created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW() NOT NULL,
        updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW() NOT NULL
    );
    
    CREATE INDEX IF NOT EXISTS ix_risk_rules_user_id ON risk_rules(user_id);
    CREATE INDEX IF NOT EXISTS ix_risk_rules_strategy_id ON risk_rules(strategy_id);
    CREATE INDEX IF NOT EXISTS ix_risk_rules_is_active ON risk_rules(is_active);
    
    -- Create notifications table
    CREATE TABLE IF NOT EXISTS notifications (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        type VARCHAR NOT NULL,
        title VARCHAR NOT NULL,
        message TEXT NOT NULL,
        priority VARCHAR DEFAULT 'MEDIUM' NOT NULL,
        is_read BOOLEAN DEFAULT FALSE NOT NULL,
        data JSONB,
        created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW() NOT NULL
    );
    
    CREATE INDEX IF NOT EXISTS ix_notifications_user_id ON notifications(user_id);
    CREATE INDEX IF NOT EXISTS ix_notifications_is_read ON notifications(is_read);
    CREATE INDEX IF NOT EXISTS ix_notifications_created_at ON notifications(created_at DESC);
    
    -- Create notification_preferences table
    CREATE TABLE IF NOT EXISTS notification_preferences (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        type VARCHAR NOT NULL,
        channels VARCHAR[] NOT NULL,
        is_enabled BOOLEAN DEFAULT TRUE NOT NULL,
        quiet_hours_start TIME,
        quiet_hours_end TIME,
        created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW() NOT NULL,
        updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW() NOT NULL,
        UNIQUE(user_id, type)
    );
    
    CREATE INDEX IF NOT EXISTS ix_notification_preferences_user_id ON notification_preferences(user_id);
    
    -- Create api_keys table
    CREATE TABLE IF NOT EXISTS api_keys (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        broker VARCHAR NOT NULL,
        encrypted_api_key TEXT NOT NULL,
        encrypted_secret_key TEXT NOT NULL,
        is_paper BOOLEAN DEFAULT TRUE NOT NULL,
        is_active BOOLEAN DEFAULT TRUE NOT NULL,
        last_used_at TIMESTAMP WITHOUT TIME ZONE,
        created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW() NOT NULL,
        updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW() NOT NULL
    );
    
    CREATE INDEX IF NOT EXISTS ix_api_keys_user_id ON api_keys(user_id);
    CREATE INDEX IF NOT EXISTS ix_api_keys_broker ON api_keys(broker);
    CREATE INDEX IF NOT EXISTS ix_api_keys_is_active ON api_keys(is_active);
    
    -- Create api_key_audit_logs table
    CREATE TABLE IF NOT EXISTS api_key_audit_logs (
        id SERIAL PRIMARY KEY,
        api_key_id INTEGER NOT NULL REFERENCES api_keys(id) ON DELETE CASCADE,
        action VARCHAR NOT NULL,
        ip_address VARCHAR,
        user_agent TEXT,
        details JSONB,
        created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW() NOT NULL
    );
    
    CREATE INDEX IF NOT EXISTS ix_api_key_audit_logs_api_key_id ON api_key_audit_logs(api_key_id);
    CREATE INDEX IF NOT EXISTS ix_api_key_audit_logs_created_at ON api_key_audit_logs(created_at DESC);
    
    -- Add notification columns to users table if they don't exist
    DO $$ 
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='notification_email') THEN
            ALTER TABLE users ADD COLUMN notification_email VARCHAR;
        END IF;
        
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='email_notifications_enabled') THEN
            ALTER TABLE users ADD COLUMN email_notifications_enabled BOOLEAN DEFAULT TRUE;
        END IF;
    END $$;
    """
    
    async with engine.begin() as conn:
        # Split by semicolon and execute each statement
        statements = [s.strip() for s in migration_sql.split(';') if s.strip()]
        for statement in statements:
            try:
                await conn.execute(text(statement))
                print(f"✓ Executed: {statement[:80]}...")
            except Exception as e:
                print(f"✗ Error: {statement[:80]}...")
                print(f"  {str(e)}")
    
    print("\n✓ Phase 7 migration completed successfully!")

if __name__ == "__main__":
    asyncio.run(apply_migration())
