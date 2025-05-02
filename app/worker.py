from celery import Celery
from app.core.config import settings

# Create Celery app
app = Celery(
    'facemoji_tasks',
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
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
    task_soft_time_limit=240  # Soft time limit before task is terminated
)
