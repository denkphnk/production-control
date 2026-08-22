from fastapi import Depends
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.cache import get_redis
from src.core.database import AsyncSessionLocal
from src.domain.services.analytics_service import AnalyticsService
from src.domain.services.batch_service import BatchService
from src.domain.services.product_service import ProductService
from src.domain.services.report_service import ReportService
from src.domain.services.webhook_service import WebhookService
from src.domain.services.workcenter_service import WorkCenterService


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


async def get_batch_service(
    session: AsyncSession = Depends(get_db), redis: Redis = Depends(get_redis)
) -> BatchService:
    return BatchService(session=session, redis=redis)


async def get_product_service(
    session: AsyncSession = Depends(get_db),
) -> ProductService:
    return ProductService(session)


async def get_workcenter_service(
    session: AsyncSession = Depends(get_db),
) -> WorkCenterService:
    return WorkCenterService(session)


async def get_webhook_service(
    session: AsyncSession = Depends(get_db),
) -> WebhookService:
    return WebhookService(session)


async def get_report_service(
    session: AsyncSession = Depends(get_db),
) -> ReportService:
    return ReportService(session)


async def get_analytics_service(
    session: AsyncSession = Depends(get_db),
) -> AnalyticsService:
    return AnalyticsService(session)
