# Quick Start Guide - Algo Trading Platform V3

**You have two options to run the backend: With Docker or Without Docker**

---

## Option 1: Run WITHOUT Docker (Recommended for Development)

This option doesn't require Docker to be running.

### Prerequisites
- Python 3.11+
- PostgreSQL 15+ (installed locally)
- Redis 7+ (installed locally)
- Node.js 20+

### Step 1: Install PostgreSQL and Redis (macOS)

```bash
# Install with Homebrew
brew install postgresql@15 redis

# Start PostgreSQL
brew services start postgresql@15

# Start Redis
brew services start redis

# Create database
createdb algo_trading
```

### Step 2: Run Backend

```bash
cd backend

# Install dependencies
poetry install

# The .env file is already created with defaults

# IMPORTANT: Initialize database tables (run once)
poetry run python init_db.py

# Start the API server
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# API will be at http://localhost:8000
# Docs at http://localhost:8000/api/docs
```

### Step 3: Run Frontend

Open a new terminal:

```bash
cd frontend

# Install dependencies (takes 1-2 minutes)
npm install

# Copy env file (already done)
# cp .env.local.example .env.local

# Start development server
npm run dev

# App will be at http://localhost:3000
```

---

## Option 2: Run WITH Docker

This requires Docker Desktop to be running.

### Prerequisites
- Docker Desktop installed and running

### Step 1: Start Docker Desktop

1. Open Docker Desktop application
2. Wait for it to fully start (whale icon in menu bar)
3. Verify: `docker ps` should work

### Step 2: Run with Docker Compose

```bash
cd backend

# The .env file is already created

# Start all services (PostgreSQL, Redis, API)
docker-compose up -d

# View logs
docker-compose logs -f api

# API will be at http://localhost:8000
# Docs at http://localhost:8000/api/docs
```

### Step 3: Run Frontend

Same as Option 1 above.

---

## Testing the Application

### 1. Backend API Test

```bash
# Health check
curl http://localhost:8000/health

# Should return: {"status":"healthy","environment":"development"}
```

### 2. Frontend Test

1. Open http://localhost:3000
2. Click "Register"
3. Create an account:
   - Email: test@example.com
   - Password: Test123!@# (must have uppercase, lowercase, number, special char)
4. You'll be redirected to the dashboard
5. Test logout and login again

### 3. API Documentation

Visit http://localhost:8000/api/docs to:
- See all 25 endpoints
- Test endpoints directly in browser
- View request/response schemas

---

## Troubleshooting

### Backend Won't Start

**Error: "Connection refused" or database errors**
- Make sure PostgreSQL is running: `brew services list`
- Make sure Redis is running: `brew services list`
- Check database exists: `psql -l | grep algo_trading`

**Error: "Port 8000 already in use"**
```bash
# Find process using port 8000
lsof -i :8000

# Kill it
kill -9 <PID>
```

### Frontend Won't Start

**Error: "npm install" fails**
```bash
# Clear npm cache
npm cache clean --force

# Delete node_modules and try again
rm -rf node_modules package-lock.json
npm install
```

**Error: "Port 3000 already in use"**
```bash
# Find process using port 3000
lsof -i :3000

# Kill it
kill -9 <PID>

# Or use a different port
npm run dev -- -p 3001
```

### TypeScript Errors in Frontend

These are normal before `npm install`:
- Run `npm install` first
- TypeScript will find all dependencies
- Errors should disappear

---

## What You Can Do Now

### Current Features ✅
- User registration
- User login/logout
- Protected dashboard
- JWT token management (automatic refresh)
- Beautiful UI

### Coming Soon (Follow NEXT_STEPS_GUIDE.md)
- Strategy management pages
- Trade execution pages
- Portfolio dashboard
- Backtesting interface
- Real-time charts

---

## Quick Commands Reference

### Backend (Without Docker)
```bash
cd backend
poetry run uvicorn app.main:app --reload  # Start server
poetry run pytest                           # Run tests (when added)
poetry run alembic upgrade head            # Run migrations (when added)
```

### Backend (With Docker)
```bash
cd backend
docker-compose up -d          # Start services
docker-compose down           # Stop services
docker-compose logs -f api    # View logs
docker-compose ps             # Check status
```

### Frontend
```bash
cd frontend
npm run dev          # Start dev server
npm run build        # Build for production
npm run start        # Start production server
npm run lint         # Lint code
npm run type-check   # Check TypeScript
```

---

## Environment Variables

The `.env` file has been created with development defaults:
- PostgreSQL: postgres/postgres @ localhost:5432
- Redis: localhost:6379
- Secret key: Development key (change in production!)
- Alpaca: Placeholder keys (add real ones to trade)

**To add your Alpaca keys** (optional for now):
1. Sign up at https://alpaca.markets (paper trading is free)
2. Get API keys from dashboard
3. Edit `backend/.env`:
   ```
   ALPACA_API_KEY=your-real-key-here
   ALPACA_SECRET_KEY=your-real-secret-here
   ```

---

## Success Checklist

- [ ] Backend running at http://localhost:8000
- [ ] Backend docs at http://localhost:8000/api/docs
- [ ] Frontend running at http://localhost:3000
- [ ] Can register a new user
- [ ] Can login with credentials
- [ ] Dashboard loads with user info
- [ ] Can logout successfully

**All checked? You're ready to build! 🚀**

---

## Next Steps

See `NEXT_STEPS_GUIDE.md` for:
- Adding more pages (strategies, trades, backtest)
- Implementing data visualization
- Connecting to real trading
- Deployment instructions

---

**Need Help?**
- Backend docs: `backend/README.md`
- Frontend docs: `frontend/README.md`
- Implementation status: `WEBAPP_V3_IMPLEMENTATION_STATUS.md`
- Next steps: `NEXT_STEPS_GUIDE.md`
