import pytest
from src.core.config import settings
@pytest.mark.asyncio(loop_scope="session")
async def test_login_brute_force_block(client, db_cleaner, redis_cleaner):
    """Тест 1: Тестируем брудфорс защиту"""
    await db_cleaner()
    await redis_cleaner()

    payload = {"username": "invalid_user@example.com", "password": "test123"}

    for _ in range(5):
        response = await client.post("/auth/login", data=payload)
        assert response.status_code == 401

    response = await client.post("/auth/login", data=payload)
    assert response.status_code == 423

@pytest.mark.asyncio(loop_scope="session")
async def test_api_rate_limiter_block(client, db_cleaner, redis_cleaner):
    """Тест 2: Тестируем Ratelimit"""
    await db_cleaner()
    await redis_cleaner()

    headers = {"X-Forwarded-For": "192.168.77.77"}

    for i in range(10):
        payload = {"username": f"fake_{i}@test.com", "password": "test123"}
        response = await client.post("/auth/login", data=payload, headers=headers)
        assert response.status_code == 401

    payload = {"username": "test_user@test.com", "password": "test123"}
    response = await client.post("/auth/login", data=payload, headers=headers)

    assert response.status_code == 429
@pytest.mark.asyncio(loop_scope="session")
async def test_swagger_docs_unauthorized(client):
    """Попытка входа в документацию без Basic Auth заголовков должна возвращать 401."""
    response = await client.get("/docs")
    assert response.status_code == 401
    assert "WWW-Authenticate" in response.headers


@pytest.mark.asyncio(loop_scope="session")
async def test_swagger_docs_bad_credentials(client):
    """Попытка входа с неверными учетными данными Basic Auth."""
    # Используем встроенный в httpx механизм передачи basic auth для тестов
    response = await client.get("/docs", auth=("wrong_user", "wrong_pass"))
    assert response.status_code == 401


@pytest.mark.asyncio(loop_scope="session")
async def test_swagger_docs_success(client):
    """Успешный доступ к Swagger UI при передаче валидных кредов из конфигурации."""
    response = await client.get("/docs", auth=(settings.DOCS_USERNAME, settings.DOCS_PASSWORD))
    assert response.status_code == 200
    assert "Price Tracker API Docs" in response.text


@pytest.mark.asyncio(loop_scope="session")
async def test_openapi_json_security(client):
    """Проверка, что схема openapi.json защищена аналогичным образом."""
    # Без авторизации
    res_anon = await client.get("/openapi.json")
    assert res_anon.status_code == 401

    # С правильной авторизацией
    res_auth = await client.get("/openapi.json", auth=(settings.DOCS_USERNAME, settings.DOCS_PASSWORD))
    assert res_auth.status_code == 200
    assert "paths" in res_auth.json()