from uuid import uuid4

from httpx import AsyncClient

from app.api.auth.utils import get_current_claims
from app.api.main import app


def _set_claims(claims: dict):
    async def _override():
        return claims

    app.dependency_overrides[get_current_claims] = _override


async def _create_user(client: AsyncClient, *, name: str = "Test User"):
    prev = app.dependency_overrides.get(get_current_claims)
    new_claims = {
        "sub": str(uuid4()),
        "email": f"{uuid4().hex[:8]}@example.com",
        "aud": "authenticated",
        "iss": "https://fakereference.supabase.co/auth/v1",
    }
    try:
        _set_claims(new_claims)
        res = await client.post("/users", json={"name": "Test Name", "time_zone": "Europe/London"})
        assert res.status_code == 201, res.text
        return res.json()
    finally:
        if prev is not None:
            app.dependency_overrides[get_current_claims] = prev
        else:
            app.dependency_overrides.pop(get_current_claims, None)


async def _create_relationship(client: AsyncClient):
    await _create_user(client)
    u2 = await _create_user(client)
    payload = {
        "type": "romantic",
        "status": "active",
        "role": "partner",
        "partner_email": u2["email"],
    }
    return await client.post("/relationships", json=payload)


async def _create_relationship_invite(client: AsyncClient, inviter=None, invitee=None):
    inviter = inviter or await _create_user(client)
    invitee = invitee or await _create_user(client)

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
        json={"invitee_email": invitee["email"]},
    )

    return res, inviter, invitee


async def _create_authed_relationship(client: AsyncClient):
    res, inviter, invitee = await _create_relationship_invite(client)
    _set_claims(
        {
            "sub": str(invitee.get("supabase_user_id")),
            "email": invitee.get("email"),
            "aud": "authenticated",
            "iss": "https://fakereference.supabase.co/auth/v1",
        }
    )
    payload = {
        "type": "romantic",
        "status": "active",
        "role": "partner",
        "invite_token": res.json()["token"],
    }
    res = await client.post("/relationships", json=payload)
    return res


async def _create_duplicate_relationship(client: AsyncClient):
    res, inviter, invitee = await _create_relationship_invite(client)
    _set_claims(
        {
            "sub": str(invitee.get("supabase_user_id")),
            "email": invitee.get("email"),
            "aud": "authenticated",
            "iss": "https://fakereference.supabase.co/auth/v1",
        }
    )
    payload = {
        "type": "romantic",
        "status": "active",
        "role": "partner",
        "invite_token": res.json()["token"],
    }
    await client.post("/relationships", json=payload)
    res = await client.post("/relationships", json=payload)
    return res


async def fake_send_email_factory(calls):
    async def _fake_send_email(sender, receiver, subject, content):
        calls.append(
            {
                "sender": sender,
                "receiver": receiver,
                "subject": subject,
                "content": content,
            }
        )

    return _fake_send_email
