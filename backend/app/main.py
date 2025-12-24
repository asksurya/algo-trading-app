"""
FastAPI application entry point.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.core.config import settings
from app.database import init_db, close_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan events.
    Handles startup and shutdown.
    """
    # Startup
    await init_db()
    
    # Start strategy scheduler
    from app.strategies.scheduler import start_scheduler
    start_scheduler()
    
    yield
    
    # Shutdown
    from app.strategies.scheduler import stop_scheduler
    stop_scheduler()
    await close_db()


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Production-grade algo trading web application API",
    lifespan=lifespan,
    docs_url="/docs",  # Changed to /docs for easier access
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Configure CORS
# In development, allow all origins. In production, use settings.ALLOWED_ORIGINS
cors_origins = ["*"] if settings.is_development else settings.ALLOWED_ORIGINS
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate Limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# Production Security Features
if not settings.is_development and not settings.is_test:
    # HTTPS Redirection
    app.add_middleware(HTTPSRedirectMiddleware)

    # Trusted Host
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["yourdomain.com", "*.yourdomain.com"]
    )

# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)

    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

    return response


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/api/docs",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
    }


# Include API routers
from app.api.v1 import (
    auth,
    users,
    strategies,
    trades,
    broker,
    orders,
    strategy_execution,
    backtests,
    risk_rules,
    api_keys,
    notifications,
    optimizer,
    live_trading,
    portfolio,
    watchlist,
    paper_trading,
)

app.include_router(
    auth.router,
    prefix=f"{settings.API_V1_STR}/auth",
    tags=["Authentication"]
)
app.include_router(
    users.router,
    prefix=f"{settings.API_V1_STR}/users",
    tags=["Users"]
)
app.include_router(
    strategies.router,
    prefix=f"{settings.API_V1_STR}/strategies",
    tags=["Strategies"]
)
app.include_router(
    strategy_execution.router,
    prefix=f"{settings.API_V1_STR}/strategies/execution",
    tags=["Strategy Execution"]
)
app.include_router(
    trades.router,
    prefix=f"{settings.API_V1_STR}/trades",
    tags=["Trades & Positions"]
)
app.include_router(
    broker.router,
    prefix=f"{settings.API_V1_STR}/broker",
    tags=["Broker & Market Data"]
)
app.include_router(
    orders.router,
    prefix=f"{settings.API_V1_STR}/orders",
    tags=["Order Execution"]
)
app.include_router(
    backtests.router,
    prefix=f"{settings.API_V1_STR}/backtests",
    tags=["Backtesting"]
)
app.include_router(
    risk_rules.router,
    prefix=f"{settings.API_V1_STR}/risk-rules",
    tags=["Risk Management"]
)
app.include_router(
    api_keys.router,
    prefix=f"{settings.API_V1_STR}/api-keys",
    tags=["API Key Management"]
)
app.include_router(
    notifications.router,
    prefix=f"{settings.API_V1_STR}/notifications",
    tags=["Notifications"]
)
app.include_router(
    optimizer.router,
    prefix=f"{settings.API_V1_STR}/optimizer",
    tags=["Strategy Optimizer"]
)
app.include_router(
    live_trading.router,
    prefix=f"{settings.API_V1_STR}/live-trading",
    tags=["Live Trading Automation"]
)
app.include_router(
    portfolio.router,
    prefix=f"{settings.API_V1_STR}/portfolio",
    tags=["Portfolio Analytics"]
)
app.include_router(
    watchlist.router,
    prefix=f"{settings.API_V1_STR}/watchlists",
    tags=["Watchlist & Alerts"]
)
app.include_router(
    paper_trading.router,
    prefix=f"{settings.API_V1_STR}/paper-trading",
    tags=["Paper Trading"]
)


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.is_development,
        log_level=settings.LOG_LEVEL.lower(),
    )
