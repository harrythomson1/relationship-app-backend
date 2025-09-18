import pytest

from app.api.auth.utils import get_current_claims
from app.api.main import app


@pytest.fixture
def claims():
    return {
        "sub": "8012611b-e385-463e-b719-1a5b468a6ce5",
        "email": "harry@example.com",
        "aud": "authenticated",
        "iss": "https://fakereference.supabase.co/auth/v1",
    }


@pytest.fixture(autouse=True)
def override_claims(claims):
    # Make every test “authenticated” by default
    async def _override():
        return claims

    app.dependency_overrides[get_current_claims] = _override
    yield
    app.dependency_overrides.clear()


class TestUsersMe:
    @pytest.mark.asyncio
    async def test_me_returns_current_user(self, client):
        payload = {"name": "Harry"}
        res = await client.post("/users", json=payload)
        assert res.status_code == 201

        res = await client.get(
            "/users/me",
        )
        assert res.status_code == 200
        me = res.json()
        assert me["name"] == "Harry"
        assert me["email"] == "harry@example.com"
        assert me["supabase_user_id"] == "8012611b-e385-463e-b719-1a5b468a6ce5"
        assert "id" in me
        assert "created_at" in me

    @pytest.mark.asyncio
    async def test_me_requires_auth(self, client):
        # No Authorization header
        res = await client.get("/users/me")
        assert res.status_code == 401

        # Malformed/invalid token
        res = await client.get(
            "/users/me",
            headers={"Authorization": "Bearer not-a-real-token"},
        )
        assert res.status_code == 401


@pytest.mark.me
@pytest.mark.update
class TestUsersUpdate:
    @pytest.mark.asyncio
    async def test_update_user_name_successfully(self, client):
        # Dev-login to get a token and user
        email = "harry@example.com"
        login_res = await client.post("/auth/dev-login", json={"email": email})
        assert login_res.status_code == 200
        payload = login_res.json()
        token = payload["token"]
        user = payload["user"]

        # Patch /users/me with new name
        update_payload = {"name": "New Harry"}
        res = await client.patch(
            "/users/me",
            json=update_payload,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 200
        body = res.json()
        assert body["id"] == user["id"]
        assert body["email"] == email
        assert body["name"] == "New Harry"

    @pytest.mark.asyncio
    async def test_update_user_name_returns_401_when_user_deleted(self, client):
        # Create a user via dev-login to get token
        email = "harry@example.com"
        login_res = await client.post("/auth/dev-login", json={"email": email})
        assert login_res.status_code == 200
        payload = login_res.json()
        token = payload["token"]

        # Simulate user being deleted between auth and update (via secured route)
        del_res = await client.delete(
            "/users/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert del_res.status_code in (200, 204)

        # Attempt to update now should 401
        res = await client.patch(
            "/users/me",
            json={"name": "New Harry"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 401
        assert res.json()["detail"] == "Could not validate credentials"


class TestUsersUpdateAuth:
    @pytest.mark.asyncio
    async def test_update_user_name_requires_auth(self, client):
        res = await client.patch("/users/me", json={"name": "Nope"})
        assert res.status_code == 401

        res = await client.patch(
            "/users/me",
            json={"name": "Nope"},
            headers={"Authorization": "Bearer not-a-real-token"},
        )
        assert res.status_code == 401


@pytest.mark.me
@pytest.mark.delete
class TestUsersDelete:
    @pytest.mark.asyncio
    async def test_delete_user_successfully(self, client):
        # Create a user via dev-login to get token
        email = "harry@example.com"
        login_res = await client.post("/auth/dev-login", json={"email": email})
        assert login_res.status_code == 200
        payload = login_res.json()
        token = payload["token"]
        user = payload["user"]

        # Delete current user via /users/me
        del_res = await client.delete(
            "/users/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert del_res.status_code in (200, 204)

        # Confirm it's gone via GET /users/{id}
        res = await client.get(f"/users/{user['id']}")
        assert res.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_user_unauthorized_after_already_deleted(self, client):
        # Create a user and delete it
        email = "harry@example.com"
        login_res = await client.post("/auth/dev-login", json={"email": email})
        assert login_res.status_code == 200
        payload = login_res.json()
        token = payload["token"]

        first_del = await client.delete(
            "/users/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert first_del.status_code in (200, 204)

        # Second delete with the same token should fail auth (user no longer exists)
        second_del = await client.delete(
            "/users/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert second_del.status_code == 401
        assert second_del.json()["detail"] == "Could not validate credentials"
