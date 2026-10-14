import asyncio
import random
from typing import Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from src.core.celery_app import celery_instance
from src.core.config import settings
from src.models import PriceHistory, TrackedRoute
from src.core.logger import logger


async def check_route_price(route_id: int):
    local_engine = create_async_engine(settings.database_url, echo=True)
    local_session = async_sessionmaker(bind=local_engine, expire_on_commit=False, class_=AsyncSession)
    async with local_session() as session:
        fake_price = random.randint(3000, 15000)
        logger.info(f"Парсер нашел цену для маршрута {route_id}: {fake_price} руб.")
        new_price = PriceHistory(route_id=route_id, price=fake_price)
        session.add(new_price)
        await session.commit()
    await local_engine.dispose()


async def get_all_routes_from_db() -> Sequence[int]:
    local_engine = create_async_engine(settings.database_url, echo=True)
    local_session = async_sessionmaker(bind=local_engine, expire_on_commit=False, class_=AsyncSession)

    async with local_session() as session:
        query = select(TrackedRoute.id)
        result = await session.execute(query)
        list_id = result.scalars().all()

    await local_engine.dispose()
    return list_id


@celery_instance.task(name="tasks.fetch_route_price")
def fetch_route_price(route_id: int):
    asyncio.run(check_route_price(route_id))


@celery_instance.task(name="tasks.fetch_all_routes_prices")
def fetch_all_routes_prices():
    logger.info("Celery Beat запустил периодической опрос всех маршрутов")
    route_ids = asyncio.run(get_all_routes_from_db())
    for route_id in route_ids:
        fetch_route_price.delay(route_id)
