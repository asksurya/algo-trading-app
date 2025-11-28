# 🚀 Algorithmic Trading Platform - Quick Start Guide

**Platform Status:** ✅ **READY FOR USE**  
**Last Tested:** 2025-11-27  
**Version:** 1.0.0

---

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Quick Start (5 Minutes)](#quick-start-5-minutes)
3. [Development Setup](#development-setup)
4. [Docker Deployment](#docker-deployment)
5. [Running Tests](#running-tests)
6. [Using the Platform](#using-the-platform)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software
- **Docker & Docker Compose** (v20+)
- **Python** 3.12+
- **Node.js** 20+
- **Git**

### API Keys (For Live Trading)
- **Alpaca API Key** (Free paper trading account)
  - Sign up at: https://alpaca.markets/
  - Get API keys from dashboard

---

## Quick Start (5 Minutes)

### Option 1: Docker (Recommended for Production)

```bash
# 1. Clone and navigate to project
cd /Users/ashwin/Desktop/algo-trading-app

# 2. Start all services with Docker
docker-compose up -d

# 3. Wait 30 seconds for health checks, then verify
docker-compose ps

# 4. Access the platform
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
# Frontend: http://localhost:3002
```

**Expected Output:**
```
NAME                    STATUS
algo-trading-postgres   Up (healthy)
algo-trading-redis      Up (healthy)
algo-trading-api        Up (healthy)
algo-trading-frontend   Up
```

### Option 2: Local Development

```bash
# 1. Start Backend
cd backend
pip install -r ../requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 2. Start Frontend (new terminal)
cd frontend
npm install
npm run dev

# 3. Access locally
# Backend: http://localhost:8000
# Frontend: http://localhost:3000
```

---

## Development Setup

### 1. Backend Setup

```bash
# Navigate to backend
cd backend

# Install dependencies
pip install -r ../requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your Alpaca API keys:
# ALPACA_API_KEY=your_key_here
# ALPACA_SECRET_KEY=your_secret_here

# Run database migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Backend will be available at:**
- API: `http://localhost:8000`
- Interactive docs: `http://localhost:8000/docs`
- Alternative docs: `http://localhost:8000/redoc`

### 2. Frontend Setup

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Configure environment
cp .env.local.example .env.local
# Default values work for local development

# Start development server
npm run dev
```

**Frontend will be available at:** `http://localhost:3000`

---

## Docker Deployment

### Full Stack with Docker Compose

```bash
# Build and start all services
docker-compose up --build -d

# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs backend
docker-compose logs frontend
docker-compose logs postgres
docker-compose logs redis

# Check service health
docker-compose ps

# Stop all services
docker-compose down

# Stop and remove volumes (clean slate)
docker-compose down -v
```

### Individual Service Commands

```bash
# Rebuild specific service
docker-compose build backend
docker-compose build frontend

# Restart specific service
docker-compose restart backend

# Execute commands in running container
docker exec -it algo-trading-api bash
docker exec algo-trading-postgres psql -U trading_user -d trading_db
```

---

## Running Tests

### Backend Tests

```bash
cd backend

# Run all tests
pytest -v

# Run with coverage
pytest --cov=app --cov-report=html --cov-report=term

# Run specific test file
pytest tests/test_auth.py -v

# Run tests matching pattern
pytest -k "test_login" -v
```

**Expected Results:**
- ✅ Overall pass rate: 90%+
- Tests: Authentication, Trading, Backtesting, Risk Management

### Frontend Tests

```bash
cd frontend

# TypeScript type checking
npm run type-check

# Linting
npm run lint

# Unit tests (Jest)
npm run test

# E2E tests (Playwright)
npm run test:e2e

# E2E with UI
npm run test:e2e:ui
```

---

## Using the Platform

### 1. First Time Setup

**Access the frontend:** `http://localhost:3000` or `http://localhost:3002` (Docker)

1. **Register an Account**
   - Click "Register" 
   - Enter email, password, and name
   - Password requirements: min 8 chars, uppercase, lowercase, number, special char

2. **Configure API Keys** (Optional, for live trading)
   - Navigate to Settings → API Keys
   - Add your Alpaca API credentials
   - Test connection

### 2. Create a Trading Strategy

```bash
# Via API (curl)
curl -X POST http://localhost:8000/api/v1/strategies \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "SMA Crossover",
    "type": "sma_crossover",
    "symbols": ["AAPL", "MSFT"],
    "parameters": {
      "short_window": 50,
      "long_window": 200
    }
  }'
```

**Via Web Interface:**
1. Go to "Strategies" in the navigation
2. Click "Create New Strategy"
3. Select strategy type (SMA Crossover, RSI, etc.)
4. Configure parameters
5. Save strategy

### 3. Run a Backtest

```bash
# Via API
curl -X POST http://localhost:8000/api/v1/backtests \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "strategy_id": "your-strategy-id",
    "symbol": "AAPL",
    "start_date": "2023-01-01",
    "end_date": "2024-01-01",
    "initial_capital": 100000
  }'
```

**Via Web Interface:**
1. Select your strategy
2. Click "Backtest"
3. Choose date range and parameters
4. Click "Run Backtest"
5. View results and metrics

### 4. Live Trading (Paper Trading)

⚠️ **Always start with paper trading!**

```bash
# Start paper trading via API
curl -X POST http://localhost:8000/api/v1/live-trading/start \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "strategy_id": "your-strategy-id",
    "paper": true,
    "symbols": ["AAPL"],
    "max_positions": 5
  }'
```

**Via Web Interface:**
1. Go to "Live Trading"
2. Select strategy
3. Ensure "Paper Trading" is enabled
4. Set risk parameters
5. Click "Start Trading"
6. Monitor in real-time

### 5. Monitor Performance

**Dashboard Features:**
- Real-time P&L
- Active positions
- Trade history
- Performance metrics
- Risk exposure

**Access:**
- Web: Navigate to "Dashboard"
- API: `GET /api/v1/dashboard`

---

## API Documentation

### Interactive API Docs

Once backend is running, visit:
- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

### Key Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/auth/register` | POST | Register new user |
| `/api/v1/auth/login` | POST | Login and get token |
| `/api/v1/strategies` | GET/POST | List/create strategies |
| `/api/v1/backtests` | POST | Run backtest |
| `/api/v1/live-trading` | POST | Start live trading |
| `/api/v1/dashboard` | GET | Get dashboard data |
| `/health` | GET | Health check |

### Authentication

All protected endpoints require a Bearer token:

```bash
# 1. Login to get token
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password"}'

# Returns: {"access_token": "eyJ...", "token_type": "bearer"}

# 2. Use token in subsequent requests
curl http://localhost:8000/api/v1/strategies \
  -H "Authorization: Bearer eyJ..."
```

---

## Troubleshooting

### Backend Issues

**Problem: "Cannot connect to database"**
```bash
# Check if PostgreSQL is running
docker ps | grep postgres
# Or for local:
psql -U trading_user -d trading_db -h localhost

# Restart database
docker-compose restart postgres
```

**Problem: "Redis connection failed"**
```bash
# Check Redis
docker exec algo-trading-redis redis-cli ping
# Should return: PONG

# Restart Redis
docker-compose restart redis
```

**Problem: "Import errors" or "Module not found"**
```bash
cd backend
pip install -r ../requirements.txt --upgrade
```

### Frontend Issues

**Problem: "Cannot connect to API"**
- Check backend is running on port 8000
- Verify `NEXT_PUBLIC_API_URL` in `.env.local`
- Check browser console for CORS errors

**Problem: "Build errors"**
```bash
cd frontend
rm -rf .next node_modules
npm install
npm run build
```

### Docker Issues

**Problem: "Port already in use"**
```bash
# Find and kill process using port
lsof -ti :8000 | xargs kill -9  # Backend
lsof -ti :3002 | xargs kill -9  # Frontend
lsof -ti :5432 | xargs kill -9  # PostgreSQL
lsof -ti :6379 | xargs kill -9  # Redis
```

**Problem: "Container won't start"**
```bash
# View container logs
docker logs algo-trading-api
docker logs algo-trading-frontend

# Rebuild from scratch
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
```

**Problem: "Health check failing"**
```bash
# Check container logs
docker-compose logs backend

# Test health endpoint manually
curl http://localhost:8000/health

# Restart service
docker-compose restart backend
```

### Test Failures

**Problem: "Tests failing with async errors"**
- Ensure pytest-asyncio is installed: `pip install pytest-asyncio`
- Check pytest.ini has `asyncio_mode = auto`

**Problem: "Database connection errors in tests"**
```bash
cd backend
rm test.db  # Remove old test database
pytest -v  # Recreate
```

---

## Environment Variables Reference

### Backend (.env)

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/trading_db

# Redis
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Alpaca Trading
ALPACA_API_KEY=your_api_key
ALPACA_SECRET_KEY=your_secret_key
ALPACA_BASE_URL=https://paper-api.alpaca.markets

# Environment
ENVIRONMENT=development  # or production
LOG_LEVEL=INFO
```

### Frontend (.env.local)

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
NEXT_PUBLIC_APP_NAME=Algo Trading Platform
```

---

## Performance Tips

### For Development
- Use local setup (faster hot-reload)
- Enable debug logging: `LOG_LEVEL=DEBUG`
- Use SQLite for quick testing: `DATABASE_URL=sqlite:///./dev.db`

### For Production
- Use Docker Compose
- Enable PostgreSQL connection pooling
- Configure Redis for caching
- Set `ENVIRONMENT=production`
- Use CDN for frontend static assets

---

## Next Steps

1. **Explore Example Strategies**
   - Check `backend/app/strategies/` for built-in strategies
   - Modify parameters to suit your needs

2. **Run Your First Backtest**
   - Use historical data from 2023-2024
   - Compare different strategy parameters
   - Analyze performance metrics

3. **Paper Trade**
   - Start with $10,000 virtual capital
   - Test strategies in real-time
   - Monitor for 1-2 weeks before going live

4. **Customize**
   - Create custom strategies
   - Add new indicators
   - Integrate additional data sources

---

## Support & Resources

- **Documentation:** See `/backend/README.md` and `/frontend/README.md`
- **Test Results:** See `TESTING_COMPLETE.md`
- **API Reference:** `http://localhost:8000/docs`
- **Logs:** `docker-compose logs -f`

---

**Ready to Trade! 🚀**

For questions or issues, check the troubleshooting section or review the logs.
