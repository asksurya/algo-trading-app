# New Features Quick Start Guide

## 🚀 Quick Setup

### 1. Run Database Migrations
```bash
cd backend
alembic upgrade head
```

### 2. Install Dependencies (Optional for full features)
```bash
# Backend - for news and reports
pip install alpha-vantage==2.3.1 twilio==8.4.0 openpyxl==3.1.2 reportlab==4.0.4

# Frontend - for advanced charting
cd ../frontend
npm install lightweight-charts recharts react-pdf
```

### 3. Set Environment Variables (Optional)
```bash
# Add to backend/.env
ALPHA_VANTAGE_API_KEY=your_key_here
NEWS_API_KEY=your_key_here
TWILIO_ACCOUNT_SID=your_sid_here
TWILIO_AUTH_TOKEN=your_token_here
```

### 4. Start Services
```bash
# Docker (recommended)
docker-compose up --build

# Or manually
cd backend && uvicorn app.main:app --reload
cd frontend && npm run dev
```

---

## 📊 New Features Overview

### 1. Portfolio Analytics
**Access:** `http://localhost:3000/dashboard/portfolio`

**Features:**
- Real-time portfolio summary
- Sharpe Ratio, Sortino Ratio, Calmar Ratio
- Max drawdown tracking
- Equity curve visualization
- Performance by period (daily/weekly/monthly/yearly)

**API:** `GET /api/v1/portfolio/summary`

---

### 2. Watchlist & Price Alerts
**Access:** `http://localhost:3000/dashboard/watchlist`

**Features:**
- Create multiple watchlists
- Add/remove symbols
- Real-time price updates
- Set price alerts (above/below)
- Notes for each symbol

**API:** `GET /api/v1/watchlist`

---

### 3. Paper Trading
**Use in code:**
```python
from app.services.paper_trading import get_paper_trading_service

service = await get_paper_trading_service(session)
account = await service.get_paper_account(user_id)
result = await service.execute_paper_order(
    user_id, "AAPL", 10, "buy"
)
```

---

### 4. Audit Trail
**Automatic logging of:**
- All trades and orders
- Authentication events
- Strategy changes
- Risk events
- Configuration changes

**Access logs programmatically:**
```python
from app.services.audit_logger import get_audit_logger

logger = await get_audit_logger(session)
await logger.log_trade(user_id, trade_data)
```

---

### 5. News Service
```python
from app.services.news_service import get_news_service

news = get_news_service()
market_news = await news.get_market_news(limit=20)
symbol_news = await news.get_symbol_news("AAPL", limit=10)
```

---

### 6. Stock Screener
```python
from app.services.screener import get_screener_service

screener = await get_screener_service(session)
results = await screener.screen_stocks(
    min_market_cap=1000000000,
    max_pe_ratio=30,
    sectors=["Technology"]
)
```

---

## 🗂️ New API Endpoints

### Portfolio
- `GET /api/v1/portfolio/summary` - Portfolio summary
- `GET /api/v1/portfolio/equity-curve` - Equity curve
- `GET /api/v1/portfolio/performance` - Performance metrics
- `GET /api/v1/portfolio/returns` - Returns analysis

### Watchlist
- `GET /api/v1/watchlist` - List watchlists
- `POST /api/v1/watchlist` - Create watchlist
- `GET /api/v1/watchlist/{id}` - Get watchlist
- `POST /api/v1/watchlist/{id}/items` - Add symbol
- `GET /api/v1/watchlist/alerts` - List alerts
- `POST /api/v1/watchlist/alerts` - Create alert

---

## 📁 Files Created

**Backend Services (9):**
- `portfolio_analytics.py` - Performance metrics
- `paper_trading.py` - Virtual trading
- `audit_logger.py` - Compliance logging
- `news_service.py` - News aggregation
- `screener.py` - Stock screening

**API Routers (2):**
- `portfolio.py` - Portfolio endpoints
- `watchlist.py` - Watchlist endpoints

**Frontend Pages (2):**
- `dashboard/portfolio/page.tsx`
- `dashboard/watchlist/page.tsx`

**Database Migrations (2):**
- `003_portfolio_analytics.py`
- `004_watchlist.py`

---

## ⚠️ Important Notes

### Models Directory Gitignored
The `backend/app/models/` directory is gitignored. You'll need to manually create:
- `portfolio.py` - Portfolio, PerformanceMetrics, TaxLot models
- `watchlist.py` - Watchlist, WatchlistItem, PriceAlert models

Model code is provided in the implementation plan.

### Placeholder Implementations
Some services use mock data and need API integration:
- News service → Integrate Alpha Vantage
- Screener → Integrate real market data
- Watchlist prices → Add WebSocket updates

---

## 🧪 Testing

```bash
# Backend
cd backend
pytest tests/test_portfolio_analytics.py -v
pytest tests/test_watchlist.py -v

# Frontend
cd frontend
npm test
npm run test:e2e
```

---

## 📖 Full Documentation

See `walkthrough.md` for:
- Complete implementation details
- Usage examples
- Database schema
- Testing procedures
- Next steps

---

## 🎯 Next Steps

1. Copy model files from implementation plan to `backend/app/models/`
2. Run migrations: `alembic upgrade head`
3. Install optional dependencies for full features
4. Test new endpoints via `/docs`
5. Access new UI pages in dashboard

**For Production:**
- Integrate real news APIs
- Add WebSocket for live price updates  
- Implement charting library (lightweight-charts)
- Set up background workers for alerts
- Add SMS/email notifications
