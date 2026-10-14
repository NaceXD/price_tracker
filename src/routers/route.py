from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import User
from src.core.database import get_db
from src.schemas.route import RouteCreate, RouteResponse
from src.crud.route import join_or_create_router
from src.routers.deps import get_current_user
from src.core.logger import logger

router = APIRouter(prefix="/routes", tags=["Routes"])


@router.post("/track", response_model=RouteResponse, status_code=status.HTTP_201_CREATED)
async def track_new_route(
        route_data: RouteCreate,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    logger.info("Создаем новый маршрут")
    new_route = await join_or_create_router(db, route_data, current_user)
    return new_route
