import hashlib
import hmac
import json
from fastapi.encoders import jsonable_encoder
import httpx

from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.schemas.webhook import WebhookCreate, WebhookUpdate
from src.data.models.webhook import WebhookDelivery, WebhookSubscription
from src.data.repositories.webhook_repository import WebhookRepository


class WebhookService:
    """Сервис для отправки вебхуков"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.webhook_repo = WebhookRepository(session)
        self.http_client = httpx.AsyncClient(timeout=10.0)

    async def get_by_id(self, subscription_id: int) -> WebhookSubscription:
        return await self.webhook_repo.get_by_id(subscription_id)


    ##########################################
    # СОЗДАНИЕ ПОДПИСКИ
    ##########################################
    async def create(self, data: WebhookCreate) -> WebhookSubscription:
        """Создает подписку"""
        data = data.model_dump()
        data["url"] = str(data['url'])

        existing = await self.webhook_repo.get_by_url(data["url"])
        if existing:
            raise ValueError(f"Webhook with URL {data['url']} already exists")
        try:
            subscription = await self.webhook_repo.create(data)
            await self.session.commit()
            self.session.refresh(subscription)
            return subscription
        except Exception:
            await self.session.rollback()
            raise

    ##########################################
    # ПОЛУЧЕНИЕ ВСЕХ ПОДПИСОК
    ##########################################
    async def get_all(self, offset: int = 0, limit: int = 20) -> Tuple[List[WebhookSubscription], int]:
        """Возвращает список всех подписок."""
        return await self.webhook_repo.get_all_with_count(offset, limit)

    async def get_failed(self):
        return await self.webhook_repo.get_failed_deliveries()

    ##########################################
    # ОБНОВЛЕНИЕ ПОДПИСКИ
    ##########################################
    async def update(self, subscription_id: int, data: WebhookUpdate) -> Optional[WebhookSubscription]:
        """Обновляет подписку."""
        existing = await self.webhook_repo.get_by_id(subscription_id)
        if not existing:
            return None

        update_data = data.model_dump(exclude_unset=True)

        if "url" in update_data:
            url_exists = await self.webhook_repo.get_by_url(update_data["url"])
            if url_exists and url_exists.id != subscription_id:
                raise ValueError(f"Webhook with URL {update_data['url']} already exists")

        try:
            subscription = await self.webhook_repo.update(subscription_id, update_data)
            await self.session.commit()
            await self.session.refresh(subscription)
            return subscription
        except Exception:
            await self.session.rollback()
            raise

    ##########################################
    # УДАЛЕНИЕ ПОДПИСКИ
    ##########################################
    async def delete(self, subscription_id: int) -> bool:
        """Удаляет подписку."""
        deleted = await self.webhook_repo.delete(subscription_id)
        await self.session.commit()
        return deleted

    ##########################################
    # ИСТОРИЯ ДОСТАВОК
    ##########################################
    async def get_deliveries(
        self,
        subscription_id: int,
        offset: int = 0,
        limit: int = 20
    ) -> Tuple[List[WebhookDelivery], int]:
        """Возвращает историю доставок для подписки."""
        return await self.webhook_repo.get_deliveries_for_subscription(
            subscription_id, offset, limit
        )

    async def send_event(
        self, event_type: str, payload: Dict[str, Any], async_mode: bool
    ) -> None:
        """Отправляет событие всем подписчикам"""
        from src.tasks.webhook_tasks import send_webhook_delivery


        subscriptions = await self.webhook_repo.get_active_subscriptions_for_event(
            event_type
        )

        if not subscriptions:
            return

        webhook_payload = {
            "event": event_type,
            "data": jsonable_encoder(payload),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        for subscription in subscriptions:
            delivery = await self.webhook_repo.create_delivery(
                {
                    "subscription_id": subscription.id,
                    "event_type": webhook_payload["event"],
                    "payload": webhook_payload,
                    "status": "pending",
                    "attempts": 0,
                }
            )
            await self.session.commit()
            if async_mode:
                send_webhook_delivery.delay(delivery.id)
            else:
                await self._send_to_subscriber(delivery, subscription, webhook_payload)

    async def _send_to_subscriber(
        self, delivery: WebhookDelivery, subscription: WebhookSubscription, payload: Dict[str, Any]
    ) -> None:
        """Отправляет событие подписчику"""
        try:
            signature = self._create_signature(payload, subscription.secret_key)

            response = await self.http_client.post(
                subscription.url,
                json=payload,
                headers={
                    "X-Webhook-Signature": signature,
                    "Content-Type": "application/json",
                },
                timeout=subscription.timeout,
            )

            if 200 <= response.status_code < 300:
                status = "success"
            else:
                status = "failed"
            response_body = response.text[:500]

            await self._save_delivery_result(
                delivery_id=delivery.id,
                status=status,
                response_status=response.status_code,
                response_body=response_body,
            )
        except httpx.TimeoutException:
            await self._save_delivery_result(
                delivery_id=delivery.id,
                status="failed",
                error_message=f"Timeout after {subscription.timeout}s",
            )


    def _create_signature(self, payload: Dict[str, Any], secret_key: str) -> str:
        """Создает HMAC-SHA256 подпись для вебхука"""
        payload_str = json.dumps(payload, sort_keys=True)

        signature = hmac.new(
            secret_key.encode(), payload_str.encode(), hashlib.sha256
        ).hexdigest()

        return signature

    async def _save_delivery_result(
        self,
        delivery_id: int,
        status: str,
        response_status: Optional[int] = None,
        response_body: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> None:
        """Сохраняет результат доставки в БД"""
        delivery = await self.webhook_repo.get_delivery_by_id(delivery_id)
        if not delivery:
            return

        delivery.status = status
        delivery.attempts = delivery.attempts + 1
        delivery.response_status = response_status
        delivery.response_body = response_body
        delivery.error_message = error_message

        if status == "success":
            delivery.delivered_at = datetime.now(timezone.utc)

        await self.session.commit()
