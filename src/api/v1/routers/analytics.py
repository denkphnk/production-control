import json

from fastapi import APIRouter, HTTPException, status

from src.core.cache import redis

analytics_router = APIRouter(prefix='/api/v1/analytics', tags=['analytics'])

@analytics_router.get("/dashboard")
async def get_analytics_dashboard():
    cached = await redis.get("dashboard_stats")

    if not cached:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail='Dashboard statistics not available'
        )

    return json.loads(cached)