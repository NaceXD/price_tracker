import secrets
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from contextlib import asynccontextmanager

from src.core.redis_client import redis_manager
from src.core.logger import logger
from src.core.config import settings
from src.routers.auth import router as auth_router
from src.routers.route import router as route_router


@asynccontextmanager
async def lifespan(_fastapi_app: FastAPI):
    logger.info("Запуск веб-приложения, подключаемся к ресурсам...")
    await redis_manager.connect()
    yield
    logger.info("Остановка веб-приложения, закрываем соединения...")
    await redis_manager.disconnect()


app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)

app.include_router(auth_router)
app.include_router(route_router)


security = HTTPBasic()


def authenticate_docs(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, settings.DOCS_USERNAME)
    correct_password = secrets.compare_digest(credentials.password, settings.DOCS_PASSWORD)

    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный логин или пароль от документации",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username



@app.get("/docs", include_in_schema=False)
async def get_documentation(_username: str = Depends(authenticate_docs)):
    return get_swagger_ui_html(openapi_url="/openapi.json", title="Price Tracker API Docs")



@app.get("/openapi.json", include_in_schema=False)
async def get_open_api_endpoint(_username: str = Depends(authenticate_docs)):
    return get_openapi(title="Price Tracker API", version="1.0.0", routes=app.routes)


@app.get("/")
async def root():
    return {"status": "working", "project": "Price Tracker API"}
