#!/bin/bash
set -e

echo "Starting Celery Worker..."
# Call the app directly, as 'backend' is the root
celery -A celery_app worker --loglevel=INFO -P gevent -c 10 &

echo "Starting FastAPI API Server..."
# Call the app directly
uvicorn api.main:app --host 0.0.0.0 --port $PORT