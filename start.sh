#!/bin/sh

# Start MeiliSearch in the background
echo "Starting MeiliSearch..."
meilisearch --db-path /app/data/meili_data --http-addr 0.0.0.0:7700 --no-analytics &
MEILI_PID=$!

# Wait for MeiliSearch to be ready
echo "Waiting for MeiliSearch to start..."
until curl -s http://localhost:7700/health > /dev/null; do
    sleep 1
done
echo "MeiliSearch is ready!"

# Start the FastAPI application
echo "Starting FastAPI application..."
exec uv run uvicorn app.main:app --host 0.0.0.0 --port 8000