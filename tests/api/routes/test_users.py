import pytest


@pytest.mark.asyncio
async def test_create_user(client):
    email = "harry@example.com"
    payload = {"email": email, "name": "Harry"}

    res = await client.post("/users", json=payload)
    assert res.status_code == 201
