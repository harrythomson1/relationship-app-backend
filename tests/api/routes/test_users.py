from uuid import uuid4

import pytest


@pytest.mark.users
@pytest.mark.create
class TestUsersCreate:
    @pytest.mark.asyncio
    async def test_create_user_success(self, client):
        payload = {"email": "harry@example.com", "name": "Harry"}
        res = await client.post("/users", json=payload)
        assert res.status_code == 201
        body = res.json()
        assert body["email"] == "harry@example.com"
        assert body["name"] == "Harry"
        assert "id" in body and body["id"] > 0
        assert "created_at" in body

    @pytest.mark.asyncio
    async def test_create_user_duplicate_email_returns_conflict(self, client):
        payload = {"email": "harry@example.com", "name": "Harry"}
        res = await client.post("/users", json=payload)
        assert res.status_code == 201
        res = await client.post("/users", json=payload)
        assert res.status_code == 409

    @pytest.mark.asyncio
    async def test_create_user_invalid_email_422(self, client):
        payload = {"email": "harry.com", "name": "Harry"}
        res = await client.post("/users", json=payload)
        assert res.status_code == 422
        assert (
            res.json()["detail"][0]["msg"]
            == "value is not a valid email address: An email address must have an @-sign."
        )


@pytest.mark.users
@pytest.mark.get
class TestUsersGet:
    @pytest.mark.asyncio
    async def test_get_user_successfully(self, client):
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
    async def test_get_user_fails_when_passing_not_an_int(self, client):
        res = await client.get("/users/NAN")
        assert res.status_code == 422
        assert (
            res.json()["detail"][0]["msg"]
            == "Input should be a valid integer, unable to parse string as an integer"
        )


class TestUsersMe:
    @pytest.mark.asyncio
    async def test_me_returns_current_user(self, client):
        # Dev-login to get a token
        email = f"harry+{uuid4().hex[:8]}@example.com"
        payload = {"email": email, "name": "Harry"}
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
        assert me["name"] == "Harry"
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

    @pytest.mark.asyncio
    async def test_update_user_name_404s_when_not_found(self, client):
        payload = {"email": "harry@example.com", "name": "Harry"}
        res = await client.post("/users", json=payload)
        payload = {"name": "New Harry"}
        assert res.status_code == 201
        created_user = res.json()
        user_id = created_user["id"]
        await client.delete(f"/users/{user_id}")
        res = await client.patch(f"/users/{user_id}", json=payload)
        assert res.status_code == 404
        assert res.json()["detail"]["message"] == "User not found"


@pytest.mark.users
@pytest.mark.delete
class TestUsersDelete:
    @pytest.mark.asyncio
    async def test_delete_user_successfully(self, client):
        payload = {"email": "harry@example.com", "name": "Harry"}
        res = await client.post("/users", json=payload)
        assert res.status_code == 201
        created_user = res.json()
        user_id = created_user["id"]
        res = await client.delete(f"/users/{user_id}")
        assert res.status_code == 204
        res = await client.get(f"/users/{user_id}")
        assert res.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_user_404s_when_not_found(self, client):
        payload = {"email": "harry@example.com", "name": "Harry"}
        res = await client.post("/users", json=payload)
        assert res.status_code == 201
        created_user = res.json()
        user_id = created_user["id"]
        res = await client.delete(f"/users/{user_id}")
        assert res.status_code == 204
        res = await client.delete(f"/users/{user_id}")
        assert res.status_code == 404
