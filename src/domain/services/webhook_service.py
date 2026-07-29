import asyncio
import hashlib
import hmac
import json
import httpx

from typing import Any, Dict, Optional
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from src.data.models.webhook import WebhookSubscription
from src.data.repositories.webhook_repository import WebhookRepository


class WebhookService:
    """Сервис для отправки вебхуков"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.webhook_repo = WebhookRepository(session)
        self.http_client = httpx.AsyncClient(timeout=10.0)

    async def send_event(
        self, event_type: str, payload: Dict[str, Any], async_mode: bool
    ) -> None:
        """Отправляет событие всем подписчикам"""
        subscriptions = await self.webhook_repo.get_active_subscriptions_for_event(
            event_type
        )

        if not subscriptions:
            return

        webhook_payload = {
            "event": event_type,
            "data": payload,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        for subscription in subscriptions:
            if async_mode:
                asyncio.create_task(
                    self._send_to_subscriber(subscription, webhook_payload)
                )
            else:
                await self._send_to_subscriber(subscription, webhook_payload)

    async def _send_to_subscriber(
        self, subscription: WebhookSubscription, payload: Dict[str, Any]
    ) -> None:
        """Отправляет событие подписчику"""
        delivery = await self.webhook_repo.create_delivery(
            {
                "subscription_id": subscription.id,
                "event_type": payload["event"],
                "payload": payload,
                "status": "pending",
                "attempts": 0,
            }
        )
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

        except Exception as e:
            await self._save_delivery_result(
                delivery_id=delivery.id, status="failed", error_message=str(e)
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
