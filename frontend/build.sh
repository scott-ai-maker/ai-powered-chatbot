#!/bin/bash

# Build script for AI Career Mentor Frontend
# Builds the React application for production deployment

set -e

echo "🚀 Building AI Career Mentor Frontend..."

# Install dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

# Build the application
echo "🏗️ Building React application..."
npm run build

echo "✅ Build completed successfully!"
echo "📁 Built files are in the 'build' directory"
echo "🌐 Ready for deployment!"