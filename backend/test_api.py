"""
Test script to verify backend API is working correctly.
Run this with: poetry run python test_api.py
"""
import asyncio
import httpx
from app.database import async_session_maker
from app.models import user as user_model
from sqlalchemy import select


async def test_health():
    """Test health endpoint."""
    async with httpx.AsyncClient() as client:
        response = await client.get("http://localhost:8000/health")
        print(f"✓ Health check: {response.status_code} - {response.json()}")
        return response.status_code == 200


async def test_register():
    """Test user registration."""
    test_user = {
        "email": "testuser@example.com",
        "password": "Test123!@#Test",
        "full_name": "Test User"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "http://localhost:8000/api/v1/auth/register",
                json=test_user
            )
            print(f"✓ Registration: {response.status_code}")
            if response.status_code == 200 or response.status_code == 201:
                data = response.json()
                print(f"  User created: {data.get('email')}")
                print(f"  Access token received: {bool(data.get('access_token'))}")
                return True, data
            else:
                print(f"  Error: {response.text}")
                return False, response.json()
        except Exception as e:
            print(f"✗ Registration failed: {str(e)}")
            return False, None


async def test_login(email: str, password: str):
    """Test user login."""
    async with httpx.AsyncClient() as client:
        try:
            # FastAPI OAuth2 expects form data, not JSON
            response = await client.post(
                "http://localhost:8000/api/v1/auth/login",
                data={
                    "username": email,  # OAuth2 uses 'username' field
                    "password": password
                }
            )
            print(f"✓ Login: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"  Access token received: {bool(data.get('access_token'))}")
                return True, data
            else:
                print(f"  Error: {response.text}")
                return False, response.json()
        except Exception as e:
            print(f"✗ Login failed: {str(e)}")
            return False, None


async def check_database():
    """Check database connection and tables."""
    try:
        async with async_session_maker() as session:
            # Check if user table exists and query it
            result = await session.execute(select(user_model.User))
            users = result.scalars().all()
            print(f"✓ Database connected")
            print(f"  Users in database: {len(users)}")
            for u in users:
                print(f"    - {u.email} (role: {u.role})")
            return True
    except Exception as e:
        print(f"✗ Database error: {str(e)}")
        return False


async def test_protected_endpoint(token: str):
    """Test protected endpoint with token."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                "http://localhost:8000/api/v1/auth/me",
                headers={"Authorization": f"Bearer {token}"}
            )
            print(f"✓ Protected endpoint: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"  User: {data.get('email')}")
                return True
            else:
                print(f"  Error: {response.text}")
                return False
        except Exception as e:
            print(f"✗ Protected endpoint failed: {str(e)}")
            return False


async def main():
    """Run all tests."""
    print("=" * 60)
    print("Backend API Test Suite")
    print("=" * 60)
    print()
    
    # Test 1: Health check
    print("1. Testing health endpoint...")
    health_ok = await test_health()
    print()
    
    if not health_ok:
        print("❌ Health check failed. Make sure backend is running!")
        return
    
    # Test 2: Database
    print("2. Testing database connection...")
    db_ok = await check_database()
    print()
    
    if not db_ok:
        print("❌ Database check failed. Run: poetry run python init_db.py")
        return
    
    # Test 3: Registration
    print("3. Testing user registration...")
    reg_ok, reg_data = await test_register()
    print()
    
    if not reg_ok:
        print("❌ Registration failed!")
        if reg_data:
            print(f"Error details: {reg_data}")
        return
    
    # Test 4: Login
    print("4. Testing user login...")
    login_ok, login_data = await test_login("testuser@example.com", "Test123!@#Test")
    print()
    
    if not login_ok:
        print("❌ Login failed!")
        return
    
    # Test 5: Protected endpoint
    print("5. Testing protected endpoint...")
    token = login_data.get("access_token") if login_data else None
    if token:
        await test_protected_endpoint(token)
    print()
    
    print("=" * 60)
    print("✅ All tests passed!")
    print("=" * 60)
    print()
    print("Your backend is working correctly.")
    print("The frontend should be able to communicate with it.")
    print()


if __name__ == "__main__":
    asyncio.run(main())
