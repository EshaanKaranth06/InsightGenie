#!/bin/bash
set -e

# We don't need PYTHONPATH if the Root Directory is correct
echo "Starting Celery Worker..."
# Call 'celery_app' (celery_app.py) directly
celery -A celery_app worker --loglevel=INFO -P gevent -c 10 &

echo "Starting FastAPI API Server..."
# Call 'api.main' (api/main.py) directly
uvicorn api.main:app --host 0.0.0.0 --port $PORT