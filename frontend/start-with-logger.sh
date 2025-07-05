#!/bin/bash

# Start Adaptive BI Frontend with Logger Server
echo "🚀 Starting Adaptive BI Frontend with Logger Server..."

# Function to kill background processes on exit
cleanup() {
    echo "🛑 Shutting down services..."
    kill $LOGGER_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    exit 0
}

# Setup trap to cleanup on script exit
trap cleanup SIGINT SIGTERM

# Install logger server dependencies if needed
if [ ! -d "node_modules_logger" ]; then
    echo "📦 Installing logger server dependencies..."
    npm install --prefix . express cors
fi

# Start logger server in background
echo "🔧 Starting logger server on port 3001..."
node loggerServer.cjs &
LOGGER_PID=$!

# Wait for logger server to start
sleep 2

# Check if logger server is running
if curl -s http://localhost:3001/health > /dev/null; then
    echo "✅ Logger server is running at http://localhost:3001"
else
    echo "❌ Failed to start logger server"
    exit 1
fi

# Start frontend development server
echo "🎨 Starting frontend development server..."
npm run dev &
FRONTEND_PID=$!

# Wait for frontend to start
sleep 3

echo ""
echo "🎉 Services started successfully!"
echo "🌐 Frontend: http://localhost:5173"
echo "📝 Logger Server: http://localhost:3001"
echo "📁 Logs will be saved to: ./logs/"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for frontend process to finish
wait $FRONTEND_PID
