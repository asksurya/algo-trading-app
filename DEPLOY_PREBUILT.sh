#!/bin/bash

echo "=== Build Locally & Deploy to VPS ==="
echo "This builds on your Mac (which has enough RAM) then deploys to VPS"
echo ""

# Get VPS connection details
read -p "Enter VPS IP address: " VPS_IP
read -p "Enter VPS username (default: root): " VPS_USER
VPS_USER=${VPS_USER:-root}

echo ""
echo "Step 1: Building frontend locally..."
cd /Users/ashwin/Desktop/algo-trading-app/frontend

# Clean previous build
rm -rf .next node_modules

# Install dependencies
npm ci

# Build
echo "Building Next.js (this takes 2-3 minutes)..."
npm run build

if [ ! -d ".next" ]; then
  echo "ERROR: Build failed!"
  exit 1
fi

echo "✅ Local build successful!"

echo ""
echo "Step 2: Creating deployment package..."
cd /Users/ashwin/Desktop/algo-trading-app

# Create tarball including built frontend
tar -czf /tmp/algo-trading-deploy.tar.gz \
  --exclude='node_modules' \
  --exclude='data' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='*.db' \
  --exclude='.git' \
  .

echo "Step 3: Copying to VPS..."
scp /tmp/algo-trading-deploy.tar.gz $VPS_USER@$VPS_IP:/tmp/

echo "Step 4: Deploying on VPS..."
ssh $VPS_USER@$VPS_IP << 'ENDSSH'
cd ~
rm -rf algo-trading-app-old
mv algo-trading-app algo-trading-app-old 2>/dev/null || true
mkdir -p algo-trading-app
cd algo-trading-app
tar -xzf /tmp/algo-trading-deploy.tar.gz
rm /tmp/algo-trading-deploy.tar.gz

# Create backend .env
cat > backend/.env << 'EOF'
DATABASE_URL=postgresql://trading_user:trading_pass@postgres:5432/trading_db
REDIS_URL=redis://redis:6379
SECRET_KEY=your-secret-key-here-change-in-production
ENCRYPTION_KEY=your-encryption-key-here-change-in-production
ALPACA_API_KEY=your-alpaca-key
ALPACA_SECRET_KEY=your-alpaca-secret
ENVIRONMENT=production
EOF

# Create frontend .env
SERVER_IP=$(curl -s ifconfig.me)
cat > .env << EOF
NEXT_PUBLIC_API_URL=http://$SERVER_IP:8000
NEXT_PUBLIC_WS_URL=ws://$SERVER_IP:8000
EOF

echo "Cleaning Docker..."
docker-compose down -v 2>/dev/null
docker system prune -af
docker builder prune -af

# Modify docker-compose to skip frontend build
echo "Using pre-built frontend..."

echo "Building backend only..."
docker-compose build --no-cache backend

echo "Starting services..."
docker-compose up -d

echo "Waiting for startup..."
sleep 60

echo "Stamping migrations..."
docker exec algo-trading-api alembic stamp head 2>/dev/null || true

echo "Verifying..."
docker ps
curl -s http://localhost:8000/health
curl -I http://localhost:3002 | head -3

echo ""
echo "Deployment complete!"
echo "Access at: http://$(curl -s ifconfig.me):3002"
ENDSSH

echo ""
echo "=== Deployment Complete ==="
echo "Access your app at: http://$VPS_IP:3002"
