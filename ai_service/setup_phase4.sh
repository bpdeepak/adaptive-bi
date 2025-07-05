#!/bin/bash

# Phase 4 Setup Script for Advanced AI Features
echo "🚀 Setting up Phase 4 Advanced AI Features..."

# Install Phase 4 dependencies
echo "📦 Installing Phase 4 dependencies..."
pip install -r requirements_phase4.txt

# Fix NumPy compatibility issue
echo "🔧 Fixing NumPy compatibility..."
pip install "numpy<2"

# Install Redis (if not already installed)
echo "🔧 Setting up Redis..."
# For Ubuntu/Debian
if command -v apt-get &> /dev/null; then
    sudo apt-get update
    sudo apt-get install -y redis-server
    # Don't fail if Redis service doesn't start - it's optional for Phase 4
    sudo systemctl start redis-server || echo "⚠️  Redis service could not start, but it's optional for Phase 4"
    sudo systemctl enable redis-server
fi

# For MacOS (if using Homebrew)
if command -v brew &> /dev/null; then
    brew install redis
    brew services start redis || echo "⚠️  Redis service could not start, but it's optional for Phase 4"
fi

echo "✅ Phase 4 setup complete!"
echo "📋 Next steps:"
echo "   1. Restart the AI service to load Phase 4 models"
echo "   2. Check logs for Phase 4 model initialization"
echo "   3. Test Phase 4 endpoints in advanced_endpoints.py"
echo ""
echo "🔍 To test Phase 4 manually:"
echo "   python test_phase4.py"
