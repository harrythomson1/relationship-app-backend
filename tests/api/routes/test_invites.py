import os

import pytest
from httpx import AsyncClient

from app.api.utils import mailer
from tests.api.test_utils import (
    _create_relationship_invite,
    fake_send_email_factory,
)


@pytest.fixture(autouse=True)
def set_test_env(monkeypatch):
    monkeypatch.setenv("GMAIL_APP_PASSWORD", "test_value")
    monkeypatch.setenv("APP_EMAIL", "no-reply@test.app")


class TestRelationshipInvite:
    @pytest.mark.asyncio
    async def test_invite_success(self, monkeypatch, client: AsyncClient):
        calls = []
        monkeypatch.setattr(mailer, "send_email", await fake_send_email_factory(calls))

        res, inviter, invitee = await _create_relationship_invite(client)

        assert res.status_code == 201, res.text
        assert len(calls) == 1
        assert calls[0]["sender"] == os.environ.get("APP_EMAIL")
        assert calls[0]["receiver"] == invitee["email"]
        assert calls[0]["subject"] == "Let's connect"

    @pytest.mark.asyncio
    async def test_invite_duplication(self, monkeypatch, client: AsyncClient):
        calls = []
        monkeypatch.setattr(mailer, "send_email", await fake_send_email_factory(calls))

        res, inviter, invitee = await _create_relationship_invite(client)

        assert res.status_code == 201, res.text
        res = await client.post("/relationships/invites", json={"invitee_email": invitee["email"]})
        assert res.status_code == 409
        assert res.json()["detail"]["message"] == "Invite already exists"
        assert len(calls) == 1
