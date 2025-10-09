#!/bin/bash

# Development server for AI Career Mentor Frontend
# Starts the React development server with hot reloading

set -e

echo "🚀 Starting AI Career Mentor Frontend Development Server..."

# Install dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

# Start development server
echo "🌟 Starting development server..."
echo "🌐 Frontend will be available at http://localhost:3000"
echo "🔌 Backend should be running at http://localhost:8000"

npm start