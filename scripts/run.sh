#!/bin/bash
# Start the Fiscal Guard API

set -e

echo "🚀 Starting Fiscal Guard API..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Copying from .env.example..."
    cp .env.example .env
    echo "📝 Please edit .env with your credentials before running again"
    exit 1
fi


# Run migrations
echo "📦 Running database migrations..."
cd core
~/.local/bin/uv run alembic upgrade head
cd ..

# # Start API
# echo "✨ Starting FastAPI server..."
# cd api
# ~/.local/bin/uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
