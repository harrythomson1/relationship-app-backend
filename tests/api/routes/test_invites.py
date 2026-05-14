import os
from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.api.models import Invite, InviteStatus
from tests.api.test_utils import (
    _create_relationship_invite,
    _create_user,
    _set_claims,
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

    @pytest.mark.asyncio
    async def test_invite_response_contains_token(self, client: AsyncClient, auto_fake_email):
        res, _, _ = await _create_relationship_invite(client)

        assert res.status_code == 201, res.text
        body = res.json()
        assert "token" in body
        assert body["token"] is not None

    @pytest.mark.asyncio
    async def test_invite_rate_limit(self, client: AsyncClient, auto_fake_email):
        inviter = await _create_user(client)
        _set_claims(
            {
                "sub": str(inviter["supabase_user_id"]),
                "email": inviter["email"],
                "aud": "authenticated",
                "iss": "https://fakereference.supabase.co/auth/v1",
            }
        )
        for i in range(10):
            res = await client.post(
                "/relationships/invites", json={"invitee_email": f"u{i}@example.com"}
            )
            assert res.status_code == 201, res.text

        res = await client.post("/relationships/invites", json={"invitee_email": "u10@example.com"})
        assert res.status_code == 429, res.text
        assert "rate limit" in res.json()["detail"]["message"].lower()

    @pytest.mark.asyncio
    async def test_invite_to_nonexistent_email_succeeds(self, client: AsyncClient, auto_fake_email):
        inviter = await _create_user(client)
        _set_claims(
            {
                "sub": str(inviter["supabase_user_id"]),
                "email": inviter["email"],
                "aud": "authenticated",
                "iss": "https://fakereference.supabase.co/auth/v1",
            }
        )
        res = await client.post(
            "/relationships/invites",
            json={"invitee_email": "nobody@nowhere.example"},
        )
        assert res.status_code == 201, res.text
        assert len(auto_fake_email) == 1
        assert auto_fake_email[0]["receiver"] == "nobody@nowhere.example"


class TestRelationshipInviteAccept:
    @pytest.mark.asyncio
    async def test_wrong_user_cannot_accept_invite(self, client: AsyncClient):
        res, inviter, invitee = await _create_relationship_invite(client)
        assert res.status_code == 201, res.text
        token = res.json()["token"]

        third_party = await _create_user(client)
        _set_claims(
            {
                "sub": str(third_party["supabase_user_id"]),
                "email": third_party["email"],
                "aud": "authenticated",
                "iss": "https://fakereference.supabase.co/auth/v1",
            }
        )
        res = await client.post(
            "/relationships",
            json={"type": "romantic", "status": "active", "role": "partner", "invite_token": token},
        )
        assert res.status_code == 403, res.text
        assert res.json()["detail"]["message"] == "Current user does not match user from the invite"

    @pytest.mark.asyncio
    async def test_invalid_token_returns_error(self, client: AsyncClient):
        invitee = await _create_user(client)
        _set_claims(
            {
                "sub": str(invitee["supabase_user_id"]),
                "email": invitee["email"],
                "aud": "authenticated",
                "iss": "https://fakereference.supabase.co/auth/v1",
            }
        )
        res = await client.post(
            "/relationships",
            json={
                "type": "romantic",
                "status": "active",
                "role": "partner",
                "invite_token": "00000000-0000-0000-0000-000000000000",
            },
        )
        assert res.status_code == 404, res.text
        assert res.json()["detail"]["message"] == "Relationship invite not found"

    @pytest.mark.asyncio
    async def test_third_party_cannot_decline_invite(self, client: AsyncClient):
        res, _inviter, _invitee = await _create_relationship_invite(client)
        assert res.status_code == 201, res.text
        token = res.json()["token"]

        third_party = await _create_user(client)
        _set_claims(
            {
                "sub": str(third_party["supabase_user_id"]),
                "email": third_party["email"],
                "aud": "authenticated",
                "iss": "https://fakereference.supabase.co/auth/v1",
            }
        )
        res = await client.put(f"/relationships/invites/{token}/decline")
        assert res.status_code == 403, res.text
        assert res.json()["detail"]["message"] == "Invite is not addressed to this user"

    @pytest.mark.asyncio
    async def test_invitee_can_decline_invite(self, client: AsyncClient):
        res, _inviter, invitee = await _create_relationship_invite(client)
        assert res.status_code == 201, res.text
        token = res.json()["token"]

        _set_claims(
            {
                "sub": str(invitee["supabase_user_id"]),
                "email": invitee["email"],
                "aud": "authenticated",
                "iss": "https://fakereference.supabase.co/auth/v1",
            }
        )
        res = await client.put(f"/relationships/invites/{token}/decline")
        assert res.status_code == 204, res.text

    @pytest.mark.asyncio
    async def test_expired_invite_cannot_be_accepted(self, client: AsyncClient, db_session):
        res, _inviter, invitee = await _create_relationship_invite(client)
        assert res.status_code == 201, res.text
        token = res.json()["token"]

        invite = (
            await db_session.execute(select(Invite).where(Invite.token == token))
        ).scalar_one()
        invite.expires_at = datetime.now(UTC) - timedelta(seconds=1)
        await db_session.commit()

        _set_claims(
            {
                "sub": str(invitee["supabase_user_id"]),
                "email": invitee["email"],
                "aud": "authenticated",
                "iss": "https://fakereference.supabase.co/auth/v1",
            }
        )
        res = await client.post(
            "/relationships",
            json={"type": "romantic", "status": "active", "role": "partner", "invite_token": token},
        )
        assert res.status_code == 410, res.text
        assert res.json()["detail"]["message"] == "Invite has expired"

        refreshed = (
            await db_session.execute(select(Invite).where(Invite.token == token))
        ).scalar_one()
        assert refreshed.status == InviteStatus.expired
