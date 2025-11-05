#!/bin/bash
set -e
export PYTHONPATH=.
echo "Starting Celery Worker..."
# This command now works because Render is in the root and can find 'backend'
celery -A backend.celery_app worker --loglevel=INFO -P gevent -c 10 &

echo "Starting FastAPI API Server..."
# This command also works now
uvicorn backend.api.main:app --host 0.0.0.0 --port $PORT