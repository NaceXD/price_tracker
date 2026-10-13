import hashlib
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.models import User, Profile
from src.schemas.user import UserCreate
from src.core.logger import logger


async def create_user(db: AsyncSession, user_schema: UserCreate) -> User:
    logger.info("Хэшируем пароль")
    hashed_password = hashlib.sha256(user_schema.password.encode()).hexdigest()
    logger.info("Пароль успешно за хэшировался")
    logger.info("Создаем нового пользователя")
    new_user = User(email=user_schema.email, hashed_password=hashed_password)
    db.add(new_user)
    logger.info("Генерируем первичный ключ пользователя")
    await db.flush()
    logger.info("Создаем связанный профиль для пользователя")
    new_profile = Profile(user_id=new_user.id, send_email=True)
    db.add(new_profile)
    logger.info("Сохраняем в бд")
    await db.commit()
    await db.refresh(new_user)
    return new_user


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    query = select(User).where(User.email == email)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    return user
