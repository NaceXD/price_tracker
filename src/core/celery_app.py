from celery import Celery
from celery.schedules import crontab
from src.core.config import settings

redis_url = f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0"

celery_instance = Celery(
    "price_tracker_tasks",
    broker=redis_url,
    backend=redis_url,
)

celery_instance.autodiscover_tasks(["src.tasks"])

celery_instance.conf.beat_schedule = {
    "parse_prices_every_5_minutes": {
        "task": "tasks.fetch_all_routes_prices",
        "schedule": crontab(minute="*/5"),
    }
}