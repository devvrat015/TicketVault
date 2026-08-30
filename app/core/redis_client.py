import redis
import redis.asyncio as aioredis
import json

from app.core.config import settings


# Sync Redis client
redis_client = redis.from_url(
    settings.REDIS_URL,
    decode_responses=True,
)


# Async Redis client
async_redis_client = aioredis.from_url(
    settings.REDIS_URL,
    decode_responses=True,
)


async def publish_event(channel: str, message: dict):
    await async_redis_client.publish(
        channel,
        json.dumps(message),
    )