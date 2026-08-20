import json

from fastapi import APIRouter, HTTPException, status, Depends

from src.domain.services.analytics_service import AnalyticsService
from src.core.cache import redis
from src.api.v1.dependencies import get_analytics_service

analytics_router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])


@analytics_router.get("/dashboard")
async def get_analytics_dashboard(service: AnalyticsService = Depends(get_analytics_service)):
    cached = await redis.get("dashboard_stats")

    if cached:
        return json.loads(cached)
    
    statistics = await service.get_dashboard_statistics()
    await redis.set('dashboard_stats',
                json.dumps(statistics, default=str),
                ex=300)

    return statistics
