#!/bin/bash

# Trading Daemon Stop Script
# This script stops the running trading daemon

echo "Stopping Trading Daemon..."
echo "================================"

# Check if PID file exists
if [ ! -f data/daemon.pid ]; then
    echo "⚠️  No PID file found. Daemon may not be running."
    echo ""
    echo "Checking for running daemon processes..."
    if pgrep -f "trading_daemon" > /dev/null; then
        echo "Found daemon process(es). Killing them..."
        pkill -f "trading_daemon"
        echo "✅ Daemon stopped"
    else
        echo "No daemon processes found"
    fi
    exit 0
fi

# Read PID from file
DAEMON_PID=$(cat data/daemon.pid)

# Check if process is running
if ps -p $DAEMON_PID > /dev/null; then
    echo "Stopping daemon (PID: $DAEMON_PID)..."
    kill $DAEMON_PID
    
    # Wait for process to stop
    sleep 2
    
    # Check if it stopped
    if ps -p $DAEMON_PID > /dev/null; then
        echo "Process didn't stop gracefully, forcing..."
        kill -9 $DAEMON_PID
    fi
    
    echo "✅ Daemon stopped"
else
    echo "⚠️  Daemon process not found (PID: $DAEMON_PID)"
fi

# Remove PID file
rm -f data/daemon.pid

echo ""
echo "📊 View final logs:"
echo "   tail data/trading_daemon.log"
