# Web Application Conversion - Implementation Plan

**Version**: 1.0  
**Date**: October 2025  
**Companion to**: WEBAPP_CONVERSION_TECHNICAL_SPEC.md

---

## Implementation Phases

This document provides a step-by-step implementation plan that can be followed by Claude 4.5 Haiku or any other AI model.

---

## PHASE 1: Backend API Setup (Week 1-2)

### Goal
Create FastAPI backend with authentication and basic endpoints.

### Step 1.1: Project Setup
```bash
# Create backend directory
mkdir -p backend
cd backend

# Initialize Poetry
poetry init --name algo-trading-api --python "^3.11"

# Add dependencies
poetry add fastapi[all] uvicorn[standard] sqlalchemy alembic psycopg2-binary
poetry add pydantic[email] python-jose[cryptography] passlib[bcrypt]
poetry add python-multipart aiofiles python-socketio redis celery
poetry add fastapi-users[sqlalchemy,oauth] python-dotenv
poetry add --group dev pytest pytest-asyncio httpx black mypy
```

### Step 1.2: Create Directory Structure
```bash
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app entry
│   ├── config.py               # Configuration
│   ├── database.py             # Database connection
│   ├── dependencies.py         # Common dependencies
│   ├── api/
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── users.py
│   │   │   ├── trading.py
│   │   │   ├── strategies.py
│   │   │   ├── trades.py
│   │   │   └── data.py
│   │   └── websocket.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── security.py         # Auth & encryption
│   │   ├── config.py           # Settings
│   │   └── exceptions.py       # Custom exceptions
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── trading.py
│   │   ├── strategy.py
│   │   └── trade.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── trading.py
│   │   ├── strategy.py
│   │   └── trade.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── trading_service.py
│   │   ├── strategy_service.py
│   │   └── data_service.py
│   └── tasks/
│       ├── __init__.py
│       └── evaluation_tasks.py
├── migrations/                  # Alembic migrations
├── tests/
├── .env.example
├── pyproject.toml
└── README.md
```

### Step 1.3: Create Database Models
**File: `app/models/user.py`**
```python
from sqlalchemy import Column, String, Boolean, DateTime, Decimal, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from app.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100))
    last_name = Column(String(100))
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True))
    
    # Alpaca credentials (encrypted)
    alpaca_api_key_encrypted = Column(Text)
    alpaca_secret_key_encrypted = Column(Text)
    
    # Trading preferences
    initial_capital = Column(Decimal(15, 2), default=10000.00)
    risk_per_trade = Column(Decimal(5, 4), default=0.02)
    max_positions = Column(Integer, default=5)
    paper_trading = Column(Boolean, default=True)
```

**File: `app/models/trading.py`**
```python
from sqlalchemy import Column, String, Boolean, DateTime, Integer, ForeignKey, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from app.database import Base

class TradingConfig(Base):
    __tablename__ = "trading_configs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    tickers = Column(ARRAY(String), nullable=False)
    check_interval = Column(Integer, default=300)
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", backref="trading_configs")
```

### Step 1.4: Create FastAPI Application
**File: `app/main.py`**
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import auth, users, trading, strategies, trades, data
from app.core.config import settings

app = FastAPI(
    title="Algo Trading API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/v1/auth", tags=["auth"])
app.include_router(users.router, prefix="/v1/users", tags=["users"])
app.include_router(trading.router, prefix="/v1/trading", tags=["trading"])
app.include_router(strategies.router, prefix="/v1/strategies", tags=["strategies"])
app.include_router(trades.router, prefix="/v1/trades", tags=["trades"])
app.include_router(data.router, prefix="/v1/data", tags=["data"])

@app.get("/")
async def root():
    return {"message": "Algo Trading API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
```

### Step 1.5: Implement Authentication
**File: `app/api/v1/auth.py`**
```python
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta

from app.core.security import create_access_token, verify_password, get_password_hash
from app.core.config import settings
from app.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, Token

router = APIRouter()

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    # Check if user exists
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(status_code=400, detail="Username already taken")
    
    # Create user
    user = User(
        email=user_data.email,
        username=user_data.username,
        password_hash=get_password_hash(user_data.password),
        first_name=user_data.first_name,
        last_name=user_data.last_name
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user

@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    # Authenticate user
    user = db.query(User).filter(User.username == form_data.username).first()
    
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }
```

**DELIVERABLE**: Working FastAPI backend with auth endpoints

---

## PHASE 2: Frontend Setup (Week 2-3)

### Goal
Create Next.js frontend with authentication and basic UI.

### Step 2.1: Project Setup
```bash
# Create frontend directory
npx create-next-app@latest frontend --typescript --tailwind --app --src-dir

cd frontend

# Install dependencies
pnpm add zustand @tanstack/react-query axios
pnpm add react-hook-form zod @hookform/resolvers
pnpm add socket.io-client recharts
pnpm add lucide-react class-variance-authority clsx tailwind-merge

# Install shadcn/ui
pnpm dlx shadcn-ui@latest init
pnpm dlx shadcn-ui@latest add button card form input label
```

### Step 2.2: Create Directory Structure
```
frontend/src/
├── app/
│   ├── (auth)/
│   │   ├── login/page.tsx
│   │   ├── register/page.tsx
│   │   └── layout.tsx
│   ├── (dashboard)/
│   │   ├── dashboard/page.tsx
│   │   ├── backtesting/page.tsx
│   │   ├── live-trading/page.tsx
│   │   ├── strategies/page.tsx
│   │   ├── history/page.tsx
│   │   ├── settings/page.tsx
│   │   └── layout.tsx
│   ├── layout.tsx
│   └── page.tsx
├── components/
│   ├── ui/              # shadcn components
│   ├── auth/
│   │   ├── login-form.tsx
│   │   └── register-form.tsx
│   ├── dashboard/
│   │   ├── stats-card.tsx
│   │   ├── trading-chart.tsx
│   │   └── recent-trades.tsx
│   ├── layout/
│   │   ├── header.tsx
│   │   ├── sidebar.tsx
│   │   └── nav.tsx
│   └── shared/
│       ├── loading.tsx
│       └── error-boundary.tsx
├── lib/
│   ├── api/
│   │   └── client.ts
│   ├── stores/
│   │   ├── auth-store.ts
│   │   └── trading-store.ts
│   ├── hooks/
│   │   ├── use-auth.ts
│   │   └── use-trading.ts
│   ├── utils/
│   │   └── cn.ts
│   └── websocket/
│       └── manager.ts
└── types/
    ├── user.ts
    ├── trading.ts
    └── api.ts
```

### Step 2.3: Create API Client
**File: `src/lib/api/client.ts`**
```typescript
import axios, { AxiosInstance } from 'axios';
import { useAuthStore } from '../stores/auth-store';

export const api: AxiosInstance = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/v1',
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
      useAuthStore.getState().logout();
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);
```

### Step 2.4: Create Auth Store
**File: `src/lib/stores/auth-store.ts`**
```typescript
import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { api } from '../api/client';

interface User {
  id: string;
  email: string;
  username: string;
  first_name?: string;
  last_name?: string;
}

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  register: (data: RegisterData) => Promise<void>;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      
      login: async (username, password) => {
        const formData = new FormData();
        formData.append('username', username);
        formData.append('password', password);
        
        const response = await api.post('/auth/login', formData, {
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        });
        
        set({
          user: response.user,
          token: response.access_token,
          isAuthenticated: true,
        });
      },
      
      logout: () => {
        set({ user: null, token: null, isAuthenticated: false });
      },
      
      register: async (data) => {
        const response = await api.post('/auth/register', data);
        // Auto-login after registration
        await useAuthStore.getState().login(data.username, data.password);
      },
    }),
    {
      name: 'auth-storage',
    }
  )
);
```

### Step 2.5: Create Login Page
**File: `src/app/(auth)/login/page.tsx`**
```typescript
'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/lib/stores/auth-store';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

export default function LoginPage() {
  const router = useRouter();
  const login = useAuthStore((state) => state.login);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await login(username, password);
      router.push('/dashboard');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Login to Algo Trading</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <Label htmlFor="username">Username</Label>
              <Input
                id="username"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
              />
            </div>
            
            <div>
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>

            {error && <p className="text-sm text-red-500">{error}</p>}

            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? 'Logging in...' : 'Login'}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
```

**DELIVERABLE**: Working Next.js frontend with login functionality

---

## PHASE 3: Migration of Trading Logic (Week 3-4)

### Goal
Integrate existing Python trading logic with new API.

### Step 3.1: Adapt Existing Services
**File: `backend/app/services/trading_service.py`**
```python
# Import existing trading logic
import sys
sys.path.append('../../src')

from src.trading.live_trader import LiveTrader
from src.trading.state_manager import StateManager
from src.strategies import *

class TradingService:
    def __init__(self, user_id: str, db_session):
        self.user_id = user_id
        self.db = db_session
        self.state_manager = StateManager()
        
    async def evaluate_strategies(self, config_id: str):
        # Implementation that calls existing strategy evaluation
        pass
    
    async def start_trading(self, config_id: str):
        # Implementation that starts trading daemon for user
        pass
    
    async def stop_trading(self, config_id: str):
        # Implementation that stops trading
        pass
```

### Step 3.2: Create Background Tasks
**File: `backend/app/tasks/evaluation_tasks.py`**
```python
from celery import Celery
from app.services.trading_service import TradingService

celery_app = Celery('trading', broker='redis://localhost:6379/0')

@celery_app.task
def evaluate_strategies_task(user_id: str, config_id: str):
    service = TradingService(user_id)
    return service.evaluate_strategies(config_id)
```

**DELIVERABLE**: Backend integrates existing trading logic

---

## PHASE 4: Real-time Features (Week 4-5)

### Goal
Implement WebSocket for real-time updates.

### Step 4.1: Backend WebSocket
**File: `backend/app/api/websocket.py`**
```python
from fastapi import WebSocket, WebSocketDisconnect, Depends
from app.core.security import get_current_user_ws
import asyncio

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
    
    def disconnect(self, websocket: WebSocket, user_id: str):
        self.active_connections[user_id].remove(websocket)
    
    async def send_personal_message(self, message: dict, user_id: str):
        for connection in self.active_connections.get(user_id, []):
            await connection.send_json(message)

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: str = Depends(get_current_user_ws)
):
    await manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_json()
            # Handle different message types
            if data['type'] == 'subscribe_ticker':
                # Subscribe to ticker updates
                pass
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
```

### Step 4.2: Frontend WebSocket
**File: `frontend/src/lib/websocket/manager.ts`**
```typescript
import { io, Socket } from 'socket.io-client';

class WebSocketManager {
  private socket: Socket | null = null;
  private token: string | null = null;

  connect(token: string) {
    this.token = token;
    this.socket = io(process.env.NEXT_PUBLIC_WS_URL!, {
      auth: { token },
      transports: ['websocket'],
    });

    this.socket.on('connect', () => {
      console.log('WebSocket connected');
    });

    this.socket.on('disconnect', () => {
      console.log('WebSocket disconnected');
    });

    this.socket.on('error', (error) => {
      console.error('WebSocket error:', error);
    });
  }

  subscribeTicker(ticker: string, callback: (data: any) => void) {
    if (!this.socket) return;
    
    this.socket.emit('subscribe_ticker', { ticker });
    this.socket.on(`ticker_update_${ticker}`, callback);
  }

  unsubscribeTicker(ticker: string) {
    if (!this.socket) return;
    
    this.socket.emit('unsubscribe_ticker', { ticker });
    this.socket.off(`ticker_update_${ticker}`);
  }

  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
  }
}

export const wsManager = new WebSocketManager();
```

**DELIVERABLE**: Real-time price and trade updates working

---

## PHASE 5: Database Migration (Week 5)

### Goal
Migrate from SQLite to PostgreSQL with multi-user support.

### Step 5.1: Create Migration Scripts
```bash
# Initialize Alembic
cd backend
alembic init migrations

# Create migration
alembic revision --autogenerate -m "Initial migration"

# Apply migration
alembic upgrade head
```

### Step 5.2: Data Migration Script
**File: `backend/scripts/migrate_data.py`**
```python
import sqlite3
import psycopg2
from app.database import SessionLocal
from app.models import
