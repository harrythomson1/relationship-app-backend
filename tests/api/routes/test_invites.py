import pytest
from httpx import AsyncClient

from app.api.utils import mailer
from tests.api.test_utils import (
    _create_user,
    dev_login,
    fake_send_email_factory,
)


class TestRelationshipInvite:
    @pytest.mark.asyncio
    async def test_invite_success(self, monkeypatch, client: AsyncClient):
        calls = []
        monkeypatch.setattr(mailer, "send_email", await fake_send_email_factory(calls))

        token, user = await dev_login(client)
        headers = {"Authorization": f"Bearer {token}"}
        user_2 = await _create_user(client)

        res = await client.post(
            "/relationships/invites", headers=headers, json={"invitee_email": user_2["email"]}
        )
        assert res.status_code == 201
        assert len(calls) == 1
        assert calls[0]["sender"] == user["email"]
        assert calls[0]["receiver"] == user_2["email"]
        assert calls[0]["subject"] == "Let's connect"
        assert calls[0]["content"] == "Hello, I want to add you to the relationship"

    @pytest.mark.asyncio
    async def test_invite_duplication(self, monkeypatch, client: AsyncClient):
        calls = []
        monkeypatch.setattr(mailer, "send_email", await fake_send_email_factory(calls))
        token, _ = await dev_login(client)
        headers = {"Authorization": f"Bearer {token}"}
        user_2 = await _create_user(client)
        res = await client.post(
            "/relationships/invites", headers=headers, json={"invitee_email": user_2["email"]}
        )
        assert res.status_code == 201
        res = await client.post(
            "/relationships/invites", headers=headers, json={"invitee_email": user_2["email"]}
        )
        assert res.status_code == 409
        assert res.json()["detail"]["message"] == "Invite already exists"
        assert len(calls) == 1
