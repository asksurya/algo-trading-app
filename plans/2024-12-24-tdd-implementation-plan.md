# TDD Implementation Plan: Frontend, Database, Settings, WebSocket, Charts

## Overview

Test-Driven Development implementation of missing features for the algo-trading-app. We write tests first to define expected behavior, then implement code to make tests pass, ensuring no regressions in existing functionality.

## Current State Analysis

### What Exists:
- **Frontend**: 2 files in `/lib/` (execution.ts, use-execution.ts), complete UI pages
- **Backend**: 100+ API endpoints fully implemented, WebSocket ready
- **Database**: 24 models migrated, 4 models missing migrations
- **Testing**: Jest configured, Playwright installed but tests failing

### What's Missing:
- 10+ frontend `/lib/` files (hooks, API clients, stores)
- Database migrations for Watchlist, PriceAlert, AuditLog
- Settings page connections (all disabled)
- WebSocket frontend integration
- Chart components

### Key Discoveries:
- Token storage inconsistency: some use `'access_token'`, others `'token'`
- Migration conflict: two paper trading migrations with same parent
- `socket.io-client` installed but incompatible with FastAPI native WebSocket
- Types already defined in `/types/index.ts`

## Desired End State

After implementation:
1. All frontend pages render without import errors
2. Authentication flow works end-to-end
3. All CRUD operations functional (strategies, backtests, trades)
4. Settings page fully functional (API keys, notifications, profile)
5. Real-time price updates via WebSocket
6. Charts display equity curves in portfolio and backtest pages
7. 90%+ test coverage on new code
8. All E2E tests pass

## What We're NOT Doing

- Refactoring existing backend code
- Adding new API endpoints
- Changing database schema beyond missing tables
- Mobile-specific optimizations
- Performance optimization beyond basic functionality
- Migrating from fetch to axios

## Implementation Approach

**Testing Pyramid:**
- Unit Tests: Jest + React Testing Library
- Integration Tests: Jest + MSW (Mock Service Worker)
- E2E Tests: Playwright with Chromium

**Workflow per feature:**
1. Write failing tests (Red)
2. Implement minimum code to pass (Green)
3. Refactor while keeping tests passing (Refactor)
4. Run E2E to verify no regressions

---

## Phase 0: Baseline E2E Tests

### Overview
Establish baseline of existing functionality before making changes.

### Changes Required:

#### 1. Run Existing E2E Tests
```bash
cd frontend
npm run test:e2e -- --project=chromium
```

#### 2. Create Smoke Test Suite
**File**: `frontend/e2e/smoke.spec.ts`
```typescript
import { test, expect } from '@playwright/test';

test.describe('Smoke Tests - Baseline', () => {
  test('homepage loads', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveTitle(/Algo Trading/);
  });

  test('login page accessible', async ({ page }) => {
    await page.goto('/login');
    await expect(page.getByRole('button', { name: /login/i })).toBeVisible();
  });

  test('register page accessible', async ({ page }) => {
    await page.goto('/register');
    await expect(page.getByRole('button', { name: /register/i })).toBeVisible();
  });

  test('unauthenticated redirects to login', async ({ page }) => {
    await page.goto('/dashboard');
    await expect(page).toHaveURL(/login/);
  });
});
```

#### 3. Document Baseline Results
**File**: `frontend/e2e/BASELINE.md`
- Record which tests pass/fail before changes
- Screenshot any current errors
- Note expected failures due to missing `/lib/` files

### Success Criteria:

#### Automated Verification:
- [x] Smoke tests created: `ls frontend/e2e/smoke.spec.ts`
- [x] Baseline documented: `ls frontend/e2e/BASELINE.md`

#### Manual Verification:
- [x] Review baseline test results
- [x] Confirm expected failures are due to missing files (auth-store missing)

---

## Phase 1: Test Infrastructure Setup

### Overview
Configure testing tools and utilities for TDD workflow.

### Changes Required:

#### 1. Jest Configuration Updates
**File**: `frontend/jest.config.js`
```javascript
const nextJest = require('next/jest');

const createJestConfig = nextJest({
  dir: './',
});

const customJestConfig = {
  setupFilesAfterEnv: ['<rootDir>/jest.setup.ts'],
  testEnvironment: 'jsdom',
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1',
  },
  testPathIgnorePatterns: ['<rootDir>/e2e/'],
  collectCoverageFrom: [
    'src/lib/**/*.{ts,tsx}',
    '!src/lib/**/*.d.ts',
  ],
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80,
    },
  },
};

module.exports = createJestConfig(customJestConfig);
```

#### 2. Jest Setup File
**File**: `frontend/jest.setup.ts`
```typescript
import '@testing-library/jest-dom';

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};
Object.defineProperty(window, 'localStorage', { value: localStorageMock });

// Mock fetch
global.fetch = jest.fn();

// Reset mocks between tests
beforeEach(() => {
  jest.clearAllMocks();
  localStorageMock.getItem.mockClear();
  localStorageMock.setItem.mockClear();
});
```

#### 3. Test Utilities
**File**: `frontend/src/lib/__tests__/test-utils.tsx`
```typescript
import React, { ReactElement } from 'react';
import { render, RenderOptions } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

// Create a new QueryClient for each test
function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
        staleTime: 0,
      },
      mutations: {
        retry: false,
      },
    },
  });
}

interface WrapperProps {
  children: React.ReactNode;
}

function createWrapper() {
  const testQueryClient = createTestQueryClient();
  return function Wrapper({ children }: WrapperProps) {
    return (
      <QueryClientProvider client={testQueryClient}>
        {children}
      </QueryClientProvider>
    );
  };
}

function customRender(
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) {
  return render(ui, { wrapper: createWrapper(), ...options });
}

export * from '@testing-library/react';
export { customRender as render, createTestQueryClient };
```

#### 4. API Mock Fixtures
**File**: `frontend/src/lib/__tests__/fixtures.ts`
```typescript
import { User, Strategy, Backtest, Trade, AuthResponse } from '@/types';

export const mockUser: User = {
  id: 'user-123',
  email: 'test@example.com',
  full_name: 'Test User',
  role: 'user',
  is_active: true,
  is_verified: true,
  created_at: '2024-01-01T00:00:00Z',
};

export const mockAuthResponse: AuthResponse = {
  access_token: 'mock-access-token',
  refresh_token: 'mock-refresh-token',
  token_type: 'bearer',
};

export const mockStrategy: Strategy = {
  id: 'strategy-123',
  user_id: 'user-123',
  name: 'Test Strategy',
  description: 'A test strategy',
  strategy_type: 'sma_crossover',
  parameters: { short_window: 10, long_window: 50 },
  is_active: true,
  is_backtested: false,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
};

export const mockBacktest: Backtest = {
  id: 'backtest-123',
  user_id: 'user-123',
  strategy_id: 'strategy-123',
  name: 'Test Backtest',
  start_date: '2024-01-01',
  end_date: '2024-03-31',
  initial_capital: 100000,
  status: 'completed',
  total_return: 15.5,
  total_trades: 45,
  win_rate: 62.2,
  sharpe_ratio: 1.85,
  max_drawdown: -8.2,
  created_at: '2024-01-01T00:00:00Z',
};

export const mockTrade: Trade = {
  id: 'trade-123',
  user_id: 'user-123',
  strategy_id: 'strategy-123',
  ticker: 'AAPL',
  trade_type: 'buy',
  status: 'filled',
  quantity: '10',
  filled_quantity: '10',
  price: '150.00',
  filled_avg_price: '150.25',
  created_at: '2024-01-01T00:00:00Z',
  executed_at: '2024-01-01T00:00:15Z',
};

export const mockBrokerAccount = {
  portfolio_value: 115500,
  cash: 100000,
  buying_power: 100000,
  pattern_day_trader: false,
  long_market_value: 15500,
};

export const mockPositions = [
  {
    symbol: 'AAPL',
    qty: 10,
    avg_entry_price: 150.00,
    market_value: 1550.00,
    unrealized_pl: 50.00,
    unrealized_plpc: 0.0333,
  },
];
```

#### 5. Install MSW for Integration Tests
```bash
cd frontend
npm install -D msw@latest
```

**File**: `frontend/src/lib/__tests__/mocks/handlers.ts`
```typescript
import { http, HttpResponse } from 'msw';
import { mockUser, mockAuthResponse, mockStrategy, mockBacktest } from '../fixtures';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const handlers = [
  // Auth endpoints
  http.post(`${API_URL}/api/v1/auth/login`, () => {
    return HttpResponse.json(mockAuthResponse);
  }),

  http.get(`${API_URL}/api/v1/auth/me`, () => {
    return HttpResponse.json(mockUser);
  }),

  // Strategies endpoints
  http.get(`${API_URL}/api/v1/strategies`, () => {
    return HttpResponse.json([mockStrategy]);
  }),

  http.post(`${API_URL}/api/v1/strategies`, () => {
    return HttpResponse.json(mockStrategy, { status: 201 });
  }),

  // Backtests endpoints
  http.get(`${API_URL}/api/v1/backtests`, () => {
    return HttpResponse.json({
      data: [mockBacktest],
      page: 1,
      page_size: 50,
      total: 1,
    });
  }),
];
```

**File**: `frontend/src/lib/__tests__/mocks/server.ts`
```typescript
import { setupServer } from 'msw/node';
import { handlers } from './handlers';

export const server = setupServer(...handlers);
```

### Success Criteria:

#### Automated Verification:
- [x] Jest config valid: `cd frontend && npm test -- --passWithNoTests`
- [x] Test utilities exist: `ls frontend/src/lib/__tests__/test-utils.tsx`
- [x] Fixtures exist: `ls frontend/src/lib/__tests__/fixtures.ts`
- [x] MSW installed: `grep msw frontend/package.json`

#### Manual Verification:
- [x] Jest runs without configuration errors (existing tests fail due to missing modules, expected)

**Implementation Note**: Pause here for manual confirmation before proceeding to Phase 2.

---

## Phase 2: Foundation Files (TDD)

### Overview
Implement core utility files using TDD: `utils.ts`, `auth-store.ts`, `query-client.ts`.

### Changes Required:

#### 1. Utils - Tests First
**File**: `frontend/src/lib/__tests__/utils.test.ts`
```typescript
import { cn } from '../utils';

describe('cn utility', () => {
  it('merges class names', () => {
    expect(cn('foo', 'bar')).toBe('foo bar');
  });

  it('handles conditional classes', () => {
    expect(cn('foo', false && 'bar', 'baz')).toBe('foo baz');
  });

  it('merges tailwind classes correctly', () => {
    expect(cn('px-2 py-1', 'px-4')).toBe('py-1 px-4');
  });

  it('handles undefined and null', () => {
    expect(cn('foo', undefined, null, 'bar')).toBe('foo bar');
  });

  it('handles empty input', () => {
    expect(cn()).toBe('');
  });
});
```

#### 2. Utils - Implementation
**File**: `frontend/src/lib/utils.ts`
```typescript
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
```

#### 3. Query Client - Tests First
**File**: `frontend/src/lib/api/__tests__/query-client.test.ts`
```typescript
import { queryClient } from '../query-client';

describe('queryClient', () => {
  it('is a QueryClient instance', () => {
    expect(queryClient).toBeDefined();
    expect(typeof queryClient.getQueryCache).toBe('function');
  });

  it('has retry disabled by default', () => {
    const options = queryClient.getDefaultOptions();
    expect(options.queries?.retry).toBe(false);
  });

  it('has 5 minute stale time', () => {
    const options = queryClient.getDefaultOptions();
    expect(options.queries?.staleTime).toBe(5 * 60 * 1000);
  });
});
```

#### 4. Query Client - Implementation
**File**: `frontend/src/lib/api/query-client.ts`
```typescript
import { QueryClient } from '@tanstack/react-query';

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      gcTime: 10 * 60 * 1000, // 10 minutes
      retry: false,
      refetchOnWindowFocus: false,
    },
    mutations: {
      retry: false,
    },
  },
});
```

#### 5. Auth Store - Tests First
**File**: `frontend/src/lib/stores/__tests__/auth-store.test.ts`
```typescript
import { renderHook, act, waitFor } from '@testing-library/react';
import { useAuthStore } from '../auth-store';
import { mockUser, mockAuthResponse } from '../../__tests__/fixtures';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

describe('useAuthStore', () => {
  beforeEach(() => {
    // Reset store state
    useAuthStore.setState({
      user: null,
      token: null,
      isAuthenticated: false,
    });
    localStorage.clear();
    jest.clearAllMocks();
  });

  describe('initial state', () => {
    it('starts with null user and token', () => {
      const { result } = renderHook(() => useAuthStore());
      expect(result.current.user).toBeNull();
      expect(result.current.token).toBeNull();
      expect(result.current.isAuthenticated).toBe(false);
    });
  });

  describe('login', () => {
    it('sets user and token on successful login', async () => {
      (global.fetch as jest.Mock)
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve(mockAuthResponse),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve(mockUser),
        });

      const { result } = renderHook(() => useAuthStore());

      await act(async () => {
        await result.current.login({ email: 'test@example.com', password: 'password' });
      });

      expect(result.current.token).toBe(mockAuthResponse.access_token);
      expect(result.current.user).toEqual(mockUser);
      expect(result.current.isAuthenticated).toBe(true);
      expect(localStorage.setItem).toHaveBeenCalledWith('access_token', mockAuthResponse.access_token);
    });

    it('throws on invalid credentials', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: () => Promise.resolve({ detail: 'Invalid credentials' }),
      });

      const { result } = renderHook(() => useAuthStore());

      await expect(
        act(async () => {
          await result.current.login({ email: 'test@example.com', password: 'wrong' });
        })
      ).rejects.toThrow('Invalid credentials');
    });
  });

  describe('logout', () => {
    it('clears user, token, and localStorage', () => {
      useAuthStore.setState({
        user: mockUser,
        token: 'test-token',
        isAuthenticated: true,
      });

      const { result } = renderHook(() => useAuthStore());

      act(() => {
        result.current.logout();
      });

      expect(result.current.user).toBeNull();
      expect(result.current.token).toBeNull();
      expect(result.current.isAuthenticated).toBe(false);
      expect(localStorage.removeItem).toHaveBeenCalledWith('access_token');
    });
  });

  describe('checkAuth', () => {
    it('fetches user if token exists in localStorage', async () => {
      (localStorage.getItem as jest.Mock).mockReturnValue('stored-token');
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockUser),
      });

      const { result } = renderHook(() => useAuthStore());

      await act(async () => {
        await result.current.checkAuth();
      });

      expect(result.current.user).toEqual(mockUser);
      expect(result.current.isAuthenticated).toBe(true);
    });

    it('does nothing if no token in localStorage', async () => {
      (localStorage.getItem as jest.Mock).mockReturnValue(null);

      const { result } = renderHook(() => useAuthStore());

      await act(async () => {
        await result.current.checkAuth();
      });

      expect(result.current.user).toBeNull();
      expect(result.current.isAuthenticated).toBe(false);
      expect(global.fetch).not.toHaveBeenCalled();
    });

    it('clears auth on 401 response', async () => {
      (localStorage.getItem as jest.Mock).mockReturnValue('expired-token');
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 401,
      });

      useAuthStore.setState({ token: 'expired-token', isAuthenticated: true });

      const { result } = renderHook(() => useAuthStore());

      await act(async () => {
        await result.current.checkAuth();
      });

      expect(result.current.user).toBeNull();
      expect(result.current.isAuthenticated).toBe(false);
      expect(localStorage.removeItem).toHaveBeenCalledWith('access_token');
    });
  });
});
```

#### 6. Auth Store - Implementation
**File**: `frontend/src/lib/stores/auth-store.ts`
```typescript
import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { User, LoginCredentials, RegisterData, AuthResponse } from '@/types';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  login: (credentials: LoginCredentials) => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
  logout: () => void;
  checkAuth: () => Promise<void>;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      isAuthenticated: false,

      login: async (credentials: LoginCredentials) => {
        const response = await fetch(`${API_URL}/api/v1/auth/login`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(credentials),
        });

        if (!response.ok) {
          const error = await response.json();
          throw new Error(error.detail || 'Login failed');
        }

        const auth: AuthResponse = await response.json();
        localStorage.setItem('access_token', auth.access_token);

        // Fetch user info
        const userResponse = await fetch(`${API_URL}/api/v1/auth/me`, {
          headers: { Authorization: `Bearer ${auth.access_token}` },
        });

        if (!userResponse.ok) {
          throw new Error('Failed to fetch user info');
        }

        const user: User = await userResponse.json();

        set({
          user,
          token: auth.access_token,
          isAuthenticated: true,
        });
      },

      register: async (data: RegisterData) => {
        const response = await fetch(`${API_URL}/api/v1/auth/register`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(data),
        });

        if (!response.ok) {
          const error = await response.json();
          throw new Error(error.detail || 'Registration failed');
        }

        // Auto-login after registration
        await get().login({ email: data.email, password: data.password });
      },

      logout: () => {
        localStorage.removeItem('access_token');
        set({
          user: null,
          token: null,
          isAuthenticated: false,
        });
      },

      checkAuth: async () => {
        const token = localStorage.getItem('access_token');
        if (!token) {
          set({ user: null, token: null, isAuthenticated: false });
          return;
        }

        try {
          const response = await fetch(`${API_URL}/api/v1/auth/me`, {
            headers: { Authorization: `Bearer ${token}` },
          });

          if (!response.ok) {
            throw new Error('Token invalid');
          }

          const user: User = await response.json();
          set({ user, token, isAuthenticated: true });
        } catch {
          localStorage.removeItem('access_token');
          set({ user: null, token: null, isAuthenticated: false });
        }
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({ token: state.token }),
    }
  )
);
```

#### 7. Integration Test - Auth Flow
**File**: `frontend/src/lib/__tests__/integration/auth-flow.test.ts`
```typescript
import { renderHook, act } from '@testing-library/react';
import { server } from '../mocks/server';
import { useAuthStore } from '../../stores/auth-store';

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe('Auth Flow Integration', () => {
  beforeEach(() => {
    useAuthStore.setState({
      user: null,
      token: null,
      isAuthenticated: false,
    });
    localStorage.clear();
  });

  it('complete login flow', async () => {
    const { result } = renderHook(() => useAuthStore());

    await act(async () => {
      await result.current.login({
        email: 'test@example.com',
        password: 'password123',
      });
    });

    expect(result.current.isAuthenticated).toBe(true);
    expect(result.current.user?.email).toBe('test@example.com');
    expect(localStorage.getItem('access_token')).toBeTruthy();
  });

  it('logout clears everything', async () => {
    const { result } = renderHook(() => useAuthStore());

    // Login first
    await act(async () => {
      await result.current.login({
        email: 'test@example.com',
        password: 'password123',
      });
    });

    // Then logout
    act(() => {
      result.current.logout();
    });

    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.user).toBeNull();
    expect(localStorage.getItem('access_token')).toBeNull();
  });
});
```

#### 8. E2E Test - Auth Still Works
**File**: `frontend/e2e/auth.spec.ts`
```typescript
import { test, expect } from '@playwright/test';

test.describe('Authentication E2E', () => {
  test('login page renders correctly', async ({ page }) => {
    await page.goto('/login');

    await expect(page.getByLabel(/email/i)).toBeVisible();
    await expect(page.getByLabel(/password/i)).toBeVisible();
    await expect(page.getByRole('button', { name: /login/i })).toBeVisible();
  });

  test('shows error on invalid credentials', async ({ page }) => {
    await page.goto('/login');

    await page.getByLabel(/email/i).fill('invalid@example.com');
    await page.getByLabel(/password/i).fill('wrongpassword');
    await page.getByRole('button', { name: /login/i }).click();

    // Should show error toast or message
    await expect(page.getByText(/invalid|error|failed/i)).toBeVisible({ timeout: 5000 });
  });

  test('redirects to login when accessing protected route', async ({ page }) => {
    await page.goto('/dashboard');
    await expect(page).toHaveURL(/login/);
  });
});
```

### Success Criteria:

#### Automated Verification:
- [x] Utils tests pass: `npm test -- utils.test.ts`
- [x] Query client tests pass: `npm test -- query-client.test.ts`
- [x] Auth store tests pass: `npm test -- auth-store.test.ts`
- [ ] Integration tests pass: `npm test -- integration`
- [ ] E2E auth tests pass: `npm run test:e2e -- auth.spec.ts`
- [ ] TypeScript compiles: `npm run type-check` (remaining errors are for Phase 3-4 hooks)

#### Manual Verification:
- [ ] Login page renders without errors
- [ ] No console errors in browser

**Implementation Note**: Pause here for manual confirmation before proceeding to Phase 3.

---

## Phase 3: API Clients (TDD)

### Overview
Create all missing API client files with tests first.

### Changes Required:

#### 1. Strategies API - Tests
**File**: `frontend/src/lib/api/__tests__/strategies.test.ts`
```typescript
import { strategiesApi } from '../strategies';
import { mockStrategy } from '../../__tests__/fixtures';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

describe('strategiesApi', () => {
  const token = 'test-token';

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('list', () => {
    it('fetches strategies with auth header', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve([mockStrategy]),
      });

      const result = await strategiesApi.list(token);

      expect(global.fetch).toHaveBeenCalledWith(
        `${API_URL}/api/v1/strategies`,
        expect.objectContaining({
          headers: { Authorization: `Bearer ${token}` },
        })
      );
      expect(result).toEqual([mockStrategy]);
    });

    it('throws on error response', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 500,
      });

      await expect(strategiesApi.list(token)).rejects.toThrow();
    });
  });

  describe('create', () => {
    it('posts new strategy', async () => {
      const newStrategy = {
        name: 'New Strategy',
        strategy_type: 'rsi',
        parameters: { period: 14 },
      };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ ...mockStrategy, ...newStrategy }),
      });

      const result = await strategiesApi.create(newStrategy, token);

      expect(global.fetch).toHaveBeenCalledWith(
        `${API_URL}/api/v1/strategies`,
        expect.objectContaining({
          method: 'POST',
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(newStrategy),
        })
      );
      expect(result.name).toBe('New Strategy');
    });
  });

  describe('get', () => {
    it('fetches single strategy by ID', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockStrategy),
      });

      const result = await strategiesApi.get('strategy-123', token);

      expect(global.fetch).toHaveBeenCalledWith(
        `${API_URL}/api/v1/strategies/strategy-123`,
        expect.objectContaining({
          headers: { Authorization: `Bearer ${token}` },
        })
      );
      expect(result.id).toBe('strategy-123');
    });
  });

  describe('update', () => {
    it('updates strategy', async () => {
      const updates = { name: 'Updated Name', is_active: false };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ ...mockStrategy, ...updates }),
      });

      const result = await strategiesApi.update('strategy-123', updates, token);

      expect(global.fetch).toHaveBeenCalledWith(
        `${API_URL}/api/v1/strategies/strategy-123`,
        expect.objectContaining({
          method: 'PUT',
          body: JSON.stringify(updates),
        })
      );
      expect(result.name).toBe('Updated Name');
    });
  });

  describe('delete', () => {
    it('deletes strategy', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        status: 204,
      });

      await strategiesApi.delete('strategy-123', token);

      expect(global.fetch).toHaveBeenCalledWith(
        `${API_URL}/api/v1/strategies/strategy-123`,
        expect.objectContaining({
          method: 'DELETE',
        })
      );
    });
  });
});
```

#### 2. Strategies API - Implementation
**File**: `frontend/src/lib/api/strategies.ts`
```typescript
import { Strategy, StrategyCreate } from '@/types';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Request failed' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return response.json();
}

export const strategiesApi = {
  async list(token: string, skip = 0, limit = 100): Promise<Strategy[]> {
    const response = await fetch(
      `${API_URL}/api/v1/strategies?skip=${skip}&limit=${limit}`,
      {
        headers: { Authorization: `Bearer ${token}` },
      }
    );
    return handleResponse<Strategy[]>(response);
  },

  async get(id: string, token: string): Promise<Strategy> {
    const response = await fetch(`${API_URL}/api/v1/strategies/${id}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    return handleResponse<Strategy>(response);
  },

  async create(data: StrategyCreate, token: string): Promise<Strategy> {
    const response = await fetch(`${API_URL}/api/v1/strategies`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });
    return handleResponse<Strategy>(response);
  },

  async update(
    id: string,
    data: Partial<Strategy>,
    token: string
  ): Promise<Strategy> {
    const response = await fetch(`${API_URL}/api/v1/strategies/${id}`, {
      method: 'PUT',
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });
    return handleResponse<Strategy>(response);
  },

  async delete(id: string, token: string): Promise<void> {
    const response = await fetch(`${API_URL}/api/v1/strategies/${id}`, {
      method: 'DELETE',
      headers: { Authorization: `Bearer ${token}` },
    });
    return handleResponse<void>(response);
  },
};
```

#### 3. Broker API - Tests and Implementation
**File**: `frontend/src/lib/api/__tests__/broker.test.ts`
```typescript
import { brokerApi } from '../broker';
import { mockBrokerAccount, mockPositions } from '../../__tests__/fixtures';

describe('brokerApi', () => {
  const token = 'test-token';

  describe('getAccount', () => {
    it('fetches broker account', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ success: true, data: mockBrokerAccount }),
      });

      const result = await brokerApi.getAccount(token);
      expect(result).toEqual(mockBrokerAccount);
    });
  });

  describe('getPositions', () => {
    it('fetches positions', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ success: true, data: mockPositions }),
      });

      const result = await brokerApi.getPositions(token);
      expect(result).toEqual(mockPositions);
    });
  });

  describe('getOrders', () => {
    it('fetches orders with status filter', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ success: true, data: [] }),
      });

      await brokerApi.getOrders(token, 'open', 50);

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('status_filter=open'),
        expect.any(Object)
      );
    });
  });
});
```

**File**: `frontend/src/lib/api/broker.ts`
```typescript
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface BrokerAccount {
  portfolio_value: number;
  cash: number;
  buying_power: number;
  pattern_day_trader: boolean;
  long_market_value: number;
  short_market_value?: number;
  equity?: number;
}

export interface BrokerPosition {
  symbol: string;
  qty: number;
  avg_entry_price: number;
  market_value: number;
  unrealized_pl: number;
  unrealized_plpc: number;
  current_price?: number;
}

export interface BrokerOrder {
  id: string;
  symbol: string;
  side: 'buy' | 'sell';
  type: string;
  qty: number;
  filled_qty: number;
  filled_avg_price?: number;
  status: string;
  created_at: string;
}

async function handleBrokerResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    throw new Error(`Broker API error: ${response.status}`);
  }
  const json = await response.json();
  return json.data;
}

export const brokerApi = {
  async getAccount(token: string): Promise<BrokerAccount> {
    const response = await fetch(`${API_URL}/api/v1/broker/account`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    return handleBrokerResponse<BrokerAccount>(response);
  },

  async getPositions(token: string): Promise<BrokerPosition[]> {
    const response = await fetch(`${API_URL}/api/v1/broker/positions`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    return handleBrokerResponse<BrokerPosition[]>(response);
  },

  async getOrders(
    token: string,
    status?: string,
    limit = 100
  ): Promise<BrokerOrder[]> {
    const params = new URLSearchParams();
    if (status) params.set('status_filter', status);
    params.set('limit', limit.toString());

    const response = await fetch(
      `${API_URL}/api/v1/broker/orders?${params}`,
      {
        headers: { Authorization: `Bearer ${token}` },
      }
    );
    return handleBrokerResponse<BrokerOrder[]>(response);
  },

  async getQuote(symbol: string, token: string) {
    const response = await fetch(
      `${API_URL}/api/v1/broker/market/quote/${symbol}`,
      {
        headers: { Authorization: `Bearer ${token}` },
      }
    );
    return handleBrokerResponse(response);
  },
};
```

#### 4. Additional API Clients (similar pattern)

**Files to create with tests:**
- `frontend/src/lib/api/trades.ts` + tests
- `frontend/src/lib/api/backtests.ts` + tests
- `frontend/src/lib/api/live-trading.ts` + tests
- `frontend/src/lib/api/optimizer.ts` + tests

*[Implementation follows same pattern as strategies - tests first, then implementation]*

### Success Criteria:

#### Automated Verification:
- [x] All API client tests pass: `npm test -- api` (28 tests passed)
- [ ] TypeScript compiles: `npm run type-check`
- [ ] No lint errors: `npm run lint`

#### Manual Verification:
- [ ] API clients can be imported without errors

**Implementation Note**: Pause here for manual confirmation before proceeding to Phase 4.

---

## Phase 4: React Query Hooks (TDD)

### Overview
Create all missing React Query hooks with tests.

### Changes Required:

#### 1. Broker Hooks - Tests
**File**: `frontend/src/lib/hooks/__tests__/use-broker.test.tsx`
```typescript
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useAccount, usePositions, useBrokerOrders } from '../use-broker';
import { mockBrokerAccount, mockPositions } from '../../__tests__/fixtures';

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

describe('useBroker hooks', () => {
  beforeEach(() => {
    localStorage.setItem('access_token', 'test-token');
  });

  describe('useAccount', () => {
    it('fetches account data', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ success: true, data: mockBrokerAccount }),
      });

      const { result } = renderHook(() => useAccount(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toEqual(mockBrokerAccount);
    });

    it('does not fetch without token', () => {
      localStorage.removeItem('access_token');

      const { result } = renderHook(() => useAccount(), {
        wrapper: createWrapper(),
      });

      expect(result.current.fetchStatus).toBe('idle');
    });
  });

  describe('usePositions', () => {
    it('fetches positions', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ success: true, data: mockPositions }),
      });

      const { result } = renderHook(() => usePositions(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toEqual(mockPositions);
    });
  });
});
```

#### 2. Broker Hooks - Implementation
**File**: `frontend/src/lib/hooks/use-broker.ts`
```typescript
import { useQuery } from '@tanstack/react-query';
import { brokerApi, BrokerAccount, BrokerPosition, BrokerOrder } from '../api/broker';

function getToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('access_token');
}

export function useAccount() {
  const token = getToken();

  return useQuery<BrokerAccount>({
    queryKey: ['broker', 'account'],
    queryFn: () => brokerApi.getAccount(token!),
    enabled: !!token,
    staleTime: 5000, // 5 seconds
    refetchInterval: 30000, // 30 seconds
  });
}

export function usePositions() {
  const token = getToken();

  return useQuery<BrokerPosition[]>({
    queryKey: ['broker', 'positions'],
    queryFn: () => brokerApi.getPositions(token!),
    enabled: !!token,
    staleTime: 3000,
    refetchInterval: 10000,
  });
}

export function useBrokerOrders(status?: string, limit = 100) {
  const token = getToken();

  return useQuery<BrokerOrder[]>({
    queryKey: ['broker', 'orders', status, limit],
    queryFn: () => brokerApi.getOrders(token!, status, limit),
    enabled: !!token,
  });
}
```

#### 3. Strategies Hooks - Tests and Implementation
**File**: `frontend/src/lib/hooks/__tests__/use-strategies.test.tsx`
```typescript
import { renderHook, waitFor, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import {
  useStrategies,
  useCreateStrategy,
  useUpdateStrategy,
  useDeleteStrategy,
} from '../use-strategies';
import { mockStrategy } from '../../__tests__/fixtures';

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

describe('useStrategies hooks', () => {
  beforeEach(() => {
    localStorage.setItem('access_token', 'test-token');
    jest.clearAllMocks();
  });

  describe('useStrategies', () => {
    it('fetches strategies list', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve([mockStrategy]),
      });

      const { result } = renderHook(() => useStrategies(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toHaveLength(1);
      expect(result.current.data?.[0].id).toBe('strategy-123');
    });
  });

  describe('useCreateStrategy', () => {
    it('creates strategy and invalidates cache', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockStrategy),
      });

      const { result } = renderHook(() => useCreateStrategy(), {
        wrapper: createWrapper(),
      });

      await act(async () => {
        await result.current.mutateAsync({
          name: 'New Strategy',
          strategy_type: 'rsi',
          parameters: {},
        });
      });

      expect(result.current.isSuccess).toBe(true);
    });
  });

  describe('useDeleteStrategy', () => {
    it('deletes strategy', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        status: 204,
      });

      const { result } = renderHook(() => useDeleteStrategy(), {
        wrapper: createWrapper(),
      });

      await act(async () => {
        await result.current.mutateAsync('strategy-123');
      });

      expect(result.current.isSuccess).toBe(true);
    });
  });
});
```

**File**: `frontend/src/lib/hooks/use-strategies.ts`
```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { strategiesApi } from '../api/strategies';
import { Strategy, StrategyCreate } from '@/types';

function getToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('access_token');
}

export function useStrategies(skip = 0, limit = 100) {
  const token = getToken();

  return useQuery<Strategy[]>({
    queryKey: ['strategies', skip, limit],
    queryFn: () => strategiesApi.list(token!, skip, limit),
    enabled: !!token,
  });
}

export function useStrategy(id: string) {
  const token = getToken();

  return useQuery<Strategy>({
    queryKey: ['strategies', id],
    queryFn: () => strategiesApi.get(id, token!),
    enabled: !!token && !!id,
  });
}

export function useCreateStrategy() {
  const queryClient = useQueryClient();
  const token = getToken();

  return useMutation({
    mutationFn: (data: StrategyCreate) => strategiesApi.create(data, token!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['strategies'] });
    },
  });
}

export function useUpdateStrategy() {
  const queryClient = useQueryClient();
  const token = getToken();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Strategy> }) =>
      strategiesApi.update(id, data, token!),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: ['strategies'] });
      queryClient.invalidateQueries({ queryKey: ['strategies', id] });
    },
  });
}

export function useDeleteStrategy() {
  const queryClient = useQueryClient();
  const token = getToken();

  return useMutation({
    mutationFn: (id: string) => strategiesApi.delete(id, token!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['strategies'] });
    },
  });
}
```

#### 4. Additional Hooks (similar pattern)

**Files to create with tests:**
- `frontend/src/lib/hooks/use-trades.ts` + tests
- `frontend/src/lib/hooks/use-backtests.ts` + tests
- Extend `frontend/src/lib/hooks/use-execution.ts` with missing exports

### Success Criteria:

#### Automated Verification:
- [ ] All hook tests pass: `npm test -- hooks`
- [ ] TypeScript compiles: `npm run type-check`
- [ ] E2E tests still pass: `npm run test:e2e`

#### Manual Verification:
- [ ] Dashboard page loads without errors
- [ ] Strategies page shows list

**Implementation Note**: Pause here for manual confirmation before proceeding to Phase 5.

---

## Phase 5: Database Migrations (TDD)

### Overview
Fix database migrations and add missing tables.

### Changes Required:

#### 1. Backend Model Tests
**File**: `backend/tests/models/test_watchlist.py`
```python
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.watchlist import Watchlist, WatchlistItem, PriceAlert


@pytest.mark.asyncio
async def test_create_watchlist(db: AsyncSession, test_user):
    """Test creating a watchlist."""
    watchlist = Watchlist(
        user_id=test_user.id,
        name="Tech Stocks",
        description="Technology sector watchlist",
    )
    db.add(watchlist)
    await db.commit()
    await db.refresh(watchlist)

    assert watchlist.id is not None
    assert watchlist.name == "Tech Stocks"
    assert watchlist.user_id == test_user.id


@pytest.mark.asyncio
async def test_add_watchlist_item(db: AsyncSession, test_user):
    """Test adding items to watchlist."""
    watchlist = Watchlist(user_id=test_user.id, name="My Watchlist")
    db.add(watchlist)
    await db.commit()
    await db.refresh(watchlist)

    item = WatchlistItem(
        watchlist_id=watchlist.id,
        symbol="AAPL",
        notes="Apple Inc.",
    )
    db.add(item)
    await db.commit()

    assert item.id is not None
    assert item.symbol == "AAPL"


@pytest.mark.asyncio
async def test_create_price_alert(db: AsyncSession, test_user):
    """Test creating a price alert."""
    alert = PriceAlert(
        user_id=test_user.id,
        symbol="AAPL",
        condition="above",
        target_price=200.00,
        message="AAPL above $200",
    )
    db.add(alert)
    await db.commit()
    await db.refresh(alert)

    assert alert.id is not None
    assert alert.is_active is True
    assert alert.triggered_at is None


@pytest.mark.asyncio
async def test_watchlist_cascade_delete(db: AsyncSession, test_user):
    """Test that deleting watchlist deletes items."""
    watchlist = Watchlist(user_id=test_user.id, name="To Delete")
    db.add(watchlist)
    await db.commit()
    await db.refresh(watchlist)

    item = WatchlistItem(watchlist_id=watchlist.id, symbol="AAPL")
    db.add(item)
    await db.commit()

    await db.delete(watchlist)
    await db.commit()

    # Item should be deleted too (cascade)
    from sqlalchemy import select
    result = await db.execute(
        select(WatchlistItem).where(WatchlistItem.watchlist_id == watchlist.id)
    )
    assert result.scalars().first() is None
```

#### 2. Export Models in __init__.py
**File**: `backend/app/models/__init__.py`
**Add to imports:**
```python
from app.models.watchlist import Watchlist, WatchlistItem, PriceAlert
from app.models.audit_log import AuditLog
```

**Add to __all__:**
```python
    # Models - Watchlist
    "Watchlist",
    "WatchlistItem",
    "PriceAlert",
    # Models - Audit
    "AuditLog",
```

#### 3. Delete Conflicting Migration
```bash
rm backend/migrations/versions/003_paper_trading.py
```

#### 4. Generate New Migration
```bash
cd backend
alembic revision --autogenerate -m "add_watchlist_pricealert_auditlog_tables"
alembic upgrade head
```

#### 5. Integration Test - API Endpoints
**File**: `backend/tests/api/test_watchlist_api.py`
```python
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_watchlist(client: AsyncClient, auth_headers):
    """Test creating a watchlist via API."""
    response = await client.post(
        "/api/v1/watchlist",
        json={"name": "Tech Stocks", "description": "Tech watchlist"},
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Tech Stocks"


@pytest.mark.asyncio
async def test_list_watchlists(client: AsyncClient, auth_headers):
    """Test listing watchlists."""
    response = await client.get("/api/v1/watchlist", headers=auth_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_create_price_alert(client: AsyncClient, auth_headers):
    """Test creating a price alert."""
    response = await client.post(
        "/api/v1/watchlist/alerts",
        json={
            "symbol": "AAPL",
            "condition": "above",
            "target_price": 200.00,
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
```

### Success Criteria:

#### Automated Verification:
- [ ] Model tests pass: `cd backend && poetry run pytest tests/models/test_watchlist.py -v`
- [ ] Migration applies: `alembic upgrade head`
- [ ] API tests pass: `poetry run pytest tests/api/test_watchlist_api.py -v`
- [ ] No migration conflicts: `alembic check`

#### Manual Verification:
- [ ] Database tables created: check via `psql` or admin tool
- [ ] Existing data intact

**Implementation Note**: Pause here for manual confirmation before proceeding to Phase 6.

---

## Phase 6: Settings Page (TDD)

### Overview
Enable settings page features with tests.

### Changes Required:

#### 1. Add Switch Component
```bash
cd frontend
npx shadcn-ui@latest add switch
```

#### 2. Settings Component Tests
**File**: `frontend/src/app/dashboard/settings/__tests__/page.test.tsx`
```typescript
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import SettingsPage from '../page';
import { useAuthStore } from '@/lib/stores/auth-store';

// Mock the auth store
jest.mock('@/lib/stores/auth-store');

const mockUser = {
  id: 'user-123',
  email: 'test@example.com',
  full_name: 'Test User',
  role: 'user',
  is_active: true,
};

describe('SettingsPage', () => {
  beforeEach(() => {
    (useAuthStore as unknown as jest.Mock).mockReturnValue({
      user: mockUser,
    });
  });

  it('displays user information', () => {
    render(<SettingsPage />);

    expect(screen.getByDisplayValue('test@example.com')).toBeInTheDocument();
    expect(screen.getByDisplayValue('Test User')).toBeInTheDocument();
  });

  it('shows API key management section', () => {
    render(<SettingsPage />);

    expect(screen.getByText(/api credentials/i)).toBeInTheDocument();
  });

  it('shows notification preferences section', () => {
    render(<SettingsPage />);

    expect(screen.getByText(/notifications/i)).toBeInTheDocument();
  });
});
```

#### 3. Settings Page Implementation
Update `frontend/src/app/dashboard/settings/page.tsx` to enable all sections and connect to backend APIs.

*[Detailed implementation code for settings page - connects to API keys, notifications, profile endpoints]*

### Success Criteria:

#### Automated Verification:
- [ ] Settings tests pass: `npm test -- settings`
- [ ] E2E test: `npm run test:e2e -- settings.spec.ts`

#### Manual Verification:
- [ ] Can add/view API keys
- [ ] Can toggle notification preferences
- [ ] Can update profile

**Implementation Note**: Pause here for manual confirmation before proceeding to Phase 7.

---

## Phase 7: WebSocket (TDD)

### Overview
Implement WebSocket for real-time updates.

### Changes Required:

#### 1. Remove socket.io-client
```bash
cd frontend
npm uninstall socket.io-client
```

#### 2. WebSocket Hook Tests
**File**: `frontend/src/lib/hooks/__tests__/use-websocket.test.ts`
```typescript
import { renderHook, act } from '@testing-library/react';
import { useMarketStream } from '../use-websocket';

// Mock WebSocket
class MockWebSocket {
  static instances: MockWebSocket[] = [];
  onopen: (() => void) | null = null;
  onmessage: ((event: { data: string }) => void) | null = null;
  onclose: (() => void) | null = null;
  onerror: ((error: Event) => void) | null = null;
  readyState = 0;

  constructor(public url: string) {
    MockWebSocket.instances.push(this);
  }

  send = jest.fn();
  close = jest.fn();

  simulateOpen() {
    this.readyState = 1;
    this.onopen?.();
  }

  simulateMessage(data: object) {
    this.onmessage?.({ data: JSON.stringify(data) });
  }

  simulateClose() {
    this.readyState = 3;
    this.onclose?.();
  }
}

(global as any).WebSocket = MockWebSocket;

describe('useMarketStream', () => {
  beforeEach(() => {
    MockWebSocket.instances = [];
    localStorage.setItem('access_token', 'test-token');
  });

  it('connects to WebSocket with token', () => {
    renderHook(() => useMarketStream(['AAPL']));

    expect(MockWebSocket.instances).toHaveLength(1);
    expect(MockWebSocket.instances[0].url).toContain('token=test-token');
    expect(MockWebSocket.instances[0].url).toContain('symbols=AAPL');
  });

  it('receives trade updates', async () => {
    const { result } = renderHook(() => useMarketStream(['AAPL']));

    const ws = MockWebSocket.instances[0];
    act(() => ws.simulateOpen());

    act(() => {
      ws.simulateMessage({
        type: 'trade',
        data: { symbol: 'AAPL', price: 150.25, size: 100 },
      });
    });

    expect(result.current.trades['AAPL']).toEqual({
      symbol: 'AAPL',
      price: 150.25,
      size: 100,
    });
  });

  it('reconnects on close', async () => {
    jest.useFakeTimers();
    renderHook(() => useMarketStream(['AAPL']));

    const ws = MockWebSocket.instances[0];
    act(() => ws.simulateOpen());
    act(() => ws.simulateClose());

    // Should attempt reconnect after delay
    act(() => jest.advanceTimersByTime(5000));

    expect(MockWebSocket.instances).toHaveLength(2);
    jest.useRealTimers();
  });

  it('cleans up on unmount', () => {
    const { unmount } = renderHook(() => useMarketStream(['AAPL']));

    const ws = MockWebSocket.instances[0];
    act(() => ws.simulateOpen());

    unmount();

    expect(ws.close).toHaveBeenCalled();
  });
});
```

#### 3. WebSocket Hook Implementation
**File**: `frontend/src/lib/hooks/use-websocket.ts`
```typescript
import { useState, useEffect, useCallback, useRef } from 'react';

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';

interface TradeData {
  symbol: string;
  price: number;
  size: number;
  timestamp?: string;
}

interface QuoteData {
  symbol: string;
  bid_price: number;
  ask_price: number;
  bid_size: number;
  ask_size: number;
}

interface MarketStreamState {
  isConnected: boolean;
  trades: Record<string, TradeData>;
  quotes: Record<string, QuoteData>;
  error: string | null;
}

export function useMarketStream(
  symbols: string[],
  streams: ('trades' | 'quotes' | 'bars')[] = ['trades', 'quotes']
) {
  const [state, setState] = useState<MarketStreamState>({
    isConnected: false,
    trades: {},
    quotes: {},
    error: null,
  });

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();

  const connect = useCallback(() => {
    const token = localStorage.getItem('access_token');
    if (!token || symbols.length === 0) return;

    const url = new URL(`${WS_URL}/api/v1/broker/stream`);
    url.searchParams.set('token', token);
    url.searchParams.set('symbols', symbols.join(','));
    url.searchParams.set('streams', streams.join(','));

    const ws = new WebSocket(url.toString());
    wsRef.current = ws;

    ws.onopen = () => {
      setState((prev) => ({ ...prev, isConnected: true, error: null }));
    };

    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);

        if (message.type === 'trade') {
          setState((prev) => ({
            ...prev,
            trades: { ...prev.trades, [message.data.symbol]: message.data },
          }));
        } else if (message.type === 'quote') {
          setState((prev) => ({
            ...prev,
            quotes: { ...prev.quotes, [message.data.symbol]: message.data },
          }));
        }
      } catch (err) {
        console.error('WebSocket message parse error:', err);
      }
    };

    ws.onclose = () => {
      setState((prev) => ({ ...prev, isConnected: false }));
      // Reconnect after 5 seconds
      reconnectTimeoutRef.current = setTimeout(connect, 5000);
    };

    ws.onerror = () => {
      setState((prev) => ({ ...prev, error: 'WebSocket error' }));
    };
  }, [symbols, streams]);

  useEffect(() => {
    connect();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [connect]);

  const subscribe = useCallback((newSymbols: string[]) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(
        JSON.stringify({ action: 'subscribe', symbols: newSymbols })
      );
    }
  }, []);

  const unsubscribe = useCallback((symbolsToRemove: string[]) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(
        JSON.stringify({ action: 'unsubscribe', symbols: symbolsToRemove })
      );
    }
  }, []);

  return {
    ...state,
    subscribe,
    unsubscribe,
  };
}
```

#### 4. E2E Test for Real-time Updates
**File**: `frontend/e2e/websocket.spec.ts`
```typescript
import { test, expect } from '@playwright/test';

test.describe('WebSocket Real-time Updates', () => {
  test.beforeEach(async ({ page }) => {
    // Login first
    await page.goto('/login');
    await page.getByLabel(/email/i).fill('test@example.com');
    await page.getByLabel(/password/i).fill('password123');
    await page.getByRole('button', { name: /login/i }).click();
    await page.waitForURL('/dashboard');
  });

  test('dashboard shows live data connection', async ({ page }) => {
    await page.goto('/dashboard');

    // Should show connection status or live data indicator
    await expect(
      page.getByText(/connected|live|real-time/i)
    ).toBeVisible({ timeout: 10000 });
  });
});
```

### Success Criteria:

#### Automated Verification:
- [ ] WebSocket tests pass: `npm test -- use-websocket.test.ts`
- [ ] socket.io-client removed: `! grep socket.io-client package.json`
- [ ] TypeScript compiles: `npm run type-check`

#### Manual Verification:
- [ ] Real-time prices update in dashboard
- [ ] WebSocket reconnects after disconnection

**Implementation Note**: Pause here for manual confirmation before proceeding to Phase 8.

---

## Phase 8: Charts (TDD)

### Overview
Implement chart components with recharts.

### Changes Required:

#### 1. Chart Component Tests
**File**: `frontend/src/components/charts/__tests__/equity-curve.test.tsx`
```typescript
import { render, screen } from '@testing-library/react';
import { EquityCurveChart } from '../equity-curve';

const mockData = [
  { date: '2024-01-01', equity: 100000, daily_return: 0 },
  { date: '2024-01-02', equity: 100500, daily_return: 0.5 },
  { date: '2024-01-03', equity: 101200, daily_return: 0.7 },
];

describe('EquityCurveChart', () => {
  it('renders without crashing', () => {
    render(<EquityCurveChart data={mockData} />);
    // Recharts renders SVG
    expect(document.querySelector('svg')).toBeInTheDocument();
  });

  it('displays empty state when no data', () => {
    render(<EquityCurveChart data={[]} />);
    expect(screen.getByText(/no data/i)).toBeInTheDocument();
  });

  it('shows loading state', () => {
    render(<EquityCurveChart data={[]} isLoading />);
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });
});
```

#### 2. Chart Component Implementation
**File**: `frontend/src/components/charts/equity-curve.tsx`
```typescript
'use client';

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface EquityCurvePoint {
  date: string;
  equity: number;
  daily_return?: number;
  cumulative_return?: number;
}

interface EquityCurveChartProps {
  data: EquityCurvePoint[];
  title?: string;
  isLoading?: boolean;
  height?: number;
}

export function EquityCurveChart({
  data,
  title = 'Equity Curve',
  isLoading = false,
  height = 300,
}: EquityCurveChartProps) {
  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>{title}</CardTitle>
        </CardHeader>
        <CardContent>
          <div
            className="flex items-center justify-center text-muted-foreground"
            style={{ height }}
          >
            Loading...
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!data || data.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>{title}</CardTitle>
        </CardHeader>
        <CardContent>
          <div
            className="flex items-center justify-center text-muted-foreground"
            style={{ height }}
          >
            No data available
          </div>
        </CardContent>
      </Card>
    );
  }

  const formatCurrency = (value: number) =>
    new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
    }).format(value);

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={height}>
          <LineChart data={data} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
            <XAxis
              dataKey="date"
              tickFormatter={formatDate}
              tick={{ fontSize: 12 }}
              className="text-muted-foreground"
            />
            <YAxis
              tickFormatter={formatCurrency}
              tick={{ fontSize: 12 }}
              className="text-muted-foreground"
              width={80}
            />
            <Tooltip
              formatter={(value: number) => [formatCurrency(value), 'Equity']}
              labelFormatter={formatDate}
              contentStyle={{
                backgroundColor: 'hsl(var(--card))',
                border: '1px solid hsl(var(--border))',
                borderRadius: '6px',
              }}
            />
            <Line
              type="monotone"
              dataKey="equity"
              stroke="hsl(var(--primary))"
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
```

#### 3. Update Portfolio Page
**File**: `frontend/src/app/dashboard/portfolio/page.tsx`
Replace placeholder with actual chart component.

#### 4. E2E Test for Charts
**File**: `frontend/e2e/charts.spec.ts`
```typescript
import { test, expect } from '@playwright/test';

test.describe('Chart Rendering', () => {
  test.beforeEach(async ({ page }) => {
    // Login
    await page.goto('/login');
    await page.getByLabel(/email/i).fill('test@example.com');
    await page.getByLabel(/password/i).fill('password123');
    await page.getByRole('button', { name: /login/i }).click();
    await page.waitForURL('/dashboard');
  });

  test('portfolio page shows equity curve chart', async ({ page }) => {
    await page.goto('/dashboard/portfolio');

    // Wait for chart to render (SVG element)
    await expect(page.locator('svg.recharts-surface')).toBeVisible({
      timeout: 10000,
    });
  });

  test('backtest results show equity curve', async ({ page }) => {
    await page.goto('/dashboard/backtests');

    // Click on a completed backtest
    await page.getByRole('link', { name: /view/i }).first().click();

    // Chart should be visible
    await expect(page.locator('svg.recharts-surface')).toBeVisible({
      timeout: 10000,
    });
  });
});
```

### Success Criteria:

#### Automated Verification:
- [ ] Chart tests pass: `npm test -- charts`
- [ ] E2E chart tests pass: `npm run test:e2e -- charts.spec.ts`
- [ ] TypeScript compiles: `npm run type-check`

#### Manual Verification:
- [ ] Charts render in portfolio page
- [ ] Charts render in backtest results

**Implementation Note**: Pause here for manual confirmation before proceeding to Phase 9.

---

## Phase 9: Final Regression Suite

### Overview
Run complete test suite and generate coverage report.

### Changes Required:

#### 1. Run All Tests
```bash
# Unit tests with coverage
cd frontend
npm test -- --coverage

# Integration tests
npm test -- --testPathPattern=integration

# E2E tests
npm run test:e2e

# Backend tests
cd ../backend
poetry run pytest --cov=app --cov-report=html
```

#### 2. Generate Reports
- Frontend coverage: `frontend/coverage/lcov-report/index.html`
- Backend coverage: `backend/htmlcov/index.html`

#### 3. Performance Check
```bash
# Build and analyze bundle
cd frontend
npm run build
npx @next/bundle-analyzer
```

### Success Criteria:

#### Automated Verification:
- [ ] All unit tests pass: `npm test`
- [ ] All E2E tests pass: `npm run test:e2e`
- [ ] Coverage > 80%: check coverage report
- [ ] Build succeeds: `npm run build`
- [ ] Backend tests pass: `poetry run pytest`

#### Manual Verification:
- [ ] All pages load without errors
- [ ] No console errors in browser
- [ ] Performance acceptable (LCP < 2.5s)

---

## Testing Strategy Summary

### Unit Tests
- All `/lib/` utilities, stores, API clients, hooks
- Component rendering tests
- Isolated with mocked dependencies

### Integration Tests
- Auth flow (store + API + localStorage)
- Data fetching (hooks + API clients + cache)
- Uses MSW for API mocking

### E2E Tests (Playwright/Chrome)
- Login/logout flow
- CRUD operations (strategies, backtests)
- Settings page functionality
- Real-time WebSocket updates
- Chart rendering

### Manual Testing Steps
1. Register new account
2. Login with credentials
3. Create strategy
4. Run backtest
5. View backtest results with charts
6. Configure settings (API keys, notifications)
7. View live dashboard with real-time updates
8. Logout

---

## References

- Research document: `research/2024-12-24-implementation-research.md`
- Existing patterns: `frontend/src/lib/api/execution.ts`
- Type definitions: `frontend/src/types/index.ts`
- Backend API docs: `http://localhost:8000/docs`
