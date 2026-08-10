from datetime import datetime, timedelta, timezone

from src.celery_app import celery_app
from src.core.database import AsyncSessionLocal
from src.data.repositories.report_repository import ReportRepository
from src.domain.services.webhook_service import WebhookService
from src.storage.minio_service import minio_service


@celery_app.task(bind=True, max_retries=3)
async def send_webhook_delivery(self, delivery_id: int):
    try:
        async with AsyncSessionLocal() as session:
            service = WebhookService(session)

            delivery = await service.webhook_repo.get_delivery_by_id(delivery_id)

            subscription = delivery.subscription

            await service._send_to_subscriber(delivery, subscription, delivery.payload)
    except Exception as exc:
        countdown = 30 * (2**self.request.retries)

        raise self.retry(exc=exc, countdown=countdown)


@celery_app.task(bind=True, max_retries=3)
async def cleanup_old_files(self):
    try:
        async with AsyncSessionLocal() as session:
            report_repo = ReportRepository(session)

            cutoff_date = datetime.now(timezone.utc) - timedelta(days=30)

            reports = await report_repo.get_older_than(cutoff_date)

            for report in reports:
                try:
                    minio_service.delete_file(
                        bucket="reports", object_name=report.file_name
                    )
                except Exception:
                    pass

                await report_repo.delete(report.id)

            await session.commit()

    except Exception as exc:
        raise self.retry(exc=exc, countdown=60 * (2**self.request.retries))


@celery_app.task(bind=True, max_retries=3)
async def retry_failed_webhooks(self):
    async with AsyncSessionLocal() as session:
        webhook_service = WebhookService(session)

        deliveries = await webhook_service.get_failed()
        for delivery in deliveries:
            if delivery.attempts < delivery.subscription.retry_count:
                send_webhook_delivery.delay(delivery.id)
