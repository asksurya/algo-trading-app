# Algo Trading API - Backend

FastAPI-based backend for the algo trading web application.

## Features

- ✅ FastAPI with async/await support
- ✅ SQLAlchemy 2.0 ORM with async sessions
- ✅ PostgreSQL database with JSONB support
- ✅ Redis caching and session management
- ✅ JWT-based authentication
- ✅ Pydantic V2 for request/response validation
- ✅ Environment-driven configuration (no hardcoded values)
- ✅ Docker and Docker Compose setup
- ✅ Production-ready architecture

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── database.py          # Database connection & session management
│   ├── dependencies.py      # Common dependencies (auth, etc.)
│   ├── core/
│   │   ├── config.py        # Settings (environment-driven)
│   │   └── security.py      # JWT & password hashing
│   ├── models/              # SQLAlchemy models
│   │   ├── user.py
│   │   ├── strategy.py
│   │   └── trade.py
│   ├── schemas/             # Pydantic schemas
│   │   ├── user.py
│   │   ├── strategy.py
│   │   └── trade.py
│   ├── api/                 # API routes (TODO)
│   ├── services/            # Business logic (TODO)
│   └── tasks/               # Background tasks (TODO)
├── tests/                   # Unit & integration tests (TODO)
├── migrations/              # Alembic migrations (TODO)
├── .env.example             # Environment variables template
├── pyproject.toml           # Poetry dependencies
├── Dockerfile               # Production Docker image
├── docker-compose.yml       # Local development stack
└── README.md
```

## Prerequisites

- Python 3.11+
- Poetry
- Docker & Docker Compose (for local development)
- PostgreSQL 15+ (if not using Docker)
- Redis 7+ (if not using Docker)

## Setup

### 1. Install Dependencies

```bash
# Install Poetry if you haven't
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
poetry install
```

### 2. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your values
# IMPORTANT: Update SECRET_KEY, ALPACA_API_KEY, ALPACA_SECRET_KEY
```

### 3. Run with Docker Compose (Recommended)

```bash
# Start all services (PostgreSQL, Redis, API)
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop services
docker-compose down
```

The API will be available at:
- API: http://localhost:8000
- Docs: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

### 4. Run Locally (Without Docker)

```bash
# Make sure PostgreSQL and Redis are running

# Run database migrations (when Alembic is set up)
# poetry run alembic upgrade head

# Run development server
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Configuration

All configuration is environment-driven through `.env` file:

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/algo_trading

# Redis
REDIS_URL=redis://localhost:6379/0

# Security (MUST CHANGE IN PRODUCTION)
SECRET_KEY=your-secret-key-min-32-chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=30

# Alpaca Trading
ALPACA_API_KEY=your-key
ALPACA_SECRET_KEY=your-secret
ALPACA_BASE_URL=https://paper-api.alpaca.markets

# CORS
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001

# Environment
ENVIRONMENT=development
LOG_LEVEL=INFO
```

## Database Models

### User
- Authentication & profile management
- Role-based access control (admin, user, viewer)
- Email verification support

### Strategy
- Trading strategy configurations
- Strategy-specific parameters (stored as JSON)
- Backtest results tracking

### Trade
- Trade execution tracking
- Order status management
- P&L calculation

### Position
- Current positions tracking
- Real-time P&L updates

## API Endpoints (Planned)

### Authentication
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/refresh` - Refresh access token
- `POST /api/v1/auth/logout` - User logout

### Users
- `GET /api/v1/users/me` - Get current user
- `PUT /api/v1/users/me` - Update current user
- `POST /api/v1/users/me/password` - Change password

### Strategies
- `GET /api/v1/strategies` - List user strategies
- `POST /api/v1/strategies` - Create strategy
- `GET /api/v1/strategies/{id}` - Get strategy
- `PUT /api/v1/strategies/{id}` - Update strategy
- `DELETE /api/v1/strategies/{id}` - Delete strategy
- `POST /api/v1/strategies/{id}/backtest` - Run backtest

### Trades
- `GET /api/v1/trades` - List trades
- `POST /api/v1/trades` - Create trade
- `GET /api/v1/trades/{id}` - Get trade
- `GET /api/v1/trades/statistics` - Get trading statistics

### Positions
- `GET /api/v1/positions` - List current positions
- `GET /api/v1/positions/{id}` - Get position

## Development

### Code Style

```bash
# Format code
poetry run black app/

# Sort imports
poetry run isort app/

# Type checking
poetry run mypy app/

# Linting
poetry run flake8 app/
```

### Testing

```bash
# Run tests (when implemented)
poetry run pytest

# With coverage
poetry run pytest --cov=app --cov-report=html
```

## Production Deployment

### Build Docker Image

```bash
docker build -t algo-trading-api:latest .
```

### Environment Variables

Ensure all environment variables are properly set in production:
- Use strong `SECRET_KEY` (generate with `openssl rand -hex 32`)
- Set `ENVIRONMENT=production`
- Use production database credentials
- Configure proper CORS origins
- Use production Alpaca credentials

### Health Checks

- Health endpoint: `GET /health`
- Returns: `{"status": "healthy", "environment": "production"}`

## Next Steps

1. **Implement API Routers** - Create actual API endpoints
2. **Add Alembic Migrations** - Database schema versioning
3. **Implement Services** - Business logic layer
4. **Add Background Tasks** - Celery tasks for strategy evaluation
5. **Write Tests** - Unit and integration tests
6. **Add WebSocket Support** - Real-time updates
7. **Implement Rate Limiting** - API protection
8. **Add Logging** - Structured logging
9. **API Documentation** - Complete OpenAPI docs

## License

This project is proprietary software.
