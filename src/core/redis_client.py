import redis.asyncio as aioredis
from src.core.config import settings


class RedisClient:
    def __init__(self):
        self.client: aioredis.Redis | None = None

    async def connect(self):
        self.client = aioredis.from_url(
            f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}",
            decode_responses=True,
        )

    async def disconnect(self):
        if self.client:
            await self.client.close()

    async def set_cache(self, key: str, value: str, expire: int = 1800):
        if self.client:
            await self.client.set(name=key, value=value, ex=expire)

    async def get_cache(self, key: str) -> str | None:
        if self.client:
            return await self.client.get(key)
        return None

redis_manager = RedisClient()