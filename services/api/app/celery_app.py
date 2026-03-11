import os
from celery import Celery

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))

CELERY_BROKER_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
CELERY_BACKEND_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"

celery_app = Celery(
    "video_platform",
    broker=CELERY_BROKER_URL,
    backend=CELERY_BACKEND_URL
)

celery_app.conf.update(
    task_track_started=True,
    result_expires=3600,  # Results expire after 1 hour
)

celery_app.conf.broker_connection_retry_on_startup = True