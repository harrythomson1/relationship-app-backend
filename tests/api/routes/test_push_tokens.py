import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.api.models import DeviceToken
from app.api.utils import push_client
from tests.api.test_utils import _create_user, _set_claims


@pytest.fixture(autouse=True)
def stub_expo_push(monkeypatch):
    calls: list[dict] = []

    async def fake_send(tokens, title, body, data=None):
        calls.append({"tokens": list(tokens), "title": title, "body": body, "data": data})
        return push_client.PushSendResult(sent=len(tokens), dead_tokens=[])

    monkeypatch.setattr(push_client, "send_push", fake_send)
    monkeypatch.setattr(
        "app.api.services.push_notifications_service.push_client.send_push", fake_send
    )
    yield calls


def _authenticate_as(user):
    _set_claims(
        {
            "sub": str(user["supabase_user_id"]),
            "email": user["email"],
            "aud": "authenticated",
            "iss": "https://fakereference.supabase.co/auth/v1",
        }
    )


class TestPushTokenRegistration:
    @pytest.mark.asyncio
    async def test_register_token(self, client: AsyncClient, db_session):
        user = await _create_user(client)
        _authenticate_as(user)

        res = await client.post(
            "/me/push-tokens",
            json={"token": "ExponentPushToken[abc123]", "platform": "ios"},
        )
        assert res.status_code == 201, res.text
        body = res.json()
        assert body["token"] == "ExponentPushToken[abc123]"
        assert body["platform"] == "ios"

        rows = (
            (
                await db_session.execute(
                    select(DeviceToken).where(DeviceToken.token == "ExponentPushToken[abc123]")
                )
            )
            .scalars()
            .all()
        )
        assert len(rows) == 1
        assert rows[0].user_id == user["id"]

    @pytest.mark.asyncio
    async def test_re_registering_same_token_updates_row(self, client: AsyncClient, db_session):
        user = await _create_user(client)
        _authenticate_as(user)

        await client.post(
            "/me/push-tokens", json={"token": "ExponentPushToken[abc]", "platform": "ios"}
        )
        res = await client.post(
            "/me/push-tokens", json={"token": "ExponentPushToken[abc]", "platform": "android"}
        )
        assert res.status_code == 201
        assert res.json()["platform"] == "android"

        rows = (
            (
                await db_session.execute(
                    select(DeviceToken).where(DeviceToken.token == "ExponentPushToken[abc]")
                )
            )
            .scalars()
            .all()
        )
        assert len(rows) == 1

    @pytest.mark.asyncio
    async def test_token_moves_to_new_user_on_reregister(self, client: AsyncClient, db_session):
        user_a = await _create_user(client)
        _authenticate_as(user_a)
        await client.post(
            "/me/push-tokens", json={"token": "ExponentPushToken[same]", "platform": "ios"}
        )

        user_b = await _create_user(client)
        _authenticate_as(user_b)
        res = await client.post(
            "/me/push-tokens", json={"token": "ExponentPushToken[same]", "platform": "ios"}
        )
        assert res.status_code == 201

        rows = (
            (
                await db_session.execute(
                    select(DeviceToken).where(DeviceToken.token == "ExponentPushToken[same]")
                )
            )
            .scalars()
            .all()
        )
        assert len(rows) == 1
        assert rows[0].user_id == user_b["id"]


class TestPushTokenSend:
    @pytest.fixture(autouse=True)
    def _enable_test_endpoint(self, monkeypatch):
        monkeypatch.setenv("ENABLE_TEST_PUSH_ENDPOINT", "true")

    @pytest.mark.asyncio
    async def test_endpoint_is_404_when_disabled(self, client: AsyncClient, monkeypatch):
        monkeypatch.delenv("ENABLE_TEST_PUSH_ENDPOINT", raising=False)
        user = await _create_user(client)
        _authenticate_as(user)
        res = await client.post("/me/push-tokens/test")
        assert res.status_code == 404, res.text

    @pytest.mark.asyncio
    async def test_test_endpoint_sends_to_caller_tokens(self, client: AsyncClient, stub_expo_push):
        user = await _create_user(client)
        _authenticate_as(user)
        await client.post(
            "/me/push-tokens", json={"token": "ExponentPushToken[t1]", "platform": "ios"}
        )
        await client.post(
            "/me/push-tokens",
            json={"token": "ExponentPushToken[t2]", "platform": "android"},
        )

        res = await client.post("/me/push-tokens/test")
        assert res.status_code == 200, res.text
        assert res.json()["sent"] == 2

        assert len(stub_expo_push) == 1
        sent = stub_expo_push[0]
        assert set(sent["tokens"]) == {"ExponentPushToken[t1]", "ExponentPushToken[t2]"}

    @pytest.mark.asyncio
    async def test_test_endpoint_with_no_tokens(self, client: AsyncClient, stub_expo_push):
        user = await _create_user(client)
        _authenticate_as(user)

        res = await client.post("/me/push-tokens/test")
        assert res.status_code == 200, res.text
        assert res.json()["sent"] == 0

    @pytest.mark.asyncio
    async def test_dead_tokens_are_removed(self, client: AsyncClient, db_session, monkeypatch):
        async def fake_send_with_dead(tokens, title, body, data=None):
            return push_client.PushSendResult(sent=0, dead_tokens=list(tokens))

        monkeypatch.setattr(
            "app.api.services.push_notifications_service.push_client.send_push",
            fake_send_with_dead,
        )

        user = await _create_user(client)
        _authenticate_as(user)
        await client.post(
            "/me/push-tokens", json={"token": "ExponentPushToken[dead]", "platform": "ios"}
        )

        res = await client.post("/me/push-tokens/test")
        assert res.status_code == 200
        assert res.json()["removed_dead_tokens"] == 1

        rows = (
            (
                await db_session.execute(
                    select(DeviceToken).where(DeviceToken.token == "ExponentPushToken[dead]")
                )
            )
            .scalars()
            .all()
        )
        assert rows == []


class TestPushTokenDeletion:
    @pytest.mark.asyncio
    async def test_unregister_token(self, client: AsyncClient, db_session):
        user = await _create_user(client)
        _authenticate_as(user)
        await client.post(
            "/me/push-tokens", json={"token": "ExponentPushToken[bye]", "platform": "ios"}
        )

        res = await client.delete("/me/push-tokens/ExponentPushToken[bye]")
        assert res.status_code == 204

        rows = (
            (
                await db_session.execute(
                    select(DeviceToken).where(DeviceToken.token == "ExponentPushToken[bye]")
                )
            )
            .scalars()
            .all()
        )
        assert rows == []
