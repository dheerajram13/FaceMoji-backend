from celery import Celery
from app.core.config import settings

# Create Celery app with explicit Redis configuration
app = Celery(
    'facemoji_tasks',
    broker='redis://redis:6379/0',
    backend='redis://redis:6379/0',
    include=['app.services.face_processor']
)

# Configure Celery
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    worker_concurrency=4,  # Number of worker processes
    task_time_limit=300,   # Maximum task execution time in seconds
    task_soft_time_limit=240,  # Soft time limit before task is terminated
    broker_connection_retry_on_startup=True,  # Add retry on startup
    task_track_started=True,  # Track task start time
    result_expires=3600  # Results expire after 1 hour
)
