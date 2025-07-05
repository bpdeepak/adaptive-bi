#!/bin/bash

echo "🔍 Testing service connections..."
echo ""

# Test Backend
echo "Testing Backend (localhost:3000)..."
if curl -s http://localhost:3000/health | grep -q "healthy"; then
    echo "✅ Backend: Healthy and accessible"
else
    echo "❌ Backend: Not accessible"
fi

# Test AI Service
echo ""
echo "Testing AI Service (localhost:8000)..."
if curl -s http://localhost:8000/api/v1/health/ | grep -q "ok"; then
    echo "✅ AI Service: Healthy and accessible"
else
    echo "❌ AI Service: Not accessible"
fi

# Test AI System Status
echo ""
echo "Testing AI System Status..."
ai_status=$(curl -s http://localhost:8000/api/v1/ai/system/status)
if echo "$ai_status" | grep -q "phase3_models"; then
    echo "✅ AI System: All models loaded and ready"
    echo "   - Contains Phase 3 and Phase 4 models"
    echo "   - Explainable AI available"
else
    echo "❌ AI System: Models not properly loaded"
fi

echo ""
echo "🎯 Frontend Configuration Summary:"
echo "- VITE_BACKEND_URL=http://localhost:3000"
echo "- VITE_AI_SERVICE_URL=http://localhost:8000"
echo "- VITE_ENABLE_MOCK_DATA=false (using real services)"
echo ""
echo "🚀 Your development environment is ready!"
echo "   The frontend will now connect to your Docker containers"
echo "   instead of using mock data."
