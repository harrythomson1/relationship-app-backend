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
