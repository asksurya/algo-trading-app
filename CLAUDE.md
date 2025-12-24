# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Algorithmic trading platform with three components:
- **FastAPI backend** (`/backend`) - REST API, WebSocket, async PostgreSQL/Redis
- **Next.js frontend** (`/frontend`) - App Router, React 19, Tailwind/shadcn-ui
- **Python CLI** (`/src`, `/pages`) - Streamlit UI, trading strategies, backtesting engine

## Build & Run Commands

### Backend (FastAPI)
```bash
cd backend
poetry install
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend (Next.js)
```bash
cd frontend
npm install
npm run dev          # Development server on port 3000
npm run build        # Production build
```

### Docker (Full Stack)
```bash
docker-compose up -d                  # Start all services
docker-compose logs -f api            # Backend logs
docker-compose logs -f frontend       # Frontend logs
```

## Testing

### Backend
```bash
cd backend
poetry run pytest                              # All tests
poetry run pytest tests/test_auth.py           # Single file
poetry run pytest -k "test_user"               # Pattern match
poetry run pytest --cov=app --cov-report=html  # With coverage
poetry run pytest -m integration               # Integration tests only
```

### Frontend
```bash
cd frontend
npm test                      # Jest unit tests
npm run test:e2e              # Playwright E2E tests
npm run test:e2e:ui           # Interactive Playwright UI
```

## Code Quality

### Backend
```bash
cd backend
poetry run black app/         # Format
poetry run isort app/         # Sort imports
poetry run flake8 app/        # Lint
poetry run mypy app/          # Type check
```

### Frontend
```bash
cd frontend
npm run lint                  # ESLint
npm run type-check            # TypeScript
```

## Architecture

### Backend Layers
```
Routes (api/v1/*.py) → Dependencies → Services → SQLAlchemy Models
         ↓
   Auth middleware (JWT)
```

- **Routes**: `/backend/app/api/v1/` - REST endpoints with Pydantic schemas
- **Services**: `/backend/app/services/` - Business logic (30+ services)
- **Models**: `/backend/app/models/` - SQLAlchemy 2.0 async models (18 models)
- **Config**: `/backend/app/core/config.py` - Environment-driven settings

### Frontend Structure
```
src/app/           # Next.js 14 App Router (route groups: (auth), dashboard)
src/components/    # React components (ui/ for shadcn, layout/ for wrappers)
src/lib/           # API clients, Zustand stores, hooks, utilities
src/types/         # TypeScript interfaces
```

State management: Zustand (client) + React Query (server)

### Trading Strategies
Located in `/src/strategies/` with `BaseStrategy` parent class:
- SMA Crossover, RSI, MACD, Bollinger Bands, VWAP, Momentum, Adaptive ML

### Key External Integrations
- **Alpaca API**: Live/paper trading via alpaca-py
- **yfinance**: Market data fetching
- **pandas-ta**: Technical indicators
- **Socket.IO**: Real-time updates

## Database

PostgreSQL 15+ with async SQLAlchemy. Key models: User, Strategy, Trade, Order, Portfolio, Backtest, LiveStrategy, PaperTradingSession, AuditLog.

Migrations: Alembic in `/backend/migrations/`

## Environment Variables

Backend requires `.env` with:
- `DATABASE_URL` (PostgreSQL async connection string)
- `REDIS_URL`
- `SECRET_KEY`, `ALGORITHM`
- `ALPACA_API_KEY`, `ALPACA_SECRET_KEY`, `ALPACA_BASE_URL`

Frontend uses `.env.local` for `NEXT_PUBLIC_API_URL`.

## Pytest Configuration

Backend uses `asyncio_mode = auto` with function-scoped loops. Test markers: `integration`, `database`, `slow`.
