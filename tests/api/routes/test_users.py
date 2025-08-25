import pytest


@pytest.mark.asyncio
async def test_create_user_success(client):
    payload = {"email": "harry@example.com", "name": "Harry"}

    res = await client.post("/users", json=payload)
    assert res.status_code == 201
    body = res.json()
    assert body["email"] == "harry@example.com"
    assert body["name"] == "Harry"
    assert "id" in body and body["id"] > 0
    assert "created_at" in body


@pytest.mark.asyncio
async def test_create_user_duplicate_email_returns_conflict(client):
    payload = {"email": "harry@example.com", "name": "Harry"}

    res = await client.post("/users", json=payload)
    assert res.status_code == 201
    res = await client.post("/users", json=payload)
    assert res.status_code == 409


@pytest.mark.asyncio
async def test_get_user_successfully(client):
    payload = {"email": "harry@example.com", "name": "Harry"}
    res = await client.post("/users", json=payload)
    assert res.status_code == 201
    created_user = res.json()
    user_id = created_user["id"]
    res = await client.get(f"/users/{user_id}")
    assert res.status_code == 200
    body = res.json()
    assert body["email"] == "harry@example.com"
    assert body["name"] == "Harry"
    assert "id" in body and body["id"] > 0
    assert "created_at" in body


@pytest.mark.asyncio
async def test_update_user_name_successfully(client):
    payload = {"email": "harry@example.com", "name": "Harry"}
    res = await client.post("/users", json=payload)
    payload = {"name": "New Harry"}
    assert res.status_code == 201
    created_user = res.json()
    user_id = created_user["id"]
    res = await client.patch(f"/users/{user_id}", json=payload)
    assert res.status_code == 200
    body = res.json()
    assert body["name"] == "New Harry"
