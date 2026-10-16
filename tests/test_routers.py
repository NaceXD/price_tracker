import pytest
from datetime import datetime, timedelta
from sqlalchemy import select
from tests.conftest import TestSessionLocal
from src.models import TrackedRoute, User


@pytest.mark.asyncio(loop_scope="session")
async def test_track_new_route_success(client, db_cleaner, redis_cleaner):
    """Проверка успешного добавления нового маршрута авторизованным пользователем."""
    await db_cleaner()
    await redis_cleaner()

    # 1. Регистрация и авторизация
    user_payload = {"email": "route_user@example.com", "password": "password123"}
    await client.post("/auth/register", json=user_payload)
    login_res = await client.post("/auth/login",
                                  data={"username": user_payload["email"], "password": user_payload["password"]})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Создание маршрута
    departure_date = (datetime.now() + timedelta(days=10)).isoformat()
    route_payload = {
        "origin": "MOW",
        "destination": "LED",
        "departure_date": departure_date
    }

    response = await client.post("/routes/track", json=route_payload, headers=headers)
    assert response.status_code == 201

    data = response.json()
    assert data["origin"] == "MOW"
    assert data["destination"] == "LED"
    assert "id" in data


@pytest.mark.asyncio(loop_scope="session")
async def test_track_route_unauthorized(client, db_cleaner):
    """Попытка добавления маршрута без токена должна возвращать 401."""
    await db_cleaner()

    route_payload = {
        "origin": "MOW",
        "destination": "DXB",
        "departure_date": (datetime.now() + timedelta(days=5)).isoformat()
    }

    response = await client.post("/routes/track", json=route_payload)
    assert response.status_code == 401


@pytest.mark.asyncio(loop_scope="session")
async def test_multiple_users_same_route_logic(client, db_cleaner, redis_cleaner):
    """Проверка Many-to-Many: два пользователя трекают один рейс.
    В БД должен создаться ровно ОДИН маршрут, привязанный к обоим."""
    await db_cleaner()
    await redis_cleaner()

    departure_date = (datetime.now() + timedelta(days=20)).isoformat()
    route_payload = {
        "origin": "PAR",
        "destination": "LON",
        "departure_date": departure_date
    }

    # Регистрируем и авторизуем первого пользователя
    await client.post("/auth/register", json={"email": "first@test.com", "password": "password123"})
    login1 = await client.post("/auth/login", data={"username": "first@test.com", "password": "password123"})
    headers1 = {"Authorization": f"Bearer {login1.json()['access_token']}"}

    # Регистрируем и авторизуем второго пользователя
    await client.post("/auth/register", json={"email": "second@test.com", "password": "password123"})
    login2 = await client.post("/auth/login", data={"username": "second@test.com", "password": "password123"})
    headers2 = {"Authorization": f"Bearer {login2.json()['access_token']}"}

    # Оба шлют один и тот же маршрут
    res1 = await client.post("/routes/track", json=route_payload, headers=headers1)
    res2 = await client.post("/routes/track", json=route_payload, headers=headers2)

    assert res1.status_code == 201
    assert res2.status_code == 201

    # Идентификаторы маршрута в ответах должны быть идентичны
    assert res1.json()["id"] == res2.json()["id"]


@pytest.mark.asyncio(loop_scope="session")
async def test_get_route_price_history_empty(client, db_cleaner, redis_cleaner):
    """Получение пустой истории цен для только что созданного маршрута."""
    await db_cleaner()
    await redis_cleaner()

    await client.post("/auth/register", json={"email": "history@test.com", "password": "password123"})
    login = await client.post("/auth/login", data={"username": "history@test.com", "password": "password123"})
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    route_res = await client.post(
        "/routes/track",
        json={"origin": "MOW", "destination": "AER",
              "departure_date": (datetime.now() + timedelta(days=12)).isoformat()},
        headers=headers
    )
    route_id = route_res.json()["id"]

    history_res = await client.get(f"/routes/{route_id}/prices", headers=headers)
    assert history_res.status_code == 200
    assert isinstance(history_res.json(), list)
    assert len(history_res.json()) == 0
