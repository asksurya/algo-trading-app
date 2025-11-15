#!/bin/bash

echo "=== Deploy from Local to VPS ==="
echo "This bypasses git and copies your LOCAL correct files to VPS"
echo ""

# Get VPS connection details
read -p "Enter VPS IP address: " VPS_IP
read -p "Enter VPS username (default: root): " VPS_USER
VPS_USER=${VPS_USER:-root}

echo ""
echo "Step 1: Creating deployment package..."
cd /Users/ashwin/Desktop/algo-trading-app

# Create tarball of correct local files (excluding .git, node_modules, etc.)
tar -czf /tmp/algo-trading-deploy.tar.gz \
  --exclude='.git' \
  --exclude='node_modules' \
  --exclude='data' \
  --exclude='__pycache__' \
  --exclude='.next' \
  --exclude='*.pyc' \
  --exclude='*.db' \
  .

echo "Step 2: Copying to VPS..."
scp /tmp/algo-trading-deploy.tar.gz $VPS_USER@$VPS_IP:/tmp/

echo "Step 3: Deploying on VPS..."
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

echo "Verifying imports are correct..."
head -12 frontend/src/app/\(auth\)/login/page.tsx | grep "@/"

echo "Cleaning Docker..."
docker-compose down -v 2>/dev/null
docker system prune -af --volumes
docker builder prune -af

echo "Building (takes 3-5 minutes)..."
docker-compose build --no-cache --pull

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

echo "Deployment complete!"
echo "Access at: http://$(curl -s ifconfig.me):3002"
ENDSSH

echo ""
echo "=== Deployment Complete ==="
echo "Access your app at: http://$VPS_IP:3002"
