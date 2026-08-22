import json

from fastapi import APIRouter, Depends
from redis.asyncio import Redis

from src.api.v1.dependencies import get_analytics_service
from src.core.cache import get_redis
from src.domain.services.analytics_service import AnalyticsService

analytics_router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])


@analytics_router.get("/dashboard")
async def get_analytics_dashboard(
    service: AnalyticsService = Depends(get_analytics_service),
    redis: Redis = Depends(get_redis),
):
    cached = await redis.get("dashboard_stats")

    if cached:
        return json.loads(cached)

    statistics = await service.get_dashboard_statistics()
    await redis.set("dashboard_stats", json.dumps(statistics, default=str), ex=300)

    return statistics
