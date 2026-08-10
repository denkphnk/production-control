from celery import Celery
from celery.schedules import crontab

from src.core.config import settings

celery_app = Celery(
    "production_control",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "src.tasks.batch_tasks",
        "src.tasks.report_tasks",
        "src.tasks.webhook_tasks",
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
    result_expires=3600,
    worker_pool="asyncio",
)

celery_app.conf.beat_schedule = {
    "auto-close-expired-batches": {
        "task": "src.tasks.batch_tasks.auto_close_expired_batches",
        "schedule": crontab(hour=1, minute=0),
    },
    "cleanup-old-files": {
        "task": "src.tasks.report_tasks.cleanup_old_files",
        "schedule": crontab(hour=2, minute=0),
    },
    "update-statistics": {
        "task": "src.tasks.batch_tasks.update_cached_statistics",
        "schedule": crontab(minute="*/5"),
    },
    "retry-failed-webhooks": {
        "task": "src.tasks.webhook_tasks.retry_failed_webhooks",
        "schedule": crontab(minute="*/15"),
    },
}

if __name__ == "__main__":
    celery_app.start()
