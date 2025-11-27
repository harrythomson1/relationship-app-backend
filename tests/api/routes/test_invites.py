import os

import pytest
from httpx import AsyncClient

from tests.api.test_utils import (
    _create_relationship_invite,
)


@pytest.fixture(autouse=True)
def set_test_env(monkeypatch):
    monkeypatch.setenv("GMAIL_APP_PASSWORD", "test_value")
    monkeypatch.setenv("APP_EMAIL", "no-reply@test.app")


class TestRelationshipInvite:
    @pytest.mark.asyncio
    async def test_invite_success(self, client: AsyncClient, auto_fake_email):
        res, inviter, invitee = await _create_relationship_invite(client)

        assert res.status_code == 201, res.text
        assert len(auto_fake_email) == 1
        assert auto_fake_email[0]["sender"] == os.environ.get("APP_EMAIL")
        assert auto_fake_email[0]["receiver"] == invitee["email"]
        assert auto_fake_email[0]["subject"] == "Let's connect"

    @pytest.mark.asyncio
    async def test_invite_duplication(self, client: AsyncClient, auto_fake_email):
        res, inviter, invitee = await _create_relationship_invite(client)

        assert res.status_code == 201, res.text
        res = await client.post("/relationships/invites", json={"invitee_email": invitee["email"]})
        assert res.status_code == 409
        assert res.json()["detail"]["message"] == "Invite already exists"
        assert len(auto_fake_email) == 1
