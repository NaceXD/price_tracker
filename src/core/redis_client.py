import redis.asyncio as aioredis
from src.core.config import settings
from src.core.logger import logger


class RedisClient:
    def __init__(self):
        self.client: aioredis.Redis | None = None

    async def connect(self):
        self.client = aioredis.from_url(
            f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}",
            decode_responses=True,
        )
        logger.info("Успешное подключение к Redis")

    async def disconnect(self):
        if self.client:
            await self.client.aclose()
            logger.info("Соединение с Redis закрыто")

    async def set_cache(self, key: str, value: str, expire: int = 1800):
        if self.client:
            await self.client.set(name=key, value=value, ex=expire)

    async def get_cache(self, key: str) -> str | None:
        if self.client:
            return await self.client.get(key)
        return None

    async def incr(self, key: str, expire: int = 60) -> int:
        if self.client:
            async with self.client.pipeline(transaction=True) as pipe:
                pipe.incr(key)
                pipe.expire(key, expire, nx=True)
                result = await pipe.execute()
            return result[0]
        return 0

    async def delete_key(self, key: str) -> None:
        if self.client:
            await self.client.delete(key)

redis_manager = RedisClient()
