from fastapi import FastAPI
from contextlib import asynccontextmanager
from src.core.redis_client import redis_manager


@asynccontextmanager
async def lifespan(_fastapi_app: FastAPI):
    await redis_manager.connect()
    yield
    await redis_manager.disconnect()

app = FastAPI(lifespan=lifespan)

@app.get("/")
async def root():
    return {"message": "Hello World"}