from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import User
from src.core.database import get_db
from src.schemas.route import RouteCreate, RouteResponse, PriceHistoryResponse
from src.crud.route import join_or_create_router, get_route_price_history
from src.routers.deps import get_current_user
from src.core.logger import logger
from src.tasks.tasks import fetch_route_price

router = APIRouter(prefix="/routes", tags=["Routes"])


@router.post("/track", response_model=RouteResponse, status_code=status.HTTP_201_CREATED)
async def track_new_route(
        route_data: RouteCreate,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    logger.info("Создаем новый маршрут")
    new_route = await join_or_create_router(db, route_data, current_user)
    fetch_route_price.delay(new_route.id)
    return new_route

@router.get("/{route_id}/prices", response_model=list[PriceHistoryResponse], status_code=status.HTTP_200_OK)
async def get_history(
        route_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    logger.info(f"Пользователь {current_user.id} затребовал историю цен для маршрута {route_id}")
    history = await get_route_price_history(db, route_id)
    return history