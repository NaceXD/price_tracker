from celery import Celery
from src.core.config import settings

redis_url = f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0"

celery_instance = Celery(
    "price_tracker_tasks",
    broker=redis_url,
    backend=redis_url,
)

celery_instance.autodiscover_tasks(["src.tasks"])
