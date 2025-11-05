#!/bin/bash
set -e

# Add the current directory (which is now /backend) to the python path
export PYTHONPATH=. 

echo "Starting Celery Worker..."
# Tell celery to find the app at 'celery_app'
celery -A celery_app worker --loglevel=INFO -P gevent -c 10 &

echo "Starting FastAPI API Server..."
# Tell uvicorn to find the app at 'api.main:app'
uvicorn api.main:app --host 0.0.0.0 --port $PORT