import pytest
from httpx import AsyncClient

from tests.api.test_utils import _create_user, _set_claims


def _authenticate_as(user):
    _set_claims(
        {
            "sub": str(user["supabase_user_id"]),
            "email": user["email"],
            "aud": "authenticated",
            "iss": "https://fakereference.supabase.co/auth/v1",
        }
    )


class TestNotificationPreferences:
    @pytest.mark.asyncio
    async def test_default_is_all_enabled(self, client: AsyncClient):
        user = await _create_user(client)
        _authenticate_as(user)

        res = await client.get("/me/notification-preferences")
        assert res.status_code == 200
        assert res.json() == {"overlap_opening": True}

    @pytest.mark.asyncio
    async def test_disable_then_re_enable(self, client: AsyncClient):
        user = await _create_user(client)
        _authenticate_as(user)

        res = await client.patch("/me/notification-preferences", json={"overlap_opening": False})
        assert res.status_code == 200
        assert res.json() == {"overlap_opening": False}

        res = await client.get("/me/notification-preferences")
        assert res.json() == {"overlap_opening": False}

        res = await client.patch("/me/notification-preferences", json={"overlap_opening": True})
        assert res.json() == {"overlap_opening": True}

    @pytest.mark.asyncio
    async def test_disable_twice_is_idempotent(self, client: AsyncClient):
        user = await _create_user(client)
        _authenticate_as(user)

        for _ in range(2):
            res = await client.patch(
                "/me/notification-preferences", json={"overlap_opening": False}
            )
            assert res.status_code == 200
            assert res.json() == {"overlap_opening": False}

    @pytest.mark.asyncio
    async def test_unknown_key_rejected(self, client: AsyncClient):
        user = await _create_user(client)
        _authenticate_as(user)

        res = await client.patch("/me/notification-preferences", json={"unknown_key": False})
        assert res.status_code == 422

    @pytest.mark.asyncio
    async def test_empty_body_rejected(self, client: AsyncClient):
        user = await _create_user(client)
        _authenticate_as(user)

        res = await client.patch("/me/notification-preferences", json={})
        assert res.status_code == 422

    @pytest.mark.asyncio
    async def test_other_user_prefs_isolated(self, client: AsyncClient):
        user_a = await _create_user(client)
        _authenticate_as(user_a)
        await client.patch("/me/notification-preferences", json={"overlap_opening": False})

        user_b = await _create_user(client)
        _authenticate_as(user_b)
        res = await client.get("/me/notification-preferences")
        assert res.json() == {"overlap_opening": True}
