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
        res = await client.post("/users", json={"name": name})
        assert res.status_code == 201, res.text
        return res.json()
    finally:
        if prev is not None:
            app.dependency_overrides[get_current_claims] = prev
        else:
            app.dependency_overrides.pop(get_current_claims, None)


async def _create_relationship(client: AsyncClient):
    u1 = await _create_user(client)
    u2 = await _create_user(client)
    payload = {
        "type": "romantic",
        "status": "pending",
        "role": "partner",
        "user_ids": [u1["id"], u2["id"]],
    }
    return await client.post("/relationships", json=payload)


async def _create_authed_relationship(client: AsyncClient):
    u1 = await _create_user(client)
    u2 = await _create_user(client)
    _set_claims(
        {
            "sub": str(u1.get("supabase_user_id")),
            "email": u1.get("email"),
            "aud": "authenticated",
            "iss": "https://fakereference.supabase.co/auth/v1",
        }
    )
    payload = {
        "type": "romantic",
        "status": "pending",
        "role": "partner",
        "user_ids": [u1["id"], u2["id"]],
    }
    res = await client.post("/relationships", json=payload)
    return res, "dummy-token"


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
