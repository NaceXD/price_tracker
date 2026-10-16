import pytest

@pytest.mark.asyncio(loop_scope="session")
async def test_register_user_success(client, db_cleaner, redis_cleaner):
    """Тест 1: Тестируем регистрацию по эндпоинту post /auth/register"""
    await db_cleaner()
    await redis_cleaner()

    payload = {"email": "valid_user@example.com", "password": "test123"}

    response = await client.post("/auth/register", json=payload)

    assert response.status_code == 201

    data = response.json()

    assert data['email'] == "valid_user@example.com"

    assert "id" in data

@pytest.mark.asyncio(loop_scope="session")
async def test_login_user_success(client, db_cleaner, redis_cleaner):
    """Тест 2: Тестируем авторизацию и получение редис ключа по эндпоинту post /auth/login"""
    await db_cleaner()
    await redis_cleaner()

    payload = {"email": "valid_user@example.com", "password": "validpass123"}
    response = await client.post("/auth/register", json=payload)

    assert response.status_code == 201

    login_payload = {"username": "valid_user@example.com", "password": "validpass123"}
    response = await client.post("/auth/login", data=login_payload)

    assert response.status_code == 200

    token_data = response.json()

    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"

@pytest.mark.asyncio(loop_scope="session")
async def test_get_current_user_success(client, db_cleaner, redis_cleaner):
    """Тест 3: Тестируем эндпоинт get /users/me"""
    await db_cleaner()
    await redis_cleaner()

    payload = {"email": "test_user@example.com", "password": "test123"}

    response = await client.post("/auth/register", json=payload)
    assert response.status_code == 201

    login_payload = {"username": "test_user@example.com", "password": "test123"}
    response = await client.post("/auth/login", data=login_payload)
    assert response.status_code == 200

    token = response.json()["access_token"]

    headers = {"Authorization": f"Bearer {token}"}
    me_response = await client.get("/auth/users/me", headers=headers)

    assert me_response.status_code == 200

    me_data = me_response.json()

    assert me_data["email"] == "test_user@example.com"