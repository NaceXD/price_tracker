import asyncio
import httpx
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
        query = select(TrackedRoute).where(TrackedRoute.id == route_id)
        result = await session.execute(query)
        route = result.scalar_one_or_none()

        if route is None:
            await local_engine.dispose()
            return

        date_str = route.departure_date.strftime("%Y-%m-%d")

        url = "https://api.travelpayouts.com/aviasales/v3/prices_for_dates"

        params = {
            "origin": route.origin,
            "destination": route.destination,
            "departure_at": date_str,
            "unique": "false",
            "token": settings.TRAVELPAYOUTS_TOKEN,
            "currency": "rub"
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, timeout=10.0)
                response.raise_for_status()
                data = response.json()

                prices_list = data.get("data", [])

                if prices_list:
                    first_ticket = prices_list[0]
                    actual_price = first_ticket.get("price")

                    logger.info(
                        f"Реальный парсер v3 нашел цену для {route.origin}-{route.destination}: {actual_price} руб.")

                    history = PriceHistory(
                        route_id=route.id,
                        price=actual_price
                    )
                    session.add(history)
                    await session.commit()
                else:
                    logger.warning(
                        f"Цен для маршрута {route.origin}-{route.destination} на дату {date_str} в кэше API нет")

        except httpx.HTTPError as http_err:
            logger.error(f"Сетевая ошибка при запросе к Aviasales: {http_err}")
        except Exception as e:
            logger.error(f"Ошибка парсинга или работы с БД: {e}")

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
