#!/bin/bash

# APK Finder Web Server Restart Script
# This script activates conda environment and starts the FastAPI server

echo "🔄 Restarting APK Finder Web Server..."

# Check if conda is available
if ! command -v conda &> /dev/null; then
    echo "❌ Error: conda command not found. Please ensure conda is installed and in PATH."
    exit 1
fi

# Activate conda environment
echo "🐍 Activating conda environment py311..."
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate py311

if [ $? -ne 0 ]; then
    echo "❌ Error: Failed to activate conda environment 'py311'"
    echo "   Please ensure the environment exists: conda create -n py311 python=3.11"
    exit 1
fi

echo "✅ Conda environment py311 activated"

# Navigate to server directory
SERVER_DIR="apk_finder/server"
if [ ! -d "$SERVER_DIR" ]; then
    echo "❌ Error: Server directory '$SERVER_DIR' not found"
    exit 1
fi

echo "📁 Navigating to server directory: $SERVER_DIR"
cd "$SERVER_DIR" || exit 1

# Check if main.py exists
if [ ! -f "main.py" ]; then
    echo "❌ Error: main.py not found in server directory"
    exit 1
fi



# Start the server
echo "🚀 Starting APK Finder Server on port 9301..."
echo "   Press Ctrl+C to stop the server"
echo "   Logs will be written to logs/apk_finder.log"
echo ""

# Run the server
nohup python main.py > running.log 2>&1 &