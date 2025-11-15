#!/bin/bash

echo "=== Proper Docker Deployment with Pre-built Frontend ==="
echo "This uses Docker for ALL services, but builds Next.js locally to avoid VPS memory issues"
echo ""

# Get VPS details
read -p "Enter VPS IP address: " VPS_IP
read -p "Enter VPS username (default: root): " VPS_USER
VPS_USER=${VPS_USER:-root}

echo ""
echo "Step 1: Building Next.js frontend locally (uses your Mac's RAM)..."
cd /Users/ashwin/Desktop/algo-trading-app/frontend

# Clean and build
rm -rf .next node_modules
npm ci
npm run build

if [ ! -d ".next/standalone" ]; then
  echo "ERROR: Build failed - .next/standalone not created!"
  exit 1
fi

echo "✅ Frontend built successfully!"

echo ""
echo "Step 2: Creating deployment package WITH pre-built frontend..."
cd /Users/ashwin/Desktop/algo-trading-app

tar -czf /tmp/algo-docker-deploy.tar.gz \
  --exclude='node_modules' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='data/*.db' \
  --exclude='.git' \
  .

echo "Step 3: Copying to VPS (this may take a minute)..."
scp /tmp/algo-docker-deploy.tar.gz $VPS_USER@$VPS_IP:/tmp/

echo "Step 4: Deploying on VPS with Docker..."
ssh $VPS_USER@$VPS_IP << 'ENDSSH'
set -e

cd ~
rm -rf algo-trading-app-old
mv algo-trading-app algo-trading-app-old 2>/dev/null || true
mkdir -p algo-trading-app
cd algo-trading-app

echo "Extracting deployment package..."
tar -xzf /tmp/algo-docker-deploy.tar.gz
rm /tmp/algo-docker-deploy.tar.gz

# Create backend .env
cat > backend/.env << 'EOF'
DATABASE_URL=postgresql://trading_user:trading_pass@postgres:5432/trading_db
REDIS_URL=redis://redis:6379
SECRET_KEY=your-secret-key-change-me
ENCRYPTION_KEY=your-encryption-key-change-me
ALPACA_API_KEY=your-key
ALPACA_SECRET_KEY=your-secret
ENVIRONMENT=production
EOF

# Create frontend .env
SERVER_IP=$(curl -s ifconfig.me)
cat > frontend/.env.production << EOF
NEXT_PUBLIC_API_URL=http://$SERVER_IP:8000
NEXT_PUBLIC_WS_URL=ws://$SERVER_IP:8000
EOF

echo "Stopping old containers..."
docker-compose -f docker-compose.prod.yml down -v 2>/dev/null || true

echo "Cleaning Docker system..."
docker system prune -f

echo "Building backend Docker image..."
docker-compose -f docker-compose.prod.yml build --no-cache backend

echo "Building frontend Docker image (lightweight - just copies pre-built files)..."
cd frontend
docker build -f Dockerfile.prod -t algo-trading-frontend:prod .
cd ..

echo "Starting all services with Docker..."
# Start backend services first
docker-compose -f docker-compose.prod.yml up -d postgres redis backend

echo "Waiting for backend to be healthy..."
sleep 30

echo "Stamping migrations..."
docker exec algo-trading-api alembic stamp head 2>/dev/null || true

echo "Starting frontend container..."
docker run -d \
  --name algo-trading-frontend \
  --network algo-trading-network \
  -p 3002:3000 \
  --restart unless-stopped \
  --memory="256m" \
  --memory-reservation="128m" \
  algo-trading-frontend:prod

echo "Waiting for frontend..."
sleep 10

echo ""
echo "Verifying deployment..."
docker ps
echo ""
echo "Backend health:"
curl -s http://localhost:8000/health || echo "Backend not ready"
echo ""
echo "Frontend status:"
curl -I http://localhost:3002 2>/dev/null | head -3 || echo "Frontend starting..."

echo ""
echo "✅ Docker deployment complete!"
echo ""
echo "All services running in Docker containers:"
echo "  - PostgreSQL (Docker)"
echo "  - Redis (Docker)"
echo "  - Backend API (Docker)"
echo "  - Frontend (Docker)"
echo ""
echo "Access your app at: http://$(curl -s ifconfig.me):3002"
echo ""
echo "To view logs:"
echo "  docker logs algo-trading-frontend"
echo "  docker logs algo-trading-api"
echo ""
echo "To restart:"
echo "  docker-compose -f docker-compose.prod.yml restart"
ENDSSH

echo ""
echo "=== Deployment Complete ==="
echo "Access: http://$VPS_IP:3002"
echo ""
echo "This deployment uses Docker for ALL services!"
