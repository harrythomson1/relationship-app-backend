import pytest


@pytest.mark.asyncio
async def test_create_user(client):
    payload = {"email": "harry@example.com", "name": "Harry"}

    res = await client.post("/users", json=payload)
    assert res.status_code == 201
    body = res.json()
    assert body["email"] == "harry@example.com"
    assert body["name"] == "Harry"
    assert "id" in body and body["id"] > 0
    assert "created_at" in body


@pytest.mark.asyncio
async def test_create_user_catches_duplicates(client):
    payload = {"email": "harry@example.com", "name": "Harry"}

    res = await client.post("/users", json=payload)
    assert res.status_code == 201
    res = await client.post("/users", json=payload)
    assert res.status_code == 409
