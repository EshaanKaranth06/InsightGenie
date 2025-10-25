import os
from celery import Celery
from dotenv import load_dotenv

# Load .env relative to this file's location (assuming .env is in backend/)
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path=dotenv_path)

broker_url = os.getenv("CELERY_BROKER_URL")
result_backend = os.getenv("CELERY_RESULT_BACKEND")

if not broker_url or not result_backend:
    raise ValueError("Celery Broker or Result Backend URL not found in .env file.")

celery = Celery(
    __name__, 
    broker=broker_url,
    backend=result_backend,
    include=['backend.pipeline.tasks', 'backend.reports.report_gen'] # Tells Celery where task functions are
)

celery.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)

# Optional: Add simple task for testing worker connection
@celery.task
def add(x, y):
    return x + y
