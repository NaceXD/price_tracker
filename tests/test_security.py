import pytest

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
