from redis.asyncio import Redis
from config import settings

redis = Redis(
    host=settings.REDIS_URL,
    port=6379,
    decode_responses=True,
)
