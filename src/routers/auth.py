import secrets
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.schemas.user import UserCreate, UserResponse, TokenResponse
from src.crud.user import create_user, get_user_by_email, authenticate_user
from src.core.database import get_db
from src.core.logger import logger
from src.core.redis_client import redis_manager
from src.routers.deps import get_current_user
from src.models import User
from src.routers.deps import ip_rate_limiter

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


@router.post("/login", response_model=TokenResponse)
async def log_user(
        form_data: OAuth2PasswordRequestForm = Depends(),
        db: AsyncSession = Depends(get_db),
        _ip_limit: None = Depends(ip_rate_limiter)
):
    logger.info(f"OAuth2 авторизация для: {form_data.username}")
    account_lock_key = f"lock:account:{form_data.username}"
    attempts_key = f"attempts:account:{form_data.username}"
    valid = await redis_manager.get_cache(key=account_lock_key)
    if valid is not None:
        logger.warning(f"Аккаунт: {form_data.username} временно заморожен")
        raise HTTPException(status_code=status.HTTP_423_LOCKED, detail="Данный аккаунт временно заморожен")

    user_schema = UserCreate(email=form_data.username, password=form_data.password)

    db_user = await authenticate_user(db, user_schema)
    if not db_user:
        current_attempts = await redis_manager.incr(key=attempts_key, expire=300)
        if current_attempts >= 5:
            logger.warning(f"Превышен лимит попыток для аккаунта: {form_data.username}")
            await redis_manager.set_cache(key=account_lock_key, value="Превышен лимит ...", expire=900)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверный email или пароль")
    await redis_manager.delete_key(key=attempts_key)
    token = secrets.token_hex(32)
    await redis_manager.set_cache(key=token, value=str(db_user.id), expire=7200)

    return {"access_token": token, "token_type": "bearer"}


@router.get("/users/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user
