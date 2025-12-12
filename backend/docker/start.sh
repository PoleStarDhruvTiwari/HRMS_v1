#!/bin/bash

set -e

echo "Starting HRMS FastAPI Backend..."

# Wait for database to be ready
if [ -n "$DATABASE_URL" ]; then
    echo "Waiting for database..."
    until pg_isready -h db -p 5432 -U postgres; do
        echo "Database is unavailable - sleeping"
        sleep 2
    done
    echo "Database is up - continuing"
fi

# Run migrations (if using Alembic)
# echo "Running database migrations..."
# alembic upgrade head

# Start the application
if [ "$ENVIRONMENT" = "production" ]; then
    echo "Starting in production mode with Gunicorn..."
    exec gunicorn -c docker/gunicorn_conf.py app.main:app
else
    echo "Starting in development mode with Uvicorn..."
    exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
fi