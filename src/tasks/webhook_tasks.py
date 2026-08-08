from src.domain.services.webhook_service import WebhookService
from src.core.database import AsyncSessionLocal
from src.celery_app import celery_app


# TODO: send_webhook_deliveries 

# TODO: cleanup_old_files()
@celery_app.task(bind=True, max_retries=3)
async def cleanup_old_files(self):
    pass


# TODO: retry_failed_webhooks()
@celery_app.task(bind=True, max_retries=3)
async def retry_failed_webhooks(self):
    async with AsyncSessionLocal() as session:
        webhook_service = WebhookService(session)

        deliveries = await webhook_service.get_failed()
        for delivery in deliveries:
            if delivery.attempts < delivery.subscription.retry_count:
