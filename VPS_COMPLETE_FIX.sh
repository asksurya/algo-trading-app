#!/bin/bash

echo "=== COMPLETE VPS FIX - Fresh Clone ==="
echo "This will DELETE the current directory and clone fresh from git"
echo ""
read -p "Press ENTER to continue or CTRL+C to cancel..."

# Get current directory name
CURRENT_DIR=$(pwd)
PARENT_DIR=$(dirname "$CURRENT_DIR")

echo "Step 1: Going to parent directory..."
cd "$PARENT_DIR"

echo "Step 2: Removing corrupted directory..."
rm -rf algo-trading-app

echo "Step 3: Fresh clone from git..."
git clone https://github.com/asksurya/algo-trading-app.git

echo "Step 4: Entering directory..."
cd algo-trading-app

echo "Step 5: Creating backend .env file..."
cat > backend/.env << 'EOF'
DATABASE_URL=postgresql://trading_user:trading_pass@postgres:5432/trading_db
REDIS_URL=redis://redis:6379
SECRET_KEY=your-secret-key-here-change-in-production
ENCRYPTION_KEY=your-encryption-key-here-change-in-production
ALPACA_API_KEY=your-alpaca-key
ALPACA_SECRET_KEY=your-alpaca-secret
ENVIRONMENT=production
EOF

echo "Step 6: Creating frontend .env..."
SERVER_IP=$(curl -s ifconfig.me)
cat > .env << EOF
NEXT_PUBLIC_API_URL=http://$SERVER_IP:8000
NEXT_PUBLIC_WS_URL=ws://$SERVER_IP:8000
EOF

echo "Step 7: Verifying imports are correct..."
head -12 frontend/src/app/\(auth\)/login/page.tsx | grep "import.*@/"

echo "Step 8: Cleaning Docker..."
docker-compose down -v 2>/dev/null
docker system prune -af --volumes
docker builder prune -af

echo "Step 9: Building (this takes 3-5 minutes)..."
docker-compose build --no-cache --pull

echo "Step 10: Starting services..."
docker-compose up -d

echo "Step 11: Waiting for startup (60 seconds)..."
sleep 60

echo "Step 12: Stamping migrations..."
docker exec algo-trading-api alembic stamp head 2>/dev/null

echo "Step 13: Verifying..."
docker ps
echo ""
curl -s http://localhost:8000/health
echo ""
curl -I http://localhost:3002 | head -3

echo ""
echo "=== Deployment Complete ==="
echo "Access: http://$(curl -s ifconfig.me):3002"
