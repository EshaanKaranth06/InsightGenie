#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

export PYTHONPATH=/opt/render/project/src

echo "Starting Celery Worker..."
# Start the Celery worker in the background
# Use -P solo for the free tier to save resources
celery -A backend.celery_app worker --loglevel=INFO -P gevent -c 10 &

echo "Starting FastAPI API Server..."
# Start the Uvicorn server in the foreground
# Render provides the $PORT variable
uvicorn backend.api.main:app --host 0.0.0.0 --port $PORT