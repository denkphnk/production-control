import json

from fastapi import APIRouter, Depends
from redis.asyncio import Redis

from src.api.v1.dependencies import get_analytics_service
from src.api.v1.schemas.batch import CompareBatchesRequest, CompareBatchesResponse
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


@analytics_router.post("/compare_batches", response_model=CompareBatchesResponse)
async def compare_batches(
    data: CompareBatchesRequest,
    service: AnalyticsService = Depends(get_analytics_service),
):
    return await service.compare_batches(data.batch_ids)
