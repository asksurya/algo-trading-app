# Web Application Conversion - Technical Specification

**Version**: 1.0  
**Date**: October 2025  
**Purpose**: Convert Streamlit algo trading app to production-grade web application

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Current State Analysis](#current-state-analysis)
3. [Target Architecture](#target-architecture)
4. [Technology Stack](#technology-stack)
5. [Database Schema](#database-schema)
6. [API Specifications](#api-specifications)
7. [Frontend Architecture](#frontend-architecture)
8. [Authentication & Authorization](#authentication--authorization)
9. [File Structure](#file-structure)
10. [Implementation Phases](#implementation-phases)
11. [Security Considerations](#security-considerations)
12. [Deployment Strategy](#deployment-strategy)
13. [Testing Strategy](#testing-strategy)

---

## Executive Summary

### Project Goals

Convert existing Streamlit-based algo trading application into a modern, scalable web application with:
- ✅ Modern responsive UI (React/Next.js)
- ✅ RESTful API backend (FastAPI)
- ✅ Robust user authentication
- ✅ Multi-user support
- ✅ Real-time updates (WebSockets)
- ✅ Production-ready deployment

### Key Benefits

- **Scalability**: Support multiple concurrent users
- **Performance**: Faster load times, better UX
- **Security**: Industry-standard auth & encryption
- **Maintainability**: Separation of concerns
- **Extensibility**: Easy to add new features

---

## Current State Analysis

### Existing Components

**Backend (Python)**
- `src/trading/` - Trading daemon, live trader, state manager
- `src/strategies/` - 11 trading strategies
- `src/backtesting/` - Backtest engine
- `src/data/` - Data fetcher with caching
- `src/analysis/` - Sentiment analyzer

**Frontend (Streamlit)**
- `app.py` - Main entry point
- `pages/` - Multiple pages (backtesting, live trading, diagnostics)
- `auth.py` - Basic password authentication

**Data Storage**
- SQLite database (`trading_state.db`)
- File-based secrets (`.streamlit/secrets.toml`)

### Limitations to Address

1. ❌ Single-user design
2. ❌ No proper user management
3. ❌ Limited real-time capabilities
4. ❌ Tightly coupled frontend/backend
5. ❌ Basic authentication only
6. ❌ Not mobile-responsive

---

## Target Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     CLIENT (Browser)                         │
│  ┌─────────────────────────────────────────────────────┐   │
│  │         Next.js/React Frontend (Port 3000)          │   │
│  │  - Dashboard  - Backtesting  - Live Trading        │   │
│  │  - Strategy Config  - Account Settings             │   │
│  └─────────────────────────────────────────────────────┘   │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTPS/REST + WebSockets
┌──────────────────────┴──────────────────────────────────────┐
│                   API SERVER (FastAPI)                       │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              REST API (Port 8000)                   │   │
│  │  - Auth  - Trading  - Strategies  - Data           │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │           WebSocket Server (Port 8000)              │   │
│  │  - Real-time updates  - Live prices  - Trades      │   │
│  └─────────────────────────────────────────────────────┘   │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────┴──────────────────────────────────────┐
│              BUSINESS LOGIC & DATA LAYER                     │
│  ┌─────────────────┐  ┌──────────────────────────────┐     │
│  │ Trading Daemon  │  │  PostgreSQL Database         │     │
│  │ (Background)    │  │  - Users  - Strategies       │     │
│  │                 │  │  - Trades  - Price Cache     │     │
│  └─────────────────┘  └──────────────────────────────┘     │
│  ┌─────────────────────────────────────────────────────┐   │
│  │         Redis (Caching & Sessions)                  │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

**Frontend (Next.js + React)**
- User interface rendering
- Client-side routing
- State management (Redux/Zustand)
- Real-time data display
- Form validation

**Backend API (FastAPI)**
- RESTful endpoints
- WebSocket connections
- Business logic orchestration
- Authentication/Authorization
- Input validation & sanitization

**Trading Daemon (Python)**
- Background strategy execution
- Trade execution with Alpaca
- Signal generation
- Data synchronization

**Database (PostgreSQL)**
- Persistent data storage
- User management
- Trading history
- Configuration storage

**Cache (Redis)**
- Session storage
- Real-time data caching
- WebSocket pub/sub
- Rate limiting

---

## Technology Stack

### Frontend

**Framework**: Next.js 14 (React 18)
- **Why**: SSR/SSG, excellent performance, great DX
- **Alternative**: React + Vite (if simpler setup preferred)

**UI Library**: Tailwind CSS + shadcn/ui
- **Why**: Modern, customizable, accessible components
- **Alternative**: Material-UI, Chakra UI

**State Management**: Zustand
- **Why**: Simple, lightweight, TypeScript-first
- **Alternative**: Redux Toolkit, Jotai

**Data Fetching**: TanStack Query (React Query)
- **Why**: Caching, automatic refetching, optimistic updates
- **Alternative**: SWR, Apollo Client

**Charts**: Recharts + TradingView Lightweight Charts
- **Why**: Beautiful, interactive, financial-grade charts
- **Alternative**: Chart.js, ApexCharts

**Forms**: React Hook Form + Zod
- **Why**: Performance, TypeScript validation
- **Alternative**: Formik + Yup

**WebSockets**: Socket.IO Client
- **Why**: Reliable, fallbacks, easy to use
- **Alternative**: Native WebSocket API

### Backend

**Framework**: FastAPI 0.104+
- **Why**: Fast, async, auto-docs, type safety
- **Alternative**: Flask + Flask-RESTX

**ORM**: SQLAlchemy 2.0 + Alembic
- **Why**: Mature, powerful, migration support
- **Alternative**: Prisma (if using TypeScript backend)

**Authentication**: FastAPI-Users + JWT
- **Why**: Complete auth solution, OAuth support
- **Alternative**: Custom JWT implementation

**WebSockets**: FastAPI WebSockets + python-socketio
- **Why**: Integrated with FastAPI, async support
- **Alternative**: Django Channels

**Task Queue**: Celery + Redis
- **Why**: Reliable, mature, distributed
- **Alternative**: Dramatiq, RQ

**Validation**: Pydantic V2
- **Why**: Built-in FastAPI, fast, TypeScript integration
- **Alternative**: Marshmallow

### Database & Cache

**Primary Database**: PostgreSQL 15+
- **Why**: ACID, JSON support, mature, scalable
- **Alternative**: MySQL 8+, CockroachDB

**Cache/Session Store**: Redis 7+
- **Why**: Fast, pub/sub, session management
- **Alternative**: Memcached, KeyDB

**Time-Series (Optional)**: TimescaleDB
- **Why**: PostgreSQL extension, perfect for price data
- **Alternative**: InfluxDB

### DevOps & Deployment

**Containerization**: Docker + Docker Compose
**Orchestration**: Docker Swarm or Kubernetes (for scale)
**Web Server**: Nginx (reverse proxy)
**Process Manager**: Systemd or Supervisor
**CI/CD**: GitHub Actions or GitLab CI
**Monitoring**: Prometheus + Grafana
**Logging**: ELK Stack or Loki

### Development Tools

**Language**: Python 3.11+, TypeScript 5+, Node.js 20+
**Package Managers**: Poetry (Python), pnpm (Node)
**Code Quality**: ESLint, Prettier, Black, mypy
**Testing**: Jest, Pytest, Playwright
**API Documentation**: OpenAPI/Swagger (auto-generated)

---

## Database Schema

### Users Table

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    is_active BOOLEAN DEFAULT true,
    is_superuser BOOLEAN DEFAULT false,
    is_verified BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP,
    
    -- Alpaca credentials (encrypted)
    alpaca_api_key_encrypted TEXT,
    alpaca_secret_key_encrypted TEXT,
    
    -- Trading preferences
    initial_capital DECIMAL(15, 2) DEFAULT 10000.00,
    risk_per_trade DECIMAL(5, 4) DEFAULT 0.02,
    max_positions INTEGER DEFAULT 5,
    paper_trading BOOLEAN DEFAULT true,
    
    CONSTRAINT valid_email CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$')
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
```

### Trading Configurations Table

```sql
CREATE TABLE trading_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    tickers TEXT[] NOT NULL, -- PostgreSQL array
    check_interval INTEGER DEFAULT 300,
    is_active BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(user_id, name)
);

CREATE INDEX idx_trading_configs_user ON trading_configs(user_id);
CREATE INDEX idx_trading_configs_active ON trading_configs(user_id, is_active);
```

### Strategy Evaluations Table

```sql
CREATE TABLE strategy_evaluations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    config_id UUID REFERENCES trading_configs(id) ON DELETE CASCADE,
    ticker VARCHAR(20) NOT NULL,
    strategy_name VARCHAR(100) NOT NULL,
    metrics JSONB NOT NULL,
    score DECIMAL(10, 4) NOT NULL,
    metric_name VARCHAR(50) NOT NULL,
    evaluated_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(user_id, ticker, strategy_name)
);

CREATE INDEX idx_strategy_eval_user ON strategy_evaluations(user_id);
CREATE INDEX idx_strategy_eval_ticker ON strategy_evaluations(user_id, ticker);
CREATE INDEX idx_strategy_eval_score ON strategy_evaluations(ticker, score DESC);
```

### Best Strategies Table

```sql
CREATE TABLE best_strategies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    ticker VARCHAR(20) NOT NULL,
    strategy_name VARCHAR(100) NOT NULL,
    score DECIMAL(10, 4) NOT NULL,
    metric_name VARCHAR(50) NOT NULL,
    selected_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(user_id, ticker)
);

CREATE INDEX idx_best_strategies_user ON best_strategies(user_id);
```

### Trade History Table

```sql
CREATE TABLE trade_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    ticker VARCHAR(20) NOT NULL,
    strategy_name VARCHAR(100) NOT NULL,
    action VARCHAR(10) NOT NULL CHECK (action IN ('BUY', 'SELL')),
    quantity INTEGER NOT NULL,
    price DECIMAL(15, 4) NOT NULL,
    total_value DECIMAL(15, 2) GENERATED ALWAYS AS (quantity * price) STORED,
    signal INTEGER NOT NULL,
    order_id VARCHAR(100),
    executed_at TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT valid_quantity CHECK (quantity > 0),
    CONSTRAINT valid_price CHECK (price > 0)
);

CREATE INDEX idx_trade_history_user ON trade_history(user_id);
CREATE INDEX idx_trade_history_ticker ON trade_history(user_id, ticker);
CREATE INDEX idx_trade_history_time ON trade_history(executed_at DESC);
```

### Price Data Cache Table

```sql
CREATE TABLE price_data_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticker VARCHAR(20) NOT NULL,
    date DATE NOT NULL,
    open DECIMAL(15, 4) NOT NULL,
    high DECIMAL(15, 4) NOT NULL,
    low DECIMAL(15, 4) NOT NULL,
    close DECIMAL(15, 4) NOT NULL,
    volume BIGINT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(ticker, date)
);

CREATE INDEX idx_price_cache_ticker ON price_data_cache(ticker, date DESC);
```

### Sessions Table (for JWT refresh tokens)

```sql
CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    refresh_token TEXT NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    ip_address INET,
    user_agent TEXT
);

CREATE INDEX idx_sessions_user ON user_sessions(user_id);
CREATE INDEX idx_sessions_token ON user_sessions(refresh_token);
CREATE INDEX idx_sessions_expires ON user_sessions(expires_at);
```

### Audit Log Table

```sql
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id UUID,
    details JSONB,
    ip_address INET,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_time ON audit_logs(created_at DESC);
```

---

## API Specifications

### Base Configuration

```
Base URL: https://api.yourdomain.com/v1
Content-Type: application/json
Authorization: Bearer <JWT_TOKEN>
```

### Authentication Endpoints

#### POST /auth/register
Register new user

**Request**:
```json
{
  "email": "user@example.com",
  "username": "trader123",
  "password": "SecurePass123!",
  "first_name": "John",
  "last_name": "Doe"
}
```

**Response (201)**:
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "username": "trader123",
  "created_at": "2025-01-01T00:00:00Z"
}
```

#### POST /auth/login
Login user

**Request**:
```json
{
  "username": "trader123",
  "password": "SecurePass123!"
}
```

**Response (200)**:
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "username": "trader123"
  }
}
```

#### POST /auth/refresh
Refresh access token

**Request**:
```json
{
  "refresh_token": "eyJ..."
}
```

**Response (200)**:
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

#### POST /auth/logout
Logout user (invalidate refresh token)

**Response (204)**: No content

### User Profile Endpoints

#### GET /users/me
Get current user profile

**Response (200)**:
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "username": "trader123",
  "first_name": "John",
  "last_name": "Doe",
  "initial_capital": 10000.00,
  "risk_per_trade": 0.02,
  "max_positions": 5,
  "paper_trading": true,
  "created_at": "2025-01-01T00:00:00Z"
}
```

#### PATCH /users/me
Update user profile

**Request**:
```json
{
  "first_name": "John",
  "initial_capital": 15000.00,
  "risk_per_trade": 0.03
}
```

**Response (200)**: Updated user object

#### POST /users/me/alpaca-credentials
Set Alpaca API credentials (encrypted)

**Request**:
```json
{
  "api_key": "PK...",
  "secret_key": "..."
}
```

**Response (200)**:
```json
{
  "status": "credentials_saved"
}
```

### Trading Configuration Endpoints

#### GET /trading/configs
List user's trading configurations

**Response (200)**:
```json
{
  "configs": [
    {
      "id": "uuid",
      "name": "My Strategy",
      "tickers": ["AAPL", "MSFT", "TSLA"],
      "check_interval": 300,
      "is_active": true,
      "created_at": "2025-01-01T00:00:00Z"
    }
  ]
}
```

#### POST /trading/configs
Create trading configuration

**Request**:
```json
{
  "name": "My Strategy",
  "tickers": ["AAPL", "MSFT", "TSLA"],
  "check_interval": 300
}
```

**Response (201)**: Created config object

#### PATCH /trading/configs/{config_id}
Update trading configuration

#### DELETE /trading/configs/{config_id}
Delete trading configuration

#### POST /trading/configs/{config_id}/activate
Activate trading configuration

**Response (200)**:
```json
{
  "status": "activated",
  "config_id": "uuid"
}
```

#### POST /trading/configs/{config_id}/deactivate
Deactivate trading configuration

### Strategy Evaluation Endpoints

#### POST /strategies/evaluate
Evaluate all strategies for tickers

**Request**:
```json
{
  "config_id": "uuid",
  "lookback_days": null,
  "metric": "sharpe_ratio"
}
```

**Response (202)**:
```json
{
  "task_id": "uuid",
  "status": "processing",
  "message": "Evaluation started"
}
```

#### GET /strategies/evaluate/{task_id}
Get evaluation status

**Response (200)**:
```json
{
  "task_id": "uuid",
  "status": "completed",
  "progress": 100,
  "results": {
    "AAPL": {
      "best_strategy": "RSI",
      "best_score": 1.45,
      "all_results": {...}
    }
  }
}
```

#### GET /strategies/results
Get strategy evaluation results

**Query Parameters**:
- `ticker` (optional): Filter by ticker
- `config_id` (optional): Filter by config

**Response (200)**:
```json
{
  "results": [
    {
      "ticker": "AAPL",
      "strategy_name": "RSI",
      "score": 1.45,
      "metrics": {...},
      "evaluated_at": "2025-01-01T00:00:00Z"
    }
  ]
}
```

### Trade History Endpoints

#### GET /trades/history
Get trade history

**Query Parameters**:
- `ticker` (optional): Filter by ticker
- `start_date` (optional): Start date
- `end_date` (optional): End date
- `limit` (default: 100): Number of records
- `offset` (default: 0): Pagination offset

**Response (200)**:
```json
{
  "trades": [
    {
      "id": "uuid",
      "ticker": "AAPL",
      "strategy_name": "RSI",
      "action": "BUY",
      "quantity": 10,
      "price": 150.25,
      "total_value": 1502.50,
      "executed_at": "2025-01-01T14:30:00Z"
    }
  ],
  "total": 156,
  "limit": 100,
  "offset": 0
}
```

#### GET /trades/statistics
Get trading statistics

**Response (200)**:
```json
{
  "total_trades": 156,
  "total_buy": 78,
  "total_sell": 78,
  "total_value": 125000.00,
  "average_trade_size": 800.00,
  "most_traded_tickers": ["AAPL", "MSFT", "TSLA"],
  "profit_loss": 5000.00,
  "period": {
    "start": "2024-01-01",
    "end": "2025-01-01"
  }
}
```

### Market Data Endpoints

#### GET /data/tickers/{ticker}
Get historical price data

**Query Parameters**:
- `start_date`: Start date (YYYY-MM-DD)
- `end_date`: End date (YYYY-MM-DD)
- `timeframe`: Timeframe (1D, 1H, etc.)

**Response (200)**:
```json
{
  "ticker": "AAPL",
  "data": [
    {
      "date": "2025-01-01",
      "open": 150.00,
      "high": 152.00,
      "low": 149.00,
      "close": 151.50,
      "volume": 50000000
    }
  ]
}
```

#### GET /data/tickers/{ticker}/latest
Get latest price

**Response (200)**:
```json
{
  "ticker": "AAPL",
  "price": 151.50,
  "timestamp": "2025-01-01T16:00:00Z"
}
```

### WebSocket Events

#### Connection
```javascript
const socket = io('wss://api.yourdomain.com', {
  auth: {
    token: 'JWT_TOKEN'
  }
});
```

#### Events

**Client → Server**:
- `subscribe_ticker`: Subscribe to ticker updates
- `unsubscribe_ticker`: Unsubscribe from ticker
- `subscribe_trades`: Subscribe to trade updates

**Server → Client**:
- `ticker_update`: Real-time price update
- `trade_executed`: New trade executed
- `strategy_update`: Strategy evaluation update
- `error`: Error message

**Example**:
```javascript
// Subscribe to ticker
socket.emit('subscribe_ticker', { ticker: 'AAPL' });

// Listen for updates
socket.on('ticker_update', (data) => {
  console.log(data);
  // { ticker: 'AAPL', price: 151.50, timestamp: '...' }
});
```

---

## Frontend Architecture

### Technology Stack Details

**Framework**: Next.js 14 with App Router
**Language**: TypeScript 5.3+
**Styling**: Tailwind CSS + shadcn/ui
**State**: Zustand + React Query
**Forms**: React Hook Form + Zod
**Charts**: Recharts + TradingView

### Directory Structure

```
frontend/
├── public/
│   ├── images/
│   └── favicon.ico
├── src/
│   ├── app/                    # Next.js 14 app directory
│   │   ├── (auth)/            # Auth layout group
│   │   │   ├── login/
│   │   │   ├── register/
│   │   │   └── layout.tsx
│   │   ├── (dashboard)/       # Dashboard layout group
│   │   │   ├── dashboard/
│   │   │   ├── backtesting/
│   │   │   ├── live-trading/
│   │   │   ├── strategies/
│   │   │   ├── history/
│   │   │   ├── settings/
│   │   │   └── layout.tsx
│   │   ├── api/               # API routes (if needed)
│   │   ├── layout.tsx         # Root layout
│   │   └── page.tsx           # Landing page
│   ├── components/
│   │   ├── ui/                # shadcn/ui components
│   │   ├── charts/            # Chart components
│   │   ├── forms/             # Form components
│   │   ├── layout/            # Layout components
│   │   └── shared/            # Shared components
│   ├── lib/
│   │   ├── api/               # API client
│   │   ├── hooks/             # Custom hooks
│   │   ├── stores/            # Zustand stores
│   │   ├── utils/             # Utility functions
│   │   ├── validations/       # Zod schemas
│   │   └── websocket/         # WebSocket client
│   ├── types/                 # TypeScript types
│   └── styles/                # Global styles
├── .env.local
├── next.config.js
├── tailwind.config.js
├── tsconfig.json
└── package.json
```

### Key Components

#### 1. Authentication
```typescript
// src/lib/stores/auth-store.ts
import create from 'zustand';

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => void;
  refreshToken: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: null,
  isAuthenticated: false,
  login: async (credentials) => {
    const response = await api.post('/auth/login', credentials);
    set({ user: response.user, token: response.access_token, isAuthenticated: true });
  },
  logout: () => {
    set({ user: null, token: null, isAuthenticated: false });
  },
  refreshToken: async () => {
    // Implementation
  },
}));
```

#### 2. API Client
```typescript
// src/lib/api/client.ts
import axios from 'axios';
import { useAuthStore } from '@/lib/stores/auth-store';

export const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor
api.interceptors.response.use(
  (response) => response.data,
  async (error) => {
    if (error.response?.status === 401) {
      // Refresh token logic
    }
    return Promise.reject(error);
  }
);
```

#### 3. WebSocket Manager
```typescript
// src/lib/websocket/manager.ts
import { io, Socket } from 'socket.io-client';

class WebSocketManager {
  private socket: Socket | null = null;

  connect(token: string) {
    this.socket = io(process.env.NEXT_PUBLIC_WS_URL!, {
      auth: { token },
    });

    this.socket.on('connect', () => {
      console.log('WebSocket connected');
    });

    this.socket.on('disconnect', () => {
      console.log('WebSocket disconnected');
    });
  }

  subscribeTicker(ticker: string, callback: (data: any) => void) {
    this.socket?.emit('subscribe_ticker', { ticker });
    this.socket?.on('ticker_update', callback);
  }

  disconnect() {
    this.socket?.disconnect();
  }
}

export const wsManager = new WebSocketManager();
```

#### 4. Trading Dashboard
```typescript
// src/app/(dashboard)/dashboard/page.tsx
'use client';

import { useQuery } from '@tanstack/react-query';
import { Card } from '@/components/ui/card';
import { TradingChart } from '@/components/charts/trading-chart';

export default function Dashboard() {
  const { data: stats } = useQuery({
    queryKey: ['trading-stats'],
    queryFn: () => api.get('/trades/statistics'),
  });

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Trading Dashboard</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <h3>Total Trades</h3>
          <p className="text-2xl font-bold">{stats?.total_trades}</p>
        </Card>
        {/* More stat cards */}
      </div>

      <TradingChart />
    </div>
  );
}
```

### Responsive Design

- Mobile-first approach
- Breakpoints: sm (640px), md (768px), lg (1024px), xl (1280px)
- Touch-friendly interfaces
- Progressive Web App (PWA) support

---

## Authentication & Authorization

### JWT Implementation

**Access Token**:
- Expires: 1 hour
- Contains: user_id, email, role
- Stored: Memory (React state)

**Refresh Token**:
- Expires: 30 days
- Stored: HTTP-only cookie
- Used to refresh access token

### Security Measures

1. **Password Requirements**:
   - Minimum 8 characters
   - Must include: uppercase, lowercase, number, special char
   - Hashed with bcrypt (cost factor: 12)

2. **Rate Limiting**:
   - Login: 5 attempts per 15 minutes
   - API calls: 100 requests per minute
   - WebSocket: 50 connections per IP

3. **HTTPS Enforcement**:
   - All API calls over HTTPS
   - Secure cookies
   - HSTS headers

4. **Input Validation**:
   - Pydantic models on backend
