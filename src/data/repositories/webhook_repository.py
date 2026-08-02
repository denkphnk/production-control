from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select


from sqlalchemy.orm import selectinload

from src.data.models.webhook import WebhookSubscription, WebhookDelivery
from src.data.repositories.base_repository import BaseRepository


class WebhookRepository(BaseRepository[WebhookSubscription]):
    """Репозиторий вебхука"""

    def __init__(self, session: AsyncSession):
        super().__init__(WebhookSubscription, session)

    ##########################################
    # ПОИСК ПО URL
    ##########################################
    async def get_by_url(self, url: str) -> Optional[WebhookSubscription]:
        """Ищет подписку по URL"""
        query = select(self.model).where(self.model.url == url)

        res = await self.session.execute(query)
        return res.scalar_one_or_none()

    ##########################################
    # СОЗДАНИЕ DELIVERY
    ##########################################
    async def create_delivery(self, data: Dict[str, Any]) -> WebhookDelivery:
        """Создает запись в таблице webhook_deliveries о попытке отправки"""
        delivery = WebhookDelivery(**data)
        self.session.add(delivery)
        await self.session.flush()
        return delivery

    ##########################################
    # ПОИСК FAILED DELIVERY
    ##########################################
    async def get_failed_deliveries(self, limit: int = 20) -> List[WebhookDelivery]:
        """Находит доставки со статусом failed, которые можно попробовать отправить снова"""
        query = (
            select(WebhookDelivery)
            .join(
                WebhookSubscription,
                WebhookDelivery.subscription_id == WebhookSubscription.id,
            )
            .where(
                WebhookDelivery.status == "failed",
                WebhookDelivery.attempts < WebhookSubscription.retry_count,
            )
        )

        res = await self.session.execute(query)
        return res.scalars().all()

    ##########################################
    # ПОИСК АКТИВНЫХ ПОДПИСОК
    ##########################################
    async def get_active_subscriptions_for_event(
        self, event_type: str
    ) -> List[WebhookSubscription]:
        """Находит все активные подписки, которые подписаны на конкретное событие"""
        query = select(self.model).where(
            self.model.is_active, self.model.events.any(event_type)
        )

        res = await self.session.execute(query)
        return res.scalars().all()

    ##########################################
    # ИСТОРИЯ ДОСТАВОК ДЛЯ КОНКРЕТНОЙ ПОДПИСКИ
    ##########################################
    async def get_deliveries_for_subscription(
        self, subscription_id: int, offset: int = 0, limit: int = 20
    ) -> Tuple[List[WebhookDelivery], int]:
        """Возвращает историю доставок для конкретной подписки с пагинацией"""
        query = (
            select(WebhookDelivery)
            .where(WebhookDelivery.subscription_id == subscription_id)
            .order_by(WebhookDelivery.created_at.desc())
        )
        total_query = (
            select(func.count())
            .select_from(WebhookDelivery)
            .where(WebhookDelivery.subscription_id == subscription_id)
        )

        query = query.offset(offset).limit(limit)
        res = await self.session.execute(query)
        res_total = await self.session.execute(total_query)

        return res.scalars().all(), res_total.scalar()

    ##########################################
    # ЧТЕНИЕ ПОДПИСКИ СО ВСЕМИ ДОСТАВКАМИ
    ##########################################
    async def get_with_deliveries(
        self, subscription_id: int
    ) -> Optional[WebhookSubscription]:
        """Получает подписку и сразу подгружает всю историю ее доставок"""
        query = (
            select(self.model)
            .where(self.model.id == subscription_id)
            .options(
                selectinload(self.model.webhook_deliveries).order_by(
                    WebhookDelivery.created_at.desc()
                )
            )
        )

        res = await self.session.execute(query)
        return res.unique().scalar_one_or_none()

    ##########################################
    # СПИСОК ДОСТАВОК
    ##########################################
    async def get_all_with_count(
        self, offset: int = 0, limit: int = 20
    ) -> Tuple[List[WebhookSubscription], int]:
        """Отдает список всех подписок с подсчетом"""
        query = select(self.model).offset(offset).limit(limit)
        total_query = select(func.count()).select_from(self.model)

        res = await self.session.execute(query)
        total = await self.session.execute(total_query)

        return res.scalars().all(), total.scalar()