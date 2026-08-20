from redis.asyncio import Redis
from src.core.config import settings

redis = Redis.from_url(
    url=str(settings.REDIS_URL),
    decode_responses=True
)
