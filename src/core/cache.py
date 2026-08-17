from redis.asyncio import Redis
from src.core.config import settings

redis = Redis(
    host=settings.REDIS_URL,
    port=6379,
    decode_responses=True,
)
