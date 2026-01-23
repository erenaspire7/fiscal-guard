#!/bin/bash
# Start the Fiscal Guard API

set -e

# Track PIDs for cleanup
API_PID=""
UI_PID=""

# Cleanup function
cleanup() {
    echo ""
    echo "🛑 Shutting down services..."

    if [ -n "$API_PID" ]; then
        echo "Stopping API (PID: $API_PID)..."
        kill $API_PID 2>/dev/null || true
    fi

    if [ -n "$UI_PID" ]; then
        echo "Stopping UI (PID: $UI_PID)..."
        kill $UI_PID 2>/dev/null || true
    fi

    echo "✅ Cleanup complete"
    exit 0
}

# Set up trap to catch Ctrl+C (SIGINT) and other termination signals
trap cleanup SIGINT SIGTERM

echo "🚀 Starting Fiscal Guard API..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Copying from .env.example..."
    cp .env.example .env
    echo "📝 Please edit .env with your credentials before running again"
    exit 1
fi

# Export environment variables from .env file
echo "📦 Loading environment variables..."
set -a
source .env
set +a

# Run migrations
cd core
uv run migrate

# Start API in background
cd ../api
uv run serve &
API_PID=$!
echo "API started with PID: $API_PID"

# Start UI in background
cd ../ui
yarn dev &
UI_PID=$!
echo "UI started with PID: $UI_PID"

# Wait for both processes
echo "Press Ctrl+C to stop all services..."
wait
