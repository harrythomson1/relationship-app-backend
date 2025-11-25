import pytest
from httpx import AsyncClient

from tests.api.test_utils import _create_authed_relationship, _create_relationship, _create_user


@pytest.mark.asyncio
class TestRelationshipsCreate:
    async def test_create_relationship_success(self, client: AsyncClient):
        res = await _create_authed_relationship(client)
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
        res = await _create_authed_relationship(client)
        assert res.status_code == 201, res.text
        rel_id = res.json()["id"]

        get_res = await client.get(f"/relationships/{rel_id}")
        assert get_res.status_code == 200, get_res.text
        body = get_res.json()
        assert body["id"] == rel_id
        assert body["type"] == "romantic"
        assert body["status"] == "pending"

    async def test_get_relationship_404(self, client: AsyncClient):
        await _create_authed_relationship(client)
        res = await client.get("/relationships/999999")
        assert res.status_code == 404
        body = res.json()
        assert "detail" in body

    async def test_unauthorized_user(self, client: AsyncClient):
        await _create_authed_relationship(client)
        rel_2 = await _create_relationship(client)
        rel_2_id = rel_2.json()["id"]
        get_res = await client.get(f"/relationships/{rel_2_id}")
        assert get_res.status_code == 401


@pytest.mark.asyncio
class TestRelationshipsUpdate:
    async def test_update_relationship_success(self, client: AsyncClient):
        result = await _create_authed_relationship(client)
        assert result.status_code == 201, result.text
        body = result.json()
        rel_id = body["id"]

        patch_payload = {"status": "active", "type": "friendship"}
        patch_res = await client.patch("/relationships", json=patch_payload)
        assert patch_res.status_code == 200, patch_res.text
        updated = patch_res.json()
        assert updated["id"] == rel_id
        assert updated["type"] == "friendship"
        assert updated["status"] == "active"

    async def test_update_relationship_404(self, client: AsyncClient):
        user = await _create_user(client)
        from tests.api.test_utils import _set_claims

        _set_claims(
            {
                "sub": str(user["supabase_user_id"]),
                "email": user["email"],
                "aud": "authenticated",
                "iss": "https://fakereference.supabase.co/auth/v1",
            }
        )
        patch_payload = {"status": "active", "type": "friendship"}
        res = await client.patch("/relationships", json=patch_payload)
        assert res.status_code == 404, res.text
        body = res.json()
        assert body["detail"].get("message") == "Relationship member not found"


@pytest.mark.asyncio
class TestRelationshipsDelete:
    async def test_delete_relationship_success(self, client: AsyncClient):
        result = await _create_authed_relationship(client)
        assert result.status_code == 201, result.text
        body = result.json()
        relationship_id = body["id"]
        deleted_relationship = await client.delete("/relationships")
        assert deleted_relationship.status_code == 204, (
            deleted_relationship.text or deleted_relationship.content
        )

        relationship = await client.get(f"/relationships/{relationship_id}")
        assert relationship.status_code == 404, relationship.text

    async def test_delete_relationship_when_headers_not_passed_in_delete(self, client: AsyncClient):
        res = await _create_authed_relationship(client)
        from app.api.auth.utils import get_current_claims
        from app.api.main import app

        prev = app.dependency_overrides.get(get_current_claims)
        app.dependency_overrides.pop(get_current_claims, None)

        deleted_relationship = await client.delete("/relationships")
        assert deleted_relationship.status_code == 401
        assert deleted_relationship.json()["detail"] == "Not authenticated"

        if prev is not None:
            app.dependency_overrides[get_current_claims] = prev

        rel_id = res.json()["id"]
        relationship = await client.get(f"/relationships/{rel_id}")
        assert relationship.status_code == 200, relationship.text

    async def test_delete_relationship_not_found(self, client: AsyncClient):
        from tests.api.test_utils import _set_claims

        user = await _create_user(client)
        _set_claims(
            {
                "sub": str(user["supabase_user_id"]),
                "email": user["email"],
                "aud": "authenticated",
                "iss": "https://fakereference.supabase.co/auth/v1",
            }
        )
        result = await client.delete("/relationships")
        assert result.status_code == 404, result.text
        assert result.json()["detail"]["message"] == "Relationship member not found"
