from celery import Celery
from celery.schedules import crontab
from analysis import REDIS_URL

celery_app = Celery(
    "analysis_service",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=[
        "analysis.tasks.process_crawl",
        "analysis.tasks.detect_trends",
        "analysis.tasks.extract_ingredients",
        "analysis.tasks.snapshot_trends",
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
    beat_schedule={
        "process-crawl-every-5-minutes": {
            "task": "analysis.tasks.process_crawl.process_crawl_data",
            "schedule": crontab(minute="*/5"),
            "options": {"expires": 60},
        },
        "detect-trends-every-15-minutes": {
            "task": "analysis.tasks.detect_trends.detect_food_trends",
            "schedule": crontab(minute="*/15"),
            "options": {"expires": 120},
        },
        "snapshot-trends-daily-midnight": {
            "task": "analysis.tasks.snapshot_trends.snapshot_trending_foods",
            "schedule": crontab(hour=0, minute=0),
            "options": {"expires": 3600},
        },
    },
)
