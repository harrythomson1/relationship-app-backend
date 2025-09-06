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
