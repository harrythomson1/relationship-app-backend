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


@pytest.mark.users
@pytest.mark.create
class TestUsersCreate:
    @pytest.mark.asyncio
    async def test_create_user_success(self, client):
        payload = {
            "name": "Harry",
        }
        res = await client.post("/users", json=payload)
        assert res.status_code == 201
        body = res.json()
        assert body["email"] == "harry@example.com"
        assert body["name"] == "Harry"
        assert "id" in body and body["id"] > 0
        assert "created_at" in body
        assert body["supabase_user_id"] == "8012611b-e385-463e-b719-1a5b468a6ce5"

    @pytest.mark.asyncio
    async def test_create_user_duplicate_email_returns_conflict(self, client):
        payload = {"name": "Harry"}
        res = await client.post("/users", json=payload)
        assert res.status_code == 201
        res = await client.post("/users", json=payload)
        assert res.status_code == 409

    @pytest.mark.asyncio
    async def test_create_user_invalid_email_422(self, client):
        async def _override_invalid_email():
            return {
                "sub": "8012611b-e385-463e-b719-1a5b468a6ce5",
                "email": "not-an-email",
                "aud": "authenticated",
                "iss": "https://fakereference.supabase.co/auth/v1",
            }

        app.dependency_overrides[get_current_claims] = _override_invalid_email
        res = await client.post("/users", json={"name": "Harry"})
        app.dependency_overrides.clear()
        assert res.status_code == 422
        assert (
            res.json()["detail"]["message"]
            == "value is not a valid email address: An email address must have an @-sign."
        )


@pytest.mark.users
@pytest.mark.get
class TestUsersGet:
    @pytest.mark.asyncio
    async def test_get_user_successfully(self, client):
        payload = {"name": "Harry"}
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
