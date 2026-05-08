from celery import Celery
from analysis import REDIS_URL

celery_app = Celery(
    "analysis_service",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=[
        "analysis.tasks.process_crawl",
        "analysis.tasks.detect_trends",
        "analysis.tasks.extract_ingredients",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,
    task_soft_time_limit=25 * 60,
    worker_max_tasks_per_child=100,
)
