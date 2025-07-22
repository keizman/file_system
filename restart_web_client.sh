#!/bin/bash

# APK Finder Web Client Build Script
# This script builds the Vue.js web client

echo "🔄 Building APK Finder Web Client..."

# Navigate to web client directory
WEB_CLIENT_DIR="apk_finder/web_client"
if [ ! -d "$WEB_CLIENT_DIR" ]; then
    echo "❌ Error: Web client directory '$WEB_CLIENT_DIR' not found"
    exit 1
fi

echo "📁 Navigating to web client directory: $WEB_CLIENT_DIR"
cd "$WEB_CLIENT_DIR" || exit 1

# Check if package.json exists
if [ ! -f "package.json" ]; then
    echo "❌ Error: package.json not found in web client directory"
    exit 1
fi

# Check if npm is available
if ! command -v npm &> /dev/null; then
    echo "❌ Error: npm command not found. Please ensure Node.js and npm are installed."
    exit 1
fi

# Install dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
    if [ $? -ne 0 ]; then
        echo "❌ Error: Failed to install dependencies"
        exit 1
    fi
else
    echo "📦 Dependencies already installed, updating..."
    npm install --silent
fi

echo "✅ Dependencies ready"

# Run build
echo "🏗️  Building Vue.js web client..."
echo "   This may take a few moments..."
echo ""

npm run build

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Web client build completed successfully!"
    echo "   Build files are located in: dist/"
    echo "   You can serve the built files with any web server"
    echo ""
    echo "💡 To serve locally, you can run:"
    echo "   npm run preview  (serves the built files)"
    echo "   npm run dev      (development server with hot reload)"
else
    echo ""
    echo "❌ Build failed. Please check the error messages above."
    exit 1
fi