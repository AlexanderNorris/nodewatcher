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
    "nodewatcher": {
        "task": "update_pools",
        "schedule": 3600,
    },
}

app = Celery(include=["pool_tasks"])
app.conf.broker_url = CELERY_BROKER_URL
app.conf.result_backend = CELERY_RESULT_BACKEND
app.conf.beat_schedule = CELERY_BEAT_SCHEDULE
