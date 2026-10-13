import secrets

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.schemas.user import UserCreate, UserResponse, TokenResponse
from src.crud.user import create_user, get_user_by_email, authenticate_user
from src.core.database import get_db
from src.core.logger import logger
from src.core.redis_client import redis_manager

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    logger.info(f"Попытка регистрации пользователя с email: {user.email}")
    existing_user = await get_user_by_email(db, email=user.email)
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Пользователь с таким email зарегистрирован")

    new_user = await create_user(db, user)
    return new_user


@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def log_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    logger.info(f"Попытка авторизации пользователя с email: {user.email}")
    db_user = await authenticate_user(db, user)
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверный email или пароль")
    logger.info("Генерируем случайный токен")
    token = secrets.token_hex(32)
    await redis_manager.set_cache(key=token, value=str(db_user.id), expire=7200)
    return {"access_token": token, "token_type": "bearer"}
