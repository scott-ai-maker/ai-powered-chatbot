#!/usr/bin/env bash
"""
Launch script for the AI Career Mentor Chatbot.

This script starts both the FastAPI backend and Streamlit frontend
in the correct order and provides useful information for users.
"""

echo "🚀 Starting AI Career Mentor Chatbot..."
echo "========================================"

# Get the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found. Please run setup first."
    exit 1
fi

# Activate virtual environment
source .venv/bin/activate

# Check if dependencies are installed
if ! python -c "import streamlit, fastapi" 2>/dev/null; then
    echo "❌ Dependencies not installed. Please run: pip install -r requirements.txt"
    exit 1
fi

echo "✅ Environment ready"

# Kill any existing processes
echo "🧹 Cleaning up existing processes..."
pkill -f "uvicorn.*8001" 2>/dev/null || true
pkill -f "streamlit.*8501" 2>/dev/null || true
sleep 2

echo "🔧 Starting FastAPI backend on port 8001..."
python -m uvicorn src.main:app --host 0.0.0.0 --port 8001 &
BACKEND_PID=$!

# Wait for backend to start
echo "⏳ Waiting for backend to initialize..."
sleep 5

# Check if backend is running
if curl -s http://localhost:8001/api/v1/health/live > /dev/null 2>&1; then
    echo "✅ Backend is running successfully"
else
    echo "❌ Backend failed to start"
    kill $BACKEND_PID 2>/dev/null || true
    exit 1
fi

echo "🎨 Starting Streamlit frontend on port 8501..."
python -m streamlit run src/frontend/app.py --server.port 8501 --server.address 0.0.0.0 --server.headless true &
FRONTEND_PID=$!

# Wait for frontend to start
echo "⏳ Waiting for frontend to initialize..."
sleep 5

echo ""
echo "🎉 AI Career Mentor Chatbot is now running!"
echo ""
echo "📡 Backend API:  http://localhost:8001"
echo "🌐 Frontend UI:  http://localhost:8501"
echo "📚 API Docs:     http://localhost:8001/docs"
echo ""
echo "💡 Usage Tips:"
echo "   - Open http://localhost:8501 in your browser to use the chat interface"
echo "   - Visit http://localhost:8001/docs to explore the API"
echo "   - Press Ctrl+C to stop both services"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down services..."
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    pkill -f "uvicorn.*8001" 2>/dev/null || true
    pkill -f "streamlit.*8501" 2>/dev/null || true
    echo "✅ Cleanup complete"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Wait for user to stop
echo "Press Ctrl+C to stop the application..."
wait