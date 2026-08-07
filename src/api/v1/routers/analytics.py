import json

from fastapi import APIRouter

from src.core.cache import redis

analytics_router = APIRouter(prefix='/api/v1/analytics', tags=['analytics'])

@analytics_router.get("/dashboard")
async def get_analytics_dashboard():
    cached = await redis.get("dashboard_stats")

    if not cached:
        return {
            "message": "Statistics not available yet"
        }

    return json.loads(cached)