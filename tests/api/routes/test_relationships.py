from uuid import uuid4

import pytest
from httpx import AsyncClient


async def _create_user(client: AsyncClient, *, name: str = "Test User") -> int:
    email = f"test+{uuid4().hex[:8]}@example.com"
    res = await client.post("/users", json={"email": email, "name": name})
    assert res.status_code == 201, res.text
    body = res.json()
    return body["id"]


async def dev_login(client: AsyncClient, email: str | None = None):
    # Dev login now expects an email body and returns { user: {...}, token: "..." }
    if email is None:
        email = f"test+{uuid4().hex[:8]}@example.com"
    res = await client.post("/auth/dev-login", json={"email": email})
    assert res.status_code == 200, res.text
    body = res.json()
    return body["token"], body["user"]["id"]


@pytest.mark.asyncio
class TestRelationshipsCreate:
    async def test_create_relationship_success(self, client: AsyncClient):
        # Create two users to relate
        u1 = await _create_user(client)
        u2 = await _create_user(client)

        payload = {
            "type": "romantic",
            "status": "pending",
            "role": "partner",
            "user_ids": [u1, u2],
        }

        res = await client.post("/relationships", json=payload)
        assert res.status_code == 201, res.text
        body = res.json()
        assert body["id"] > 0
        assert body["type"] == "romantic"
        assert body["status"] == "pending"
        assert "created_at" in body
        assert "updated_at" in body


@pytest.mark.asyncio
class TestRelationshipsGet:
    async def test_get_relationship_success(self, client: AsyncClient):
        # First, create a relationship we can fetch
        u1 = await _create_user(client)
        u2 = await _create_user(client)
        create_payload = {
            "type": "romantic",
            "status": "pending",
            "role": "partner",
            "user_ids": [u1, u2],
        }
        create_res = await client.post("/relationships", json=create_payload)
        assert create_res.status_code == 201, create_res.text
        rel_id = create_res.json()["id"]

        # Now retrieve it
        get_res = await client.get(f"/relationships/{rel_id}")
        assert get_res.status_code == 200, get_res.text
        body = get_res.json()
        assert body["id"] == rel_id
        assert body["type"] == "romantic"
        assert body["status"] == "pending"

    async def test_get_relationship_404(self, client: AsyncClient):
        res = await client.get("/relationships/999999")
        assert res.status_code == 404
        body = res.json()
        assert "detail" in body


@pytest.mark.asyncio
class TestRelationshipsUpdate:
    async def test_update_relationship_success(self, client: AsyncClient):
        token, me_id = await dev_login(client)

        # Create a second user
        u2 = await _create_user(client)

        # Create a relationship including the authenticated user
        payload = {
            "type": "romantic",
            "status": "pending",
            "role": "partner",
            "user_ids": [me_id, u2],
        }
        create_res = await client.post("/relationships", json=payload)
        assert create_res.status_code == 201, create_res.text
        body = create_res.json()
        rel_id = body["id"]

        # Update the relationship
        patch_payload = {"status": "active", "type": "friendship"}
        headers = {"Authorization": f"Bearer {token}"}
        patch_res = await client.patch("/relationships", json=patch_payload, headers=headers)
        assert patch_res.status_code == 200, patch_res.text
        updated = patch_res.json()
        assert updated["id"] == rel_id
        assert updated["type"] == "friendship"
        assert updated["status"] == "active"

    async def test_update_relationship_404(self, client: AsyncClient):
        token, _ = await dev_login(client)
        patch_payload = {"status": "active", "type": "friendship"}
        headers = {"Authorization": f"Bearer {token}"}
        res = await client.patch("/relationships", json=patch_payload, headers=headers)
        assert res.status_code == 404
