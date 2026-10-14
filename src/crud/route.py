from typing import Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models import TrackedRoute, User, PriceHistory
from src.schemas.route import RouteCreate
from src.core.logger import logger


async def join_or_create_router(db: AsyncSession, route_schema: RouteCreate, current_user: User) -> TrackedRoute:
    query = select(TrackedRoute).where(
        TrackedRoute.origin == route_schema.origin,
        TrackedRoute.destination == route_schema.destination,
        TrackedRoute.departure_date == route_schema.departure_date
    ).options(selectinload(TrackedRoute.users))
    execute_route = await db.execute(query)
    route = execute_route.scalar_one_or_none()
    if route:
        if current_user not in route.users:
            logger.info(f"Маршрут найден. Добавляем пользователя {current_user.id} в список")
            route.users.append(current_user)
        else:
            logger.info(f"Пользователь {current_user.id} уже отслеживает этот маршрут")
    else:
        logger.info("Маршрут не найден в БД. Создаем новый объект")
        route = TrackedRoute(
            origin=route_schema.origin,
            destination=route_schema.destination,
            departure_date=route_schema.departure_date,
        )
        route.users.append(current_user)
        db.add(route)
    await db.commit()
    await db.refresh(route)
    logger.info(f"Маршрут с ID {route.id} успешно сохранен/обновлен в БД")
    return route


async def get_route_price_history(db: AsyncSession, route_id: int) -> Sequence[PriceHistory]:
    query = select(PriceHistory).where(PriceHistory.route_id == route_id).order_by(PriceHistory.checked_at.asc())
    result = await db.execute(query)

    return result.scalars().all()
