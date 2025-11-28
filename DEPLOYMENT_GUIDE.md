# Deployment Guide for Algo Trading Platform

This guide covers the complete deployment process for the algorithmic trading platform.

## Prerequisites

### System Requirements
- Docker & Docker Compose
- Node.js 20+
- Python 3.12+
- Firebase CLI
- Git

### Accounts & Services
- Firebase project with Hosting and App Hosting enabled
- PostgreSQL database (managed or Docker)
- Redis instance (managed or Docker)
- Domain name (for production)

## Environment Setup

### 1. Environment Variables

#### Backend (.env)
```bash
# Database
DATABASE_URL=postgresql://user:password@host:5432/database
POSTGRES_USER=user
POSTGRES_PASSWORD=password
POSTGRES_DB=database

# Redis
REDIS_URL=redis://host:6379/0

# Security - CHANGE IN PRODUCTION!
SECRET_KEY=your-secure-random-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=30

# Alpaca Trading (Production credentials)
ALPACA_API_KEY=your_production_api_key
ALPACA_SECRET_KEY=your_production_secret_key
ALPACA_BASE_URL=https://api.alpaca.markets

# CORS (Production domains)
ALLOWED_ORIGINS=["https://yourdomain.com","https://www.yourdomain.com"]

# Application
APP_NAME=Algo Trading Platform
APP_VERSION=1.0.0
API_V1_STR=/api/v1
ENVIRONMENT=production
LOG_LEVEL=INFO
```

#### Frontend (.env.production)
```bash
# Replace with your actual domain
NEXT_PUBLIC_API_URL=https://backend.yourdomain.com
NEXT_PUBLIC_WS_URL=wss://backend.yourdomain.com
```

### 2. Firebase Setup

```bash
# Login to Firebase
firebase login

# Initialize Firebase project (if not already done)
firebase init
# Select: Hosting, App Hosting
# Choose existing project or create new

# Configure hosting target
firebase use --add
# Select your project and give it a target name like 'frontend'

# Configure backend app hosting
firebase apphosting:backend:create backend --project your-project-id
```

## Deployment Options

### Option 1: Full Docker Deployment (Recommended)

#### Backend + Database Deployment

1. **Update docker-compose.prod.yml**
   - Modify database credentials
   - Update backend environment variables
   - Adjust resource limits as needed

2. **Deploy Services**
   ```bash
   # Build and deploy
   docker-compose -f docker-compose.prod.yml up -d --build

   # Check logs
   docker-compose -f docker-compose.prod.yml logs -f
   ```

#### Frontend Deployment

```bash
# Build the frontend
cd frontend
npm ci
npm run build

# Deploy to Firebase Hosting
firebase deploy --only hosting
```

### Option 2: Hybrid Docker + Firebase Deployment

1. **Backend on Firebase App Hosting**
   ```bash
   # Deploy backend to Firebase App Hosting
   firebase deploy --only apphosting
   ```

2. **Frontend on Firebase Hosting**
   ```bash
   # Build and deploy frontend
   cd frontend
   npm ci
   npm run build
   firebase deploy --only hosting:frontend
   ```

3. **Database & Redis**
   - Use managed services (AWS RDS, Google Cloud SQL, etc.)
   - Or deploy via Docker Compose on a VPS

## Manual Deployment Steps

### Backend Deployment

```bash
cd backend

# Install dependencies
pip install poetry
poetry install --no-dev

# Run migrations
poetry run alembic upgrade head

# Set environment variables
cp .env.example .env
# Edit .env with production values

# Run with Gunicorn
poetry run gunicorn -k uvicorn.workers.UvicornWorker -c gunicorn_conf.py app.main:app
```

### Frontend Deployment

```bash
cd frontend

# Install dependencies
npm ci

# Build for production
npm run build

# Export for static hosting
npm run export

# Deploy to hosting provider
# Files will be in the 'out' directory
```

## CI/CD Pipeline Setup

### GitHub Actions Example

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy

on:
  push:
    branches: [main]

env:
  REGISTRY: ghcr.io
  BACKEND_IMAGE: ${{ github.repository }}/backend
  FRONTEND_IMAGE: ${{ github.repository }}/frontend

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v4

    - name: Log in to Container Registry
      uses: docker/login-action@v3
      with:
        registry: ${{ env.REGISTRY }}
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}

    - name: Build Backend
      run: |
        cd backend
        docker build -t ${{ env.BACKEND_IMAGE }} .

    - name: Build Frontend
      run: |
        cd frontend
        docker build -t ${{ env.FRONTEND_IMAGE }} .

    - name: Deploy to Firebase
      uses: FirebaseExtended/action-hosting-deploy@v0
      with:
        repoToken: ${{ secrets.FIREBASE_TOKEN }}
        firebaseServiceAccount: ${{ secrets.FIREBASE_SERVICE_ACCOUNT }}
        channelId: live
        projectId: your-project-id
```

## Monitoring & Maintenance

### Health Checks

```bash
# Backend health check
curl https://your-backend-url/health

# Frontend availability check
curl https://your-frontend-url/
```

### Database Maintenance

```bash
# Backup database
docker exec algo-trading-postgres pg_dump -U trading_user trading_db > backup.sql

# Run migrations
docker exec algo-trading-backend alembic upgrade head
```

### Logs

```bash
# Docker container logs
docker-compose -f docker-compose.prod.yml logs -f backend

# Firebase logs
firebase functions:log
```

## Troubleshooting

### Common Issues

1. **Database Connection Issues**
   - Verify DATABASE_URL in backend environment
   - Check PostgreSQL service is running
   - Ensure proper network connectivity

2. **Frontend API Connection**
   - Verify NEXT_PUBLIC_API_URL is set correctly
   - Check CORS configuration
   - Ensure backend is accessible

3. **Authentication Problems**
   - Verify SECRET_KEY is set and secure
   - Check token expiration settings
   - Review CORS allowed origins

4. **Build Failures**
   - Clear Docker cache: `docker system prune`
   - Rebuild without cache: `docker-compose build --no-cache`
   - Check build logs for specific errors

## Security Checklist

- [ ] No hardcoded credentials in source code
- [ ] SECRET_KEY changed from default
- [ ] HTTPS enabled on all domains
- [ ] CORS properly configured for production domains only
- [ ] Database credentials rotated
- [ ] API keys for third-party services are production keys
- [ ] Environment variables properly set
- [ ] Debug logging disabled in production
- [ ] Security headers configured (CSP, X-Frame-Options, etc.)

## Performance Optimization

- Enable gzip compression on hosting
- Set appropriate cache headers for static assets
- Monitor API response times
- Set up database connection pooling
- Implement CDN for static assets
- Regular database query optimization
