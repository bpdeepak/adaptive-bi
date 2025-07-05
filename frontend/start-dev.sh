#!/bin/bash

# Adaptive BI Frontend Development Setup Script

echo "🚀 Starting Adaptive BI Frontend Development Server"
echo "=================================================="

# Check if we're in the frontend directory
if [ ! -f "package.json" ]; then
    echo "❌ Error: package.json not found. Please run this script from the frontend directory."
    exit 1
fi

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

# Check for .env file
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found. Creating from template..."
    cat > .env << EOF
# Backend API URL
VITE_BACKEND_URL=http://localhost:3000

# AI Service URL
VITE_AI_SERVICE_URL=http://localhost:8000

# Environment
VITE_NODE_ENV=development
EOF
    echo "✅ Created .env file with default settings"
fi

echo "🔧 Environment Configuration:"
echo "   - Backend API: ${VITE_BACKEND_URL:-http://localhost:3000}"
echo "   - AI Service: ${VITE_AI_SERVICE_URL:-http://localhost:8000}"
echo ""

echo "🌟 Starting development server..."
echo "   - Frontend will be available at: http://localhost:5173"
echo "   - Press Ctrl+C to stop the server"
echo ""

# Start the development server
npm run dev
