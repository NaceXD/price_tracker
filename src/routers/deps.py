from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.redis_client import redis_manager
from src.core.logger import logger
from src.crud.user import get_user_by_id
from src.models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


async def get_current_user(
        token: str = Depends(oauth2_scheme),
        db: AsyncSession = Depends(get_db)
) -> User:
    user_id_str = await redis_manager.get_cache(key=token)

    if user_id_str is None:
        logger.warning("Попытка доступа с недействительным или просроченным токеном")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Недействительный или просроченный токен сессии"
        )

    user = await get_user_by_id(db, int(user_id_str))
    if user is None:
        logger.error(f"Критическая ошибка: Сессия существует для несуществующего юзера с ID {user_id_str}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь не найден"
        )

    return user
