# VPS Docker Deployment Guide

## Complete Docker Deployment with All Services

This guide will help you deploy the entire Algo Trading app using Docker on your VPS.

---

## Prerequisites

Your VPS should have:
- Docker installed
- Docker Compose installed
- Git installed
- At least 2GB RAM
- 20GB+ storage

---

## Step-by-Step Deployment

### 1. Pull Latest Code

```bash
# SSH into your VPS
ssh root@your-vps-ip

# Navigate to project or clone fresh
cd ~
rm -rf algo-trading-app  # Remove old version if exists
git clone https://github.com/yourusername/algo-trading-app.git
cd algo-trading-app
```

### 2. Configure Environment Variables

```bash
# Create backend .env file
cat > backend/.env << 'EOF'
# Database (auto-configured for Docker)
DATABASE_URL=postgresql://trading_user:trading_pass@postgres:5432/trading_db

# Redis (auto-configured for Docker)
REDIS_URL=redis://redis:6379

# Security - CHANGE THESE!
SECRET_KEY=your-super-secret-key-min-32-chars-change-this
ENCRYPTION_KEY=your-encryption-key-32-bytes-base64-change-this

# Alpaca API
ALPACA_API_KEY=your_alpaca_api_key_here
ALPACA_SECRET_KEY=your_alpaca_secret_key_here
ALPACA_BASE_URL=https://paper-api.alpaca.markets

# App Settings
ENVIRONMENT=production
LOG_LEVEL=INFO
ALLOWED_ORIGINS=*

# JWT Settings
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
EOF

# IMPORTANT: Edit the .env file and change SECRET_KEY, ENCRYPTION_KEY, and Alpaca keys
nano backend/.env
```

### 3. Generate Secure Keys

```bash
# Generate SECRET_KEY
python3 -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32))"

# Generate ENCRYPTION_KEY
python3 -c "from cryptography.fernet import Fernet; print('ENCRYPTION_KEY=' + Fernet.generate_key().decode())"

# Copy these values into backend/.env
```

### 4. Set Frontend Environment Variables

```bash
# Get your server IP
SERVER_IP=$(curl -s ifconfig.me)

# Create .env file in root for docker-compose
cat > .env << EOF
NEXT_PUBLIC_API_URL=http://$SERVER_IP:8000
NEXT_PUBLIC_WS_URL=ws://$SERVER_IP:8000
EOF

echo "Your server IP is: $SERVER_IP"
echo "Frontend will use: http://$SERVER_IP:8000"
```

### 5. Build and Start All Services

```bash
# Stop any old containers
docker-compose down

# Build and start (this will take 5-10 minutes)
docker-compose up -d --build

# Watch the build progress
docker-compose logs -f
# Press Ctrl+C when you see "Application startup complete"
```

### 6. Wait for Services to Be Ready

```bash
# Wait for all services to be healthy (about 30-60 seconds)
echo "Waiting for services to start..."
sleep 60

# Check status
docker-compose ps

# You should see all 4 services as "Up" and "healthy"
```

### 7. Run Database Migrations

```bash
# Run migrations to create database tables
docker exec -it algo-trading-api alembic upgrade head

# You should see output like:
# INFO  [alembic.runtime.migration] Running upgrade -> 001_initial_schema
# ...
```

### 8. Verify Everything is Running

```bash
# Check all containers
docker ps

# Test backend health
curl http://localhost:8000/health
# Should return: {"status":"healthy","environment":"production"}

# Test frontend
curl -I http://localhost:3002
# Should return: HTTP/1.1 200 OK

# Get your server IP
echo "Access your app at: http://$(curl -s ifconfig.me):3002"
```

---

## Access Your Application

1. **Frontend:** `http://YOUR_SERVER_IP:3002`
2. **Backend API:** `http://YOUR_SERVER_IP:8000`
3. **API Docs:** `http://YOUR_SERVER_IP:8000/docs`

Replace `YOUR_SERVER_IP` with your actual server IP (run `curl ifconfig.me` to get it).

---

## Management Commands

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend

# Last 100 lines
docker-compose logs --tail=100
```

### Restart Services

```bash
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart backend
docker-compose restart frontend
```

### Stop Services

```bash
# Stop all (keeps data)
docker-compose stop

# Stop and remove containers (keeps data)
docker-compose down

# Stop and remove everything including data
docker-compose down -v
```

### Update Code

```bash
# Pull latest code
git pull

# Rebuild and restart
docker-compose up -d --build

# Run any new migrations
docker exec -it algo-trading-api alembic upgrade head
```

---

## Troubleshooting

### Backend Won't Start

```bash
# Check logs
docker logs algo-trading-api

# Common issues:
# 1. Database connection - check DATABASE_URL in backend/.env
# 2. Missing env vars - ensure all required vars are set
# 3. Port conflict - check if port 8000 is already in use

# Fix and rebuild
docker-compose up -d --build backend
```

### Frontend Won't Build

```bash
# Check logs
docker logs algo-trading-frontend --tail=100

# Common issues:
# 1. Build timeout - frontend build takes time, be patient
# 2. Out of memory - need at least 2GB RAM
# 3. Node modules - clear and rebuild:

docker-compose down
docker-compose build --no-cache frontend
docker-compose up -d
```

### Database Connection Issues

```bash
# Check postgres is running
docker exec -it algo-trading-postgres pg_isready -U trading_user

# Check if migrations ran
docker exec -it algo-trading-api alembic current

# Re-run migrations
docker exec -it algo-trading-api alembic upgrade head
```

### Can't Access from Browser

```bash
# Check firewall
sudo ufw status

# Allow ports if needed
sudo ufw allow 3002/tcp
sudo ufw allow 8000/tcp

# Check containers are accessible
curl http://localhost:3002
curl http://localhost:8000/health
```

---

## Security Hardening (Production)

### 1. Use Strong Passwords

```bash
# In backend/.env, set strong values for:
# - SECRET_KEY (use the generated one)
# - ENCRYPTION_KEY (use the generated one)
# - Database password (change from default)
```

### 2. Configure Firewall

```bash
# Enable firewall
sudo ufw enable

# Allow SSH (IMPORTANT - do this first!)
sudo ufw allow 22/tcp

# Allow HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Allow app ports
sudo ufw allow 3002/tcp
sudo ufw allow 8000/tcp

# Check status
sudo ufw status
```

### 3. Set Up SSL (Optional but Recommended)

```bash
# Install Certbot
sudo apt update
sudo apt install certbot

# Get SSL certificate (requires domain name)
sudo certbot certonly --standalone -d yourdomain.com

# Configure Nginx as reverse proxy (separate guide)
```

### 4. Restrict Database Access

```bash
# Edit docker-compose.yml to remove exposed ports
# Change:
#   ports:
#     - "5432:5432"
# To:
#   expose:
#     - "5432"

# This makes database only accessible from other containers
```

---

## Monitoring

### Check Resource Usage

```bash
# Container stats
docker stats

# Disk usage
docker system df

# Clean up unused resources
docker system prune -a
```

### Set Up Log Rotation

```bash
# Docker logs can grow large
# Configure log rotation in docker-compose.yml:

# Add to each service:
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

---

## Backup

### Backup Database

```bash
# Create backup
docker exec algo-trading-postgres pg_dump -U trading_user trading_db > backup.sql

# Restore backup
cat backup.sql | docker exec -i algo-trading-postgres psql -U trading_user trading_db
```

### Backup Everything

```bash
# Stop containers
docker-compose down

# Backup volumes
sudo tar czf algo-trading-backup.tar.gz \
  /var/lib/docker/volumes/algo-trading-app_postgres_data \
  /var/lib/docker/volumes/algo-trading-app_redis_data \
  backend/.env

# Restart
docker-compose up -d
```

---

## Complete Fresh Installation

If you want to start completely fresh:

```bash
# Stop and remove everything
cd ~/algo-trading-app
docker-compose down -v

# Remove all images
docker rmi $(docker images -q algo-trading*)

# Remove project
cd ~
rm -rf algo-trading-app

# Clone fresh
git clone https://github.com/yourusername/algo-trading-app.git
cd algo-trading-app

# Follow deployment steps from the beginning
```

---

## Quick Reference

```bash
# Start
docker-compose up -d

# Stop
docker-compose down

# Restart
docker-compose restart

# View logs
docker-compose logs -f

# Check status
docker-compose ps

# Run migrations
docker exec -it algo-trading-api alembic upgrade head

# Access shell
docker exec -it algo-trading-api bash
docker exec -it algo-trading-frontend sh
```

---

## Success Checklist

- [ ] All 4 containers running (postgres, redis, backend, frontend)
- [ ] All containers show "healthy" status
- [ ] Database migrations completed
- [ ] Backend health check returns 200 OK
- [ ] Frontend accessible in browser
- [ ] Can register new user
- [ ] Can login successfully
- [ ] Dashboard shows data

Once all checkboxes are complete, your app is fully deployed! 🎉

---

## Getting Help

If you encounter issues:

1. Check logs: `docker-compose logs -f`
2. Check container status: `docker ps -a`
3. Verify environment variables: `cat backend/.env`
4. Check firewall: `sudo ufw status`
5. Test endpoints: `curl http://localhost:8000/health`

Report issues with log output for faster troubleshooting.
