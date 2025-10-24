# Algo Trading Platform - Frontend

Next.js 14 frontend application for the algo trading platform.

## Features

- ✅ Next.js 14 with App Router
- ✅ TypeScript for type safety
- ✅ Tailwind CSS + shadcn/ui components
- ✅ React Query for server state management
- ✅ Zustand for client state management
- ✅ Socket.IO for real-time updates
- ✅ React Hook Form + Zod validation
- ✅ Recharts for data visualization

## Project Structure

```
frontend/
├── src/
│   ├── app/                    # Next.js 14 app directory
│   │   ├── (auth)/            # Auth layout group
│   │   │   ├── login/
│   │   │   └── register/
│   │   ├── (dashboard)/       # Dashboard layout group
│   │   │   ├── dashboard/
│   │   │   ├── strategies/
│   │   │   ├── trades/
│   │   │   └── backtest/
│   │   ├── layout.tsx         # Root layout
│   │   └── page.tsx           # Landing page
│   ├── components/
│   │   ├── ui/                # shadcn/ui components
│   │   ├── layout/            # Layout components
│   │   └── features/          # Feature-specific components
│   ├── lib/
│   │   ├── api/               # API client
│   │   ├── stores/            # Zustand stores
│   │   ├── hooks/             # Custom hooks
│   │   └── utils/             # Utility functions
│   └── types/                 # TypeScript types
├── public/                    # Static assets
├── package.json
├── tsconfig.json
├── tailwind.config.js
├── next.config.js
└── README.md
```

## Prerequisites

- Node.js 20+
- npm, yarn, or pnpm
- Backend API running on http://localhost:8000

## Setup

### 1. Install Dependencies

```bash
# Using npm
npm install

# Using yarn
yarn install

# Using pnpm
pnpm install
```

### 2. Configure Environment

```bash
# Copy example environment file
cp .env.local.example .env.local

# Edit .env.local with your API URL
# NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 3. Run Development Server

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## Available Scripts

```bash
# Development server
npm run dev

# Production build
npm run build

# Start production server
npm run start

# Lint code
npm run lint

# Type check
npm run type-check
```

## Key Technologies

### Next.js 14 (App Router)
- Server and client components
- File-based routing
- Built-in optimizations
- TypeScript support

### State Management
- **Zustand**: Global client state (auth, UI)
- **React Query**: Server state (API data, caching)

### Styling
- **Tailwind CSS**: Utility-first CSS
- **shadcn/ui**: Accessible component library
- **CSS Variables**: Theme customization

### Forms & Validation
- **React Hook Form**: Performant forms
- **Zod**: TypeScript-first validation

### Data Visualization
- **Recharts**: Charts for trading data
- **TradingView**: Advanced charting (optional)

## API Integration

### Authentication Flow

```typescript
// Login
POST /api/v1/auth/login
Body: { email, password }
Response: { access_token, refresh_token }

// Store tokens in Zustand store
// Add token to axios interceptor
// Redirect to dashboard
```

### API Client

```typescript
// src/lib/api/client.ts
import axios from 'axios';

export const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
});

// Request interceptor for auth token
api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
```

### React Query Usage

```typescript
// Fetch strategies
const { data, isLoading } = useQuery({
  queryKey: ['strategies'],
  queryFn: () => api.get('/api/v1/strategies'),
});

// Create strategy
const mutation = useMutation({
  mutationFn: (data) => api.post('/api/v1/strategies', data),
  onSuccess: () => queryClient.invalidateQueries(['strategies']),
});
```

## WebSocket Integration

```typescript
// src/lib/websocket/manager.ts
import { io } from 'socket.io-client';

const socket = io(process.env.NEXT_PUBLIC_WS_URL!);

// Subscribe to real-time updates
socket.on('ticker_update', (data) => {
  // Update UI with real-time price data
});
```

## Component Architecture

### shadcn/ui Components
```bash
# Add components as needed
npx shadcn-ui@latest add button
npx shadcn-ui@latest add card
npx shadcn-ui@latest add dialog
npx shadcn-ui@latest add form
```

### Custom Components
- Layout components (Header, Sidebar, Footer)
- Feature components (StrategyCard, TradeList, Chart)
- Form components (StrategyForm, TradeForm)

## Deployment

### Production Build

```bash
# Build for production
npm run build

# Test production build locally
npm run start
```

### Deploy to Vercel

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel

# Production deployment
vercel --prod
```

### Environment Variables
Set these in your deployment platform:
- `NEXT_PUBLIC_API_URL`: Backend API URL
- `NEXT_PUBLIC_WS_URL`: WebSocket URL

## Development Roadmap

### Phase 1: Core Structure ✅
- [x] Next.js setup
- [x] TypeScript configuration
- [x] Tailwind CSS setup
- [x] Basic file structure

### Phase 2: Authentication (TODO)
- [ ] Login page
- [ ] Register page
- [ ] Auth store (Zustand)
- [ ] Protected routes
- [ ] Token management

### Phase 3: Dashboard (TODO)
- [ ] Dashboard layout
- [ ] Portfolio summary
- [ ] Recent trades
- [ ] Active strategies
- [ ] Real-time updates

### Phase 4: Strategies (TODO)
- [ ] Strategy list
- [ ] Create strategy form
- [ ] Strategy details
- [ ] Backtest interface
- [ ] Strategy analytics

### Phase 5: Trading (TODO)
- [ ] Trade list with filters
- [ ] Create trade form
- [ ] Position tracking
- [ ] Trading statistics
- [ ] P&L charts

### Phase 6: Polish (TODO)
- [ ] Loading states
- [ ] Error handling
- [ ] Toast notifications
- [ ] Responsive design
- [ ] Dark mode

## Testing

```bash
# Run tests (when implemented)
npm run test

# E2E tests with Playwright
npm run test:e2e
```

## Contributing

This is a private project. For questions or issues, contact the development team.

## License

Proprietary - All rights reserved
