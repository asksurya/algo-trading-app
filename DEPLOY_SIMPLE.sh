#!/bin/bash

echo "=== Simple Deployment: Pre-built Frontend + Docker Backend ==="
echo ""

# Get VPS details
read -p "Enter VPS IP address: " VPS_IP
read -p "Enter VPS username (default: root): " VPS_USER
VPS_USER=${VPS_USER:-root}

echo ""
echo "Step 1: Building frontend locally..."
cd /Users/ashwin/Desktop/algo-trading-app/frontend

# Clean and build
rm -rf .next node_modules
npm ci
npm run build

if [ ! -d ".next" ]; then
  echo "ERROR: Build failed!"
  exit 1
fi

echo "✅ Frontend built successfully!"

echo ""
echo "Step 2: Creating deployment package..."
cd /Users/ashwin/Desktop/algo-trading-app

tar -czf /tmp/algo-deploy.tar.gz \
  --exclude='node_modules' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='data' \
  --exclude='.git' \
  .

echo "Step 3: Copying to VPS..."
scp /tmp/algo-deploy.tar.gz $VPS_USER@$VPS_IP:/tmp/

echo "Step 4: Deploying on VPS..."
ssh $VPS_USER@$VPS_IP << 'ENDSSH'
set -e

cd ~
rm -rf algo-trading-app-old
mv algo-trading-app algo-trading-app-old 2>/dev/null || true
mkdir -p algo-trading-app
cd algo-trading-app

echo "Extracting..."
tar -xzf /tmp/algo-deploy.tar.gz
rm /tmp/algo-deploy.tar.gz

# Backend .env
cat > backend/.env << 'EOF'
DATABASE_URL=postgresql://trading_user:trading_pass@postgres:5432/trading_db
REDIS_URL=redis://redis:6379
SECRET_KEY=your-secret-key-change-me
ENCRYPTION_KEY=your-encryption-key-change-me
ALPACA_API_KEY=your-key
ALPACA_SECRET_KEY=your-secret
ENVIRONMENT=production
EOF

# Frontend .env
SERVER_IP=$(curl -s ifconfig.me)
cat > .env << EOF
NEXT_PUBLIC_API_URL=http://$SERVER_IP:8000
NEXT_PUBLIC_WS_URL=ws://$SERVER_IP:8000
EOF

echo "Installing frontend production dependencies..."
cd frontend
npm ci --production

echo "Stopping old services..."
cd ..
docker-compose down -v 2>/dev/null || true
pkill -f "node.*server.js" || true

echo "Cleaning Docker..."
docker system prune -f

echo "Starting backend services..."
docker-compose up -d postgres redis backend

echo "Waiting for backend..."
sleep 30

echo "Stamping migrations..."
docker exec algo-trading-api alembic stamp head 2>/dev/null || true

echo "Starting frontend (direct Node.js)..."
cd frontend
nohup node .next/standalone/server.js > /tmp/frontend.log 2>&1 &
FRONTEND_PID=$!
echo $FRONTEND_PID > /tmp/frontend.pid

sleep 5

echo ""
echo "Verifying..."
docker ps
echo ""
curl -s http://localhost:8000/health || echo "Backend not ready"
echo ""
curl -I http://localhost:3000 2>/dev/null | head -3 || echo "Frontend starting..."

echo ""
echo "✅ Deployment complete!"
echo "Backend: http://$(curl -s ifconfig.me):8000"
echo "Frontend: http://$(curl -s ifconfig.me):3000"
echo ""
echo "To check frontend logs: tail -f /tmp/frontend.log"
echo "To stop frontend: kill \$(cat /tmp/frontend.pid)"
ENDSSH

echo ""
echo "=== Deployment Complete ==="
echo "Access: http://$VPS_IP:3000"
