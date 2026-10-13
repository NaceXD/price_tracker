from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.schemas.user import UserCreate, UserResponse
from src.crud.user import create_user, get_user_by_email
from src.core.database import get_db
from src.core.logger import logger

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
