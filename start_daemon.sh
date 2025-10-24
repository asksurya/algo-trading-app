#!/bin/bash

# Trading Daemon Startup Script
# This script starts the trading daemon as a background process

echo "Starting Trading Daemon..."
echo "================================"

# Check if daemon is already running
if pgrep -f "trading_daemon" > /dev/null; then
    echo "⚠️  Daemon is already running!"
    echo "To stop it, run: ./stop_daemon.sh"
    exit 1
fi

# Create data directory if it doesn't exist
mkdir -p data

# Start the daemon
nohup python -m src.trading.trading_daemon > data/daemon_output.log 2>&1 &

# Get the process ID
DAEMON_PID=$!

# Save PID to file
echo $DAEMON_PID > data/daemon.pid

echo "✅ Trading Daemon started!"
echo "Process ID: $DAEMON_PID"
echo ""
echo "📊 Monitor logs:"
echo "   tail -f data/trading_daemon.log"
echo ""
echo "⏹️  Stop daemon:"
echo "   ./stop_daemon.sh"
echo ""
echo "🎛️  Control trading:"
echo "   Use the Live Trading V2 page in the web interface"
