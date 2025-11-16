# Debugging Guide - Troubleshooting Registration Issues

This guide will help you identify and fix any issues with the application.

## Step-by-Step Debugging Process

### Step 1: Verify Backend is Running

```bash
cd backend

# Check if backend is running
curl http://localhost:8000/health

# Expected output:
# {"status":"healthy","environment":"development"}
```

**If this fails:**
- Backend is not running
- Start it with: `poetry run uvicorn app.main:app --reload`

### Step 2: Test Backend API Directly

Run the comprehensive test script:

```bash
cd backend
poetry run python test_api.py
```

**This will test:**
1. Health endpoint
2. Database connection
3. User registration
4. User login
5. Protected endpoints

**If any test fails**, the script will show you exactly what's wrong.

### Step 3: Check Database Tables

```bash
cd backend

# Check if tables exist
poetry run python -c "
import asyncio
from app.database import engine, Base
from app.models import user, strategy, trade

async def check():
    async with engine.begin() as conn:
        tables = await conn.run_sync(lambda sync_conn: Base.metadata.tables.keys())
        print('Tables:', list(tables))

asyncio.run(check())
"
```

**Expected output:**
```
Tables: ['users', 'strategies', 'strategy_tickers', 'trades', 'positions']
```

**If tables are missing:**
```bash
poetry run python init_db.py
```

### Step 4: Test Registration via curl

```bash
# Test registration endpoint directly
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "Test123!@#Test",
    "full_name": "Test User"
  }'
```

**Expected response (200 or 201):**
```json
{
  "id": 1,
  "email": "test@example.com",
  "full_name": "Test User",
  "role": "user",
  "is_active": true,
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

**Common errors:**

1. **422 Validation Error**:
   - Password too weak
   - Email format invalid
   - Missing required fields

2. **400 Email already registered**:
   - User already exists
   - Try different email

3. **500 Internal Server Error**:
   - Database connection issue
   - Check backend logs

### Step 5: Check Frontend Configuration

```bash
cd frontend

# Verify .env.local exists
cat .env.local

# Should show:
# NEXT_PUBLIC_API_URL=http://localhost:8000
# NEXT_PUBLIC_WS_URL=ws://localhost:8000
# NEXT_PUBLIC_APP_NAME=Algo Trading Platform
```

**If file doesn't exist:**
```bash
cp .env.local.example .env.local
```

### Step 6: Check Frontend Logs

Open browser console (F12) and check for errors:

**Common issues:**

1. **Network Error / CORS**:
   ```
   Access to fetch at 'http://localhost:8000' blocked by CORS
   ```
   - Backend not running
   - CORS misconfigured

2. **404 Not Found**:
   ```
   POST http://localhost:8000/api/v1/auth/register 404
   ```
   - Backend not running on port 8000
   - Wrong API URL in .env.local

3. **Connection Refused**:
   ```
   Failed to fetch
   ```
   - Backend not running

### Step 7: Test Frontend API Client

Create a test file to check frontend API client:

```bash
cd frontend

# Create test file
cat > test-api.js << 'EOF'
const axios = require('axios');

async function test() {
  try {
    const response = await axios.post(
      'http://localhost:8000/api/v1/auth/register',
      {
        email: 'frontendtest@example.com',
        password: 'Test123!@#Test',
        full_name: 'Frontend Test'
      }
    );
    console.log('✓ Success:', response.data);
  } catch (error) {
    console.log('✗ Error:', error.response?.data || error.message);
  }
}

test();
EOF

# Run test
node test-api.js
```

### Step 8: Check Backend Logs

While the frontend is trying to register, watch backend logs:

```bash
cd backend

# If running with uvicorn, you'll see logs in terminal
# Look for:
# - POST /api/v1/auth/register
# - Status code (200, 400, 422, 500)
# - Any error messages
```

## Common Issues and Solutions

### Issue 1: "Registration failed. Please try again."

**Possible causes:**
1. Backend not running
2. Database not initialized
3. CORS issues
4. Network error

**Solution:**
```bash
# 1. Ensure backend is running
cd backend
poetry run uvicorn app.main:app --reload

# 2. Ensure database is initialized
poetry run python init_db.py

# 3. Test with curl (see Step 4)

# 4. Check browser console for actual error
```

### Issue 2: Password validation errors

**Error**: "Password must be at least 8 characters"

**Solution**: Use strong password with:
- At least 8 characters
- Uppercase letter (A-Z)
- Lowercase letter (a-z)
- Number (0-9)
- Special character (!@#$%^&*)

**Example**: `Test123!@#Test`

### Issue 3: Email already exists

**Error**: "Email already registered"

**Solution**: Use different email or clear database:

```bash
cd backend

# Delete existing user
poetry run python -c "
import asyncio
from app.database import async_session_maker
from app.models.user import User
from sqlalchemy import delete

async def clear():
    async with async_session_maker() as session:
        await session.execute(delete(User).where(User.email == 'test@example.com'))
        await session.commit()
        print('User deleted')

asyncio.run(clear())
"
```

### Issue 4: CORS errors

**Error**: "blocked by CORS policy"

**Check**:
```bash
cd backend
cat .env | grep ALLOWED_ORIGINS

# Should show:
# ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001
```

**Fix**: Make sure frontend URL is in ALLOWED_ORIGINS

### Issue 5: Database connection errors

**Error**: "Connection refused" or "database does not exist"

**Solution**:
```bash
# Check PostgreSQL is running
brew services list | grep postgresql

# If not running:
brew services start postgresql@15

# Create database if missing:
createdb algo_trading

# Initialize tables:
cd backend
poetry run python init_db.py
```

## Complete Test Procedure

Follow these steps in order:

```bash
# Terminal 1: Backend
cd backend
poetry install
poetry run python init_db.py
poetry run python test_api.py  # Should pass all tests
poetry run uvicorn app.main:app --reload

# Terminal 2: Frontend
cd frontend
npm install
npm run dev

# Terminal 3: Test with curl
curl http://localhost:8000/health
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"curltest@example.com","password":"Test123!@#Test"}'

# Browser: Open http://localhost:3000
# - Open DevTools (F12)
# - Go to Network tab
# - Try to register
# - Check for errors in Console and Network tabs
```

## Getting More Information

### Enable Detailed Backend Logs

Edit `backend/.env`:
```
LOG_LEVEL=DEBUG
```

Restart backend to see detailed logs.

### Check Frontend Build

```bash
cd frontend
npm run build

# If build fails, fix errors before running dev server
```

### Test API Documentation

Visit http://localhost:8000/api/docs

Try registering a user directly from Swagger UI:
1. Click on `/api/v1/auth/register`
2. Click "Try it out"
3. Fill in the request body
4. Click "Execute"
5. Check response

## Still Having Issues?

If you've tried everything above and registration still fails:

1. **Check the exact error message** in browser console
2. **Check backend terminal logs** for errors
3. **Run the test script**: `poetry run python test_api.py`
4. **Verify all services are running**:
   - PostgreSQL: `brew services list`
   - Redis: `brew services list`
   - Backend: `curl http://localhost:8000/health`
   - Frontend: Open http://localhost:3000

## Quick Reference

### Start Everything
```bash
# Terminal 1
cd backend && poetry run uvicorn app.main:app --reload

# Terminal 2
cd frontend && npm run dev
```

### Test Everything
```bash
# Backend API test
cd backend && poetry run python test_api.py

# Manual test
curl http://localhost:8000/health
```

### Reset Everything
```bash
# Stop services
pkill -f uvicorn
pkill -f "next dev"

# Clear database (optional)
cd backend
poetry run python -c "
import asyncio
from app.database import engine, Base

async def reset():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    print('Database reset')

asyncio.run(reset())
"

# Restart
cd backend && poetry run uvicorn app.main:app --reload &
cd frontend && npm run dev &
