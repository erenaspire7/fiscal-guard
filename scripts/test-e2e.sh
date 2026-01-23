#!/bin/bash
# Run E2E tests for Fiscal Guard

set -e

# Parse flags
RESET_DB=false
TEST_SCENARIO=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --reset-db)
            RESET_DB=true
            shift
            ;;
        *)
            TEST_SCENARIO="$1"
            shift
            ;;
    esac
done

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
}

# Set up trap to catch Ctrl+C (SIGINT) and other termination signals
trap cleanup SIGINT SIGTERM EXIT

echo "🧪 Starting E2E Test Environment..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Copying from .env.example..."
    cp .env.example .env
    echo "📝 Please edit .env with your credentials (especially GOOGLE_API_KEY) before running again"
    exit 1
fi

# Export environment variables from .env file
echo "📦 Loading environment variables..."
set -a
source .env
set +a

# Check for required GOOGLE_API_KEY
if [ -z "$GOOGLE_API_KEY" ] || [ "$GOOGLE_API_KEY" = "your-google-api-key" ]; then
    echo "❌ GOOGLE_API_KEY is required for E2E tests"
    echo "   Please set it in your .env file"
    echo "   Get your key from: https://makersuite.google.com/app/apikey"
    exit 1
fi

# Disable Opik tracing for tests
export OPIK_TRACING_ENABLED=false

# Reset database if requested
if [ "$RESET_DB" = true ]; then
    echo "🗑️  Resetting database..."
    cd core

    # Drop all tables by downgrading to base
    echo "   Dropping all tables..."
    uv run alembic downgrade base

    # Run migrations from scratch
    echo "   Running migrations from scratch..."
    uv run alembic upgrade head

    cd ..
    echo "✅ Database reset complete"
else
    # Run migrations normally
    echo "🔄 Running database migrations..."
    cd core
    uv run migrate
    cd ..
fi

# Start API in background
echo "🚀 Starting API server..."
cd api
uv run uvicorn src.api.main:app --port 8000 &
API_PID=$!
echo "   API started with PID: $API_PID"
cd ..

# Start UI in background
echo "🎨 Starting UI server..."
cd ui
yarn dev --port 5173 &
UI_PID=$!
echo "   UI started with PID: $UI_PID"
cd ..

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 5

# Health check for API
MAX_RETRIES=30
RETRY_COUNT=0
echo "🔍 Checking API health..."
while ! curl -s http://localhost:8000/health > /dev/null; do
    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
        echo "❌ API failed to start after ${MAX_RETRIES} attempts"
        exit 1
    fi
    echo "   Waiting for API... (${RETRY_COUNT}/${MAX_RETRIES})"
    sleep 1
done
echo "✅ API is ready"

# Health check for UI
echo "🔍 Checking UI health..."
RETRY_COUNT=0
while ! curl -s http://localhost:5173 > /dev/null; do
    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
        echo "❌ UI failed to start after ${MAX_RETRIES} attempts"
        exit 1
    fi
    echo "   Waiting for UI... (${RETRY_COUNT}/${MAX_RETRIES})"
    sleep 1
done
echo "✅ UI is ready"

# Run E2E tests
echo ""
echo "🎬 Running E2E tests..."
cd e2e-tests

# Check if specific test scenario is provided
if [ -n "$TEST_SCENARIO" ]; then
    echo "   Running scenario: $TEST_SCENARIO"
    yarn test:$TEST_SCENARIO
else
    echo "   Running all tests"
    yarn test
fi

TEST_EXIT_CODE=$?

cd ..

echo ""
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo "✅ All tests passed!"
else
    echo "❌ Some tests failed (exit code: $TEST_EXIT_CODE)"
fi

exit $TEST_EXIT_CODE
