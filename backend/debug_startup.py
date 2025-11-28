import os
import sys
import asyncio
from app.core.config import settings

print(f"Checking environment...")
print(f"DATABASE_URL: {settings.DATABASE_URL}")
print(f"REDIS_URL: {settings.REDIS_URL}")

try:
    print("Attempting to import app.main...")
    from app.main import app
    print("Successfully imported app.main")
except Exception as e:
    print(f"Failed to import app.main: {e}")
    sys.exit(1)

async def test_startup():
    print("Testing startup events...")
    try:
        # Simulate lifespan startup
        async with app.router.lifespan_context(app):
            print("Lifespan startup successful")
    except Exception as e:
        print(f"Lifespan startup failed: {e}")
        # check if it is redis connection error
        if "redis" in str(e).lower() or "connection refused" in str(e).lower():
            print("CRITICAL: Redis connection failed. Ensure Redis is running.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(test_startup())
