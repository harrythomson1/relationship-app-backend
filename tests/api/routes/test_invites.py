import os

import pytest
from httpx import AsyncClient

from app.api.utils import mailer
from tests.api.test_utils import (
    _create_user,
    _set_claims,
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

        user = await _create_user(client)
        user_2 = await _create_user(client)

        _set_claims(
            {
                "sub": str(user["supabase_user_id"]),
                "email": user["email"],
                "aud": "authenticated",
                "iss": "https://fakereference.supabase.co/auth/v1",
            }
        )

        res = await client.post("/relationships/invites", json={"invitee_email": user_2["email"]})
        assert res.status_code == 201, res.text
        assert len(calls) == 1
        assert calls[0]["sender"] == os.environ.get("APP_EMAIL")
        assert calls[0]["receiver"] == user_2["email"]
        assert calls[0]["subject"] == "Let's connect"
        assert calls[0]["content"] == "Hello, I want to add you to the relationship"

    @pytest.mark.asyncio
    async def test_invite_duplication(self, monkeypatch, client: AsyncClient):
        calls = []
        monkeypatch.setattr(mailer, "send_email", await fake_send_email_factory(calls))
        user = await _create_user(client)
        user_2 = await _create_user(client)
        _set_claims(
            {
                "sub": str(user["supabase_user_id"]),
                "email": user["email"],
                "aud": "authenticated",
                "iss": "https://fakereference.supabase.co/auth/v1",
            }
        )
        res = await client.post("/relationships/invites", json={"invitee_email": user_2["email"]})
        assert res.status_code == 201, res.text
        res = await client.post("/relationships/invites", json={"invitee_email": user_2["email"]})
        assert res.status_code == 409
        assert res.json()["detail"]["message"] == "Invite already exists"
        assert len(calls) == 1
