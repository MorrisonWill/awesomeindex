#!/bin/sh

# Start MeiliSearch in the background
echo "Starting MeiliSearch..."
meilisearch --db-path /app/data/meili_data --http-addr 0.0.0.0:7700 --no-analytics &
MEILI_PID=$!

# Start the FastAPI application
echo "Starting FastAPI application..."
exec uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
