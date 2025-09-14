from uuid import uuid4

from httpx import AsyncClient


async def _create_user(client: AsyncClient, *, name: str = "Test User"):
    email = f"test+{uuid4().hex[:8]}@example.com"
    res = await client.post("/users", json={"email": email, "name": name})
    assert res.status_code == 201, res.text
    body = res.json()
    return body


async def dev_login(client: AsyncClient, email: str | None = None):
    # Dev login now expects an email body and returns { user: {...}, token: "..." }
    if email is None:
        email = f"test+{uuid4().hex[:8]}@example.com"
    res = await client.post("/auth/dev-login", json={"email": email})
    assert res.status_code == 200, res.text
    body = res.json()
    # breakpoint()
    return body["token"], body["user"]


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
    token, user = await dev_login(client)
    u2 = await _create_user(client)
    payload = {
        "type": "romantic",
        "status": "pending",
        "role": "partner",
        "user_ids": [user["id"], u2["id"]],
    }
    return await client.post("/relationships", json=payload), token


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
