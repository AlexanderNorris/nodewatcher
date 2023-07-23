from celery import Celery
from celery.schedules import crontab
import requests
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)

session = requests.Session()
session.headers = {"User-Agent": "NodeWatcher Release 0.1"}


CELERY_BROKER_URL = "redis://redis:6379/0"
CELERY_RESULT_BACKEND = "redis://redis:6379/1"
CELERY_BEAT_SCHEDULE = {
    "pool-update": {
        "task": "update_pools",
        # Discovery runs nightly at midnight for pools
        # Add random offset of 1 hour here to reduce spike against Koios API
        "schedule": crontab(minute=0, hour=0),
    },
    "metric-gathering": {"task": "gather_metrics", "schedule": 600},
}

app = Celery(include=["pool_tasks", "relay_tasks"])
app.conf.broker_url = CELERY_BROKER_URL
app.conf.result_backend = CELERY_RESULT_BACKEND
app.conf.beat_schedule = CELERY_BEAT_SCHEDULE
app.autodiscover_tasks()
