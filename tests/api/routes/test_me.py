import pytest


class TestUsersMe:
    @pytest.mark.asyncio
    async def test_me_returns_current_user(self, client):
        # Dev-login to get a token
        email = "harry@example.com"
        payload = {"email": email}
        res = await client.post("/auth/dev-login", json=payload)
        assert res.status_code == 200

        data = res.json()
        token = data["token"]
        user = data["user"]
        assert "id" in user and user["id"] > 0

        # Call /users/me with Bearer token
        res = await client.get(
            "/users/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 200
        me = res.json()
        assert me["id"] == user["id"]
        assert me["email"] == email
        assert me["name"] == "Test User"
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


@pytest.mark.users
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
        user = payload["user"]

        # Simulate user being deleted between auth and update
        del_res = await client.delete(f"/users/{user['id']}")
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
