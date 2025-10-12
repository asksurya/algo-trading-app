#!/bin/bash

# Algorithmic Trading GUI Launcher
# This script launches the Streamlit web application

echo "🚀 Starting Algorithmic Trading Platform..."
echo ""

# Check if streamlit is installed
if ! command -v streamlit &> /dev/null
then
    echo "⚠️  Streamlit not found. Installing dependencies..."
    pip3 install -r requirements.txt
fi

# Launch the app
echo "📈 Launching web interface..."
echo "🌐 The app will open in your default browser"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Try multiple methods to run streamlit
if command -v streamlit &> /dev/null; then
    streamlit run app.py
elif command -v python3 &> /dev/null; then
    python3 -m streamlit run app.py
elif command -v python &> /dev/null; then
    python -m streamlit run app.py
else
    echo "❌ Error: Python not found. Please install Python 3.9+"
    exit 1
fi
