from src.celery_app import celery_app
from src.core.database import AsyncSessionLocal
from src.domain.services.webhook_service import WebhookService



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
async def retry_failed_webhooks(self):
    async with AsyncSessionLocal() as session:
        webhook_service = WebhookService(session)

        deliveries = await webhook_service.get_failed()
        for delivery in deliveries:
            if delivery.attempts < delivery.subscription.retry_count:
                send_webhook_delivery.delay(delivery.id)
