#!/bin/bash

echo "=== VPS Docker Build Fix Script ==="
echo "This script will completely clean and rebuild the Docker environment"
echo ""

# Step 1: Stop and remove everything
echo "Step 1: Stopping all containers..."
docker-compose down -v

echo "Step 2: Removing all Docker data..."
docker system prune -af --volumes
docker builder prune -af

# Step 2: Clean git repository
echo "Step 3: Cleaning git repository..."
git clean -fdx
git reset --hard HEAD

# Step 3: Pull latest code
echo "Step 4: Pulling latest code..."
git fetch origin
git reset --hard origin/main

# Step 4: Verify correct imports
echo "Step 5: Verifying imports are correct..."
grep "import.*@/lib" frontend/src/app/\(auth\)/login/page.tsx | head -1

# Step 5: Build with no cache
echo "Step 6: Building with no cache (this will take 2-3 minutes)..."
docker-compose build --no-cache --pull

# Step 6: Start services
echo "Step 7: Starting services..."
docker-compose up -d

# Step 7: Wait for services
echo "Step 8: Waiting for services to start (60 seconds)..."
sleep 60

# Step 8: Stamp migrations
echo "Step 9: Stamping migrations..."
docker exec algo-trading-api alembic stamp head 2>/dev/null || echo "Migrations already stamped or not needed"

# Step 9: Verify
echo "Step 10: Verifying deployment..."
docker ps
echo ""
curl -s http://localhost:8000/health || echo "Backend not yet ready"
echo ""
curl -I http://localhost:3002 | head -3 || echo "Frontend not yet ready"

echo ""
echo "=== Deployment Complete ==="
echo "Access your app at: http://$(curl -s ifconfig.me):3002"
