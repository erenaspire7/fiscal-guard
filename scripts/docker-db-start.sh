#!/bin/bash

# Fiscal Guard - PostgreSQL Database Startup Script
# This script starts a PostgreSQL 15 container for local development
# using Docker directly (without docker-compose)

set -e

# Configuration
CONTAINER_NAME="fiscal-guard-postgres"
POSTGRES_USER="postgres"
POSTGRES_PASSWORD="postgres"
POSTGRES_DB="fiscal_guard"
POSTGRES_PORT="5432"
VOLUME_NAME="fiscal-guard-postgres-data"

echo "🚀 Starting Fiscal Guard PostgreSQL database..."

# Check if container already exists
if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "📦 Container '${CONTAINER_NAME}' already exists"

    # Check if it's running
    if docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        echo "✅ Database is already running"
        echo "🔗 Connection: postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@localhost:${POSTGRES_PORT}/${POSTGRES_DB}"
        exit 0
    else
        echo "▶️  Starting existing container..."
        docker start "${CONTAINER_NAME}"
    fi
else
    echo "🆕 Creating new PostgreSQL container..."

    # Create Docker volume if it doesn't exist
    if ! docker volume ls --format '{{.Name}}' | grep -q "^${VOLUME_NAME}$"; then
        echo "📁 Creating volume '${VOLUME_NAME}'..."
        docker volume create "${VOLUME_NAME}"
    fi

    # Run new container
    docker run -d \
        --name "${CONTAINER_NAME}" \
        -e POSTGRES_USER="${POSTGRES_USER}" \
        -e POSTGRES_PASSWORD="${POSTGRES_PASSWORD}" \
        -e POSTGRES_DB="${POSTGRES_DB}" \
        -p "${POSTGRES_PORT}:5432" \
        -v "${VOLUME_NAME}:/var/lib/postgresql/data" \
        --health-cmd "pg_isready -U postgres" \
        --health-interval 5s \
        --health-timeout 5s \
        --health-retries 5 \
        postgres:15-alpine
fi

# Wait for database to be healthy
echo "⏳ Waiting for database to be ready..."
TIMEOUT=30
ELAPSED=0

while [ $ELAPSED -lt $TIMEOUT ]; do
    if docker exec "${CONTAINER_NAME}" pg_isready -U "${POSTGRES_USER}" > /dev/null 2>&1; then
        echo "✅ Database is ready!"
        echo ""
        echo "📊 Connection Details:"
        echo "   Host: localhost"
        echo "   Port: ${POSTGRES_PORT}"
        echo "   Database: ${POSTGRES_DB}"
        echo "   User: ${POSTGRES_USER}"
        echo "   Password: ${POSTGRES_PASSWORD}"
        echo ""
        echo "🔗 Connection String:"
        echo "   postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@localhost:${POSTGRES_PORT}/${POSTGRES_DB}"
        echo ""
        echo "🛠️  Useful Commands:"
        echo "   Stop:    docker stop ${CONTAINER_NAME}"
        echo "   Restart: docker restart ${CONTAINER_NAME}"
        echo "   Logs:    docker logs ${CONTAINER_NAME}"
        echo "   Shell:   docker exec -it ${CONTAINER_NAME} psql -U ${POSTGRES_USER} -d ${POSTGRES_DB}"
        exit 0
    fi

    sleep 1
    ELAPSED=$((ELAPSED + 1))
    echo -n "."
done

echo ""
echo "❌ Database failed to start within ${TIMEOUT} seconds"
echo "📋 Check logs with: docker logs ${CONTAINER_NAME}"
exit 1
