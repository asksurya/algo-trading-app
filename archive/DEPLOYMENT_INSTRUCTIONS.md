# Deployment Instructions - Web Application V3

## Overview

This document provides step-by-step instructions for deploying the Algo Trading Platform V3 in production.

## Prerequisites

- Docker and Docker Compose installed
- PostgreSQL 15+ database
- Redis 7+ cache
- Node.js 18+ (for frontend build)
- Domain name and SSL certificates (for production)

## Backend Deployment

### 1. Environment Configuration

Create `.env` file in the `backend` directory:

```bash
cd backend
cp .env.example .env
```

Configure the following variables:

```env
# Security
SECRET_KEY=your-super-secret-key-min-32-chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/algo_trading

# Redis
REDIS_URL=redis://localhost:6379/0

# Alpaca API
ALPACA_API_KEY=your-alpaca-api-key
ALPACA_SECRET_KEY=your-alpaca-secret-key
ALPACA_BASE_URL=https://paper-api.alpaca.markets

# CORS
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

### 2. Database Setup

Run migrations:

```bash
cd backend
poetry install
poetry run alembic upgrade head
```

### 3. Docker Deployment

Build and start services:

```bash
cd backend
docker-compose up -d
```

Verify services are running:

```bash
docker-compose ps
docker-compose logs -f
```

### 4. API Access

The API will be available at:
- Development: http://localhost:8000
- API Documentation: http://localhost:8000/api/docs
- Health Check: http://localhost:8000/health

## Frontend Deployment

### 1. Environment Configuration

Create `.env.local` in the `frontend` directory:

```bash
cd frontend
cp .env.local.example .env.local
```

Configure:

```env
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
```

### 2. Build for Production

```bash
cd frontend
npm install
npm run build
```

### 3. Deployment Options

#### Option A: Vercel (Recommended)

1. Push code to GitHub
2. Import project in Vercel
3. Configure environment variables
4. Deploy

#### Option B: Docker

```bash
cd frontend
docker build -t algo-trading-frontend .
docker run -p 3000:3000 algo-trading-frontend
```

#### Option C: Static Export

```bash
npm run build
# Deploy the .next folder to your hosting provider
```

## Production Checklist

### Security

- [ ] Change SECRET_KEY to a strong random value
- [ ] Enable HTTPS/SSL
- [ ] Configure CORS properly
- [ ] Set up rate limiting
- [ ] Enable API authentication
- [ ] Regular security updates

### Database

- [ ] Set up automated backups
- [ ] Configure connection pooling
- [ ] Set up monitoring
- [ ] Index optimization
- [ ] Regular maintenance

### Monitoring

- [ ] Set up application monitoring (e.g., Sentry)
- [ ] Configure logging (e.g., CloudWatch, ELK)
- [ ] Set up uptime monitoring
- [ ] Configure alerts
- [ ] Performance monitoring

### Scaling

- [ ] Configure load balancer
- [ ] Set up auto-scaling
- [ ] CDN for frontend assets
- [ ] Database read replicas
- [ ] Redis cluster (if needed)

## Quick Start Commands

### Development

```bash
# Backend
cd backend
poetry install
poetry run uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

### Production

```bash
# Backend with Docker
cd backend
docker-compose up -d

# Frontend build
cd frontend
npm run build
npm start
```

## Troubleshooting

### Database Connection Issues

```bash
# Check PostgreSQL status
docker-compose logs postgres

# Test connection
psql -h localhost -U your_user -d algo_trading
```

### Redis Connection Issues

```bash
# Check Redis status
docker-compose logs redis

# Test connection
redis-cli ping
```

### API Issues

```bash
# Check backend logs
docker-compose logs api

# Check health endpoint
curl http://localhost:8000/health
```

## Maintenance

### Database Backups

```bash
# Backup
pg_dump -h localhost -U your_user algo_trading > backup.sql

# Restore
psql -h localhost -U your_user algo_trading < backup.sql
```

### Updates

```bash
# Backend
cd backend
git pull
poetry install
poetry run alembic upgrade head
docker-compose restart

# Frontend
cd frontend
git pull
npm install
npm run build
npm restart
```

## Support

For issues and questions:
- GitHub Issues: https://github.com/yourusername/algo-trading-app/issues
- Documentation: See README.md files in backend/ and frontend/

---

**Version**: 3.0.0  
**Last Updated**: October 20, 2025
