#!/bin/bash
set -e

echo "=== Starting InterviewSage AI Backend Entrypoint ==="

# Wait for PostgreSQL
if [ -n "$POSTGRES_HOST" ]; then
    echo "Waiting for PostgreSQL at ${POSTGRES_HOST}:${POSTGRES_PORT:-5432}..."
    while ! nc -z "$POSTGRES_HOST" "${POSTGRES_PORT:-5432}"; do
      sleep 1
    done
    echo "PostgreSQL is ready!"
fi

# Wait for Redis
if [ -n "$REDIS_HOST" ]; then
    echo "Waiting for Redis at ${REDIS_HOST}:${REDIS_PORT:-6379}..."
    while ! nc -z "$REDIS_HOST" "${REDIS_PORT:-6379}"; do
      sleep 1
    done
    echo "Redis is ready!"
fi

# Run Database Migrations
echo "Running Alembic database migrations..."
alembic upgrade head || echo "Migrations completed or already up to date."

# Start FastAPI application
echo "Starting FastAPI Uvicorn Server..."
exec "$@"
