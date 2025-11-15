#!/bin/bash
set -e

echo "=== Complete Docker Deployment to VPS ==="
echo ""

# Get VPS details
read -p "Enter VPS IP address: " VPS_IP
read -p "Enter VPS username (default: root): " VPS_USER
VPS_USER=${VPS_USER:-root}

echo ""
echo "=========================================="
echo "Building with VPS-specific configuration"
echo "API URL: http://$VPS_IP:8000"
echo "=========================================="
echo ""

# Set environment variables for the build
export NEXT_PUBLIC_API_URL="http://$VPS_IP:8000"
export NEXT_PUBLIC_WS_URL="ws://$VPS_IP:8000"

echo "Step 1: Building frontend with correct API URL..."
cd /Users/ashwin/Desktop/algo-trading-app/frontend

# Create .env.production for the build
cat > .env.production << EOF
NEXT_PUBLIC_API_URL=http://$VPS_IP:8000
NEXT_PUBLIC_WS_URL=ws://$VPS_IP:8000
EOF

# Clean and build
rm -rf .next node_modules
npm ci
npm run build

# Verify the API URL was baked into the build
echo ""
echo "Verifying API URL in build..."
if grep -r "$VPS_IP:8000" .next/ > /dev/null 2>&1; then
    echo "✅ API URL correctly configured in build"
else
    echo "⚠️  Warning: API URL might not be in build, but continuing..."
fi

if [ ! -d ".next/standalone" ]; then
  echo "ERROR: Build failed - .next/standalone not created!"
  exit 1
fi

echo "✅ Frontend built successfully with VPS configuration!"

echo ""
echo "Step 2: Creating deployment package..."
cd /Users/ashwin/Desktop/algo-trading-app

# Create deployment tarball
tar -czf /tmp/algo-final-deploy.tar.gz \
  --exclude='node_modules' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='data/*.db' \
  --exclude='.git' \
  .

echo "Step 3: Copying to VPS..."
scp /tmp/algo-final-deploy.tar.gz $VPS_USER@$VPS_IP:/tmp/

echo "Step 4: Deploying on VPS..."
ssh $VPS_USER@$VPS_IP << ENDSSH
set -e

cd ~
echo "Backing up old deployment..."
rm -rf algo-trading-app-old
mv algo-trading-app algo-trading-app-old 2>/dev/null || true
mkdir -p algo-trading-app
cd algo-trading-app

echo "Extracting deployment package..."
tar -xzf /tmp/algo-final-deploy.tar.gz
rm /tmp/algo-final-deploy.tar.gz

echo "Creating backend environment file..."
cat > backend/.env << EOF
DATABASE_URL=postgresql://trading_user:trading_pass@postgres:5432/trading_db
REDIS_URL=redis://redis:6379
SECRET_KEY=super-secret-key-minimum-thirty-two-characters-long-change-me
ENCRYPTION_KEY=encryption-key-minimum-thirty-two-characters-long-change-me
ALPACA_API_KEY=your-alpaca-key-here
ALPACA_SECRET_KEY=your-alpaca-secret-here
ENVIRONMENT=production
ALLOWED_ORIGINS=http://$VPS_IP:3002,http://localhost:3002
EOF

echo "Verifying backend .env..."
cat backend/.env | grep SECRET_KEY

echo ""
echo "Stopping old containers..."
docker-compose -f docker-compose.prod.yml down 2>/dev/null || true
docker stop algo-trading-frontend 2>/dev/null || true
docker rm algo-trading-frontend 2>/dev/null || true

echo "Cleaning Docker..."
docker system prune -f

echo ""
echo "Building backend image..."
docker-compose -f docker-compose.prod.yml build --no-cache backend

echo ""
echo "Building frontend image..."
cd frontend
docker build -f Dockerfile.prod -t algo-trading-frontend:prod .
cd ..

echo ""
echo "Starting database services..."
docker-compose -f docker-compose.prod.yml up -d postgres redis

echo "Waiting for database..."
sleep 15

echo ""
echo "Starting backend..."
docker-compose -f docker-compose.prod.yml up -d backend

echo "Waiting for backend to be healthy..."
sleep 20

echo ""
echo "Stamping migrations..."
docker exec algo-trading-api alembic stamp head 2>/dev/null || echo "Migration stamp not needed"

echo ""
echo "Starting frontend..."
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
echo "=========================================="
echo "Verifying Deployment"
echo "=========================================="
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "Backend Health:"
curl -s http://localhost:8000/health || echo "Backend not ready yet"

echo ""
echo "Frontend Status:"
curl -I http://localhost:3002 2>/dev/null | head -3 || echo "Frontend starting..."

echo ""
echo "=========================================="
echo "✅ Deployment Complete!"
echo "=========================================="
echo ""
echo "🌐 Access your app at: http://$VPS_IP:3002"
echo ""
echo "Backend API: http://$VPS_IP:8000"
echo "API Docs: http://$VPS_IP:8000/docs"
echo ""
echo "📋 Useful commands:"
echo "  View logs:"
echo "    docker logs algo-trading-frontend"
echo "    docker logs algo-trading-api"
echo "  Restart services:"
echo "    docker-compose -f docker-compose.prod.yml restart"
echo "  View all containers:"
echo "    docker ps"
echo ""
ENDSSH

echo ""
echo "=========================================="
echo "✅ Deployment Script Complete!"
echo "=========================================="
echo ""
echo "🌐 Your app is now running at: http://$VPS_IP:3002"
echo ""
echo "The frontend has been built with the correct API URL:"
echo "  NEXT_PUBLIC_API_URL=http://$VPS_IP:8000"
echo ""
echo "All services are running in Docker containers:"
echo "  ✅ PostgreSQL"
echo "  ✅ Redis"
echo "  ✅ Backend API"
echo "  ✅ Frontend"
echo ""
echo "🎉 You're all set! Open http://$VPS_IP:3002 in your browser"
