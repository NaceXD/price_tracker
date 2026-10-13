from fastapi import FastAPI, Depends
from contextlib import asynccontextmanager
from src.core.redis_client import redis_manager
from src.core.logger import logger
from src.routers.auth import router as auth_router
from src.routers.deps import get_current_user
from src.models import User
from src.schemas.user import UserResponse


@asynccontextmanager
async def lifespan(_fastapi_app: FastAPI):
    logger.info("Запуск веб-приложениея, подключаемся к ресурсам...")
    await redis_manager.connect()
    yield
    logger.info("Остановка веб-приложения, закрываем соединения ...")
    await redis_manager.disconnect()


app = FastAPI(lifespan=lifespan)
app.include_router(auth_router)


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/redis-test")
async def redis_test():
    logger.info("Получаем запрос на эндпоинт /redis-test")
    key_name = "my_test"
    test_key = "Redis работает"
    logger.info(f"Записываем в Redis ключ '{key_name}'")
    await redis_manager.set_cache(key=key_name, value=test_key)
    logger.info(f"Читаем из Redis кл '{key_name}'")
    result = await redis_manager.get_cache(key=key_name)
    return {"status": "ok", "value": result}

@app.get("/users/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user