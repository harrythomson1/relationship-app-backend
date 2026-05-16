import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.api.main import app
from app.api.models import DeviceToken, NotificationOptOut, User
from app.api.notifications.keys import NotificationKey
from app.api.utils import push_client
from tests.api.test_utils import (
    _create_authed_relationship,
    _create_duplicate_relationship,
    _create_user,
    _set_claims,
    get_current_claims,
)


@pytest.fixture
def fake_push(monkeypatch):
    calls: list[dict] = []

    async def fake_send(tokens, title, body, data=None):
        calls.append({"tokens": list(tokens), "title": title, "body": body, "data": data})
        return push_client.PushSendResult(sent=len(tokens), dead_tokens=[])

    monkeypatch.setattr(
        "app.api.services.push_notifications_service.push_client.send_push", fake_send
    )
    return calls


async def _add_push_token_for(db_session, email: str, token: str):
    user = (await db_session.execute(select(User).where(User.email == email))).scalar_one()
    db_session.add(DeviceToken(user_id=user.id, token=token, platform="ios"))
    await db_session.commit()
    return user


@pytest.fixture
def claims():
    return {
        "sub": "8012611b-e385-463e-b719-1a5b468a6ce5",
        "email": "harry@example.com",
        "aud": "authenticated",
        "iss": "https://fakereference.supabase.co/auth/v1",
    }


@pytest.fixture(autouse=True)
def override_claims(claims):
    # Make every test “authenticated” by default
    async def _override():
        return claims

    app.dependency_overrides[get_current_claims] = _override
    yield
    app.dependency_overrides.clear()


@pytest.mark.asyncio
class TestRelationshipsCreate:
    async def test_create_relationship_success(self, client: AsyncClient):
        res = await _create_authed_relationship(client)
        assert res.status_code == 201, res.text
        body = res.json()
        assert body["id"] > 0
        assert body["type"] == "romantic"
        assert body["status"] == "active"
        assert "created_at" in body
        assert "updated_at" in body

    async def test_create_relationship_cannot_create_duplicates(self, client: AsyncClient):
        res = await _create_duplicate_relationship(client)
        assert res.status_code == 409
        assert (
            res.json()["detail"].get("message")
            == "A relationship between these users already exists"
        )


@pytest.mark.asyncio
class TestRelationshipsGet:
    async def test_get_relationship_success(self, client: AsyncClient):
        res = await _create_authed_relationship(client)
        assert res.status_code == 201, res.text
        rel_id = res.json()["id"]

        get_res = await client.get(f"/relationships/{rel_id}")
        assert get_res.status_code == 200, get_res.text
        body = get_res.json()
        assert body["id"] == rel_id
        assert body["type"] == "romantic"
        assert body["status"] == "active"

    async def test_get_relationship_404(self, client: AsyncClient):
        await _create_authed_relationship(client)
        res = await client.get("/relationships/999999")
        assert res.status_code == 404
        body = res.json()
        assert "detail" in body

    async def test_unauthorized_user(self, client: AsyncClient):
        rel = await _create_authed_relationship(client)

        _set_claims(
            {
                "sub": "not the authed user",
                "email": "random@email.com",
                "aud": "authenticated",
                "iss": "https://fakereference.supabase.co/auth/v1",
            }
        )
        rel_id = rel.json()["id"]
        get_res = await client.get(f"/relationships/{rel_id}")
        assert get_res.status_code == 401

    async def test_get_relationship_forbidden_for_non_member(self, client: AsyncClient):
        rel = await _create_authed_relationship(client)
        rel_id = rel.json()["id"]

        outsider = await _create_user(client)
        _set_claims(
            {
                "sub": str(outsider["supabase_user_id"]),
                "email": outsider["email"],
                "aud": "authenticated",
                "iss": "https://fakereference.supabase.co/auth/v1",
            }
        )
        get_res = await client.get(f"/relationships/{rel_id}")
        assert get_res.status_code == 403, get_res.text


@pytest.mark.asyncio
class TestRelationshipsUpdate:
    async def test_update_relationship_success(self, client: AsyncClient):
        result = await _create_authed_relationship(client)
        assert result.status_code == 201, result.text
        body = result.json()
        rel_id = body["id"]

        patch_payload = {"status": "active", "type": "friendship"}
        patch_res = await client.patch("/relationships", json=patch_payload)
        assert patch_res.status_code == 200, patch_res.text
        updated = patch_res.json()
        assert updated["id"] == rel_id
        assert updated["type"] == "friendship"
        assert updated["status"] == "active"

    async def test_setting_next_meet_at_notifies_partner(
        self, client: AsyncClient, db_session, fake_push
    ):
        from tests.api.test_utils import _create_relationship_invite

        res, inviter, invitee = await _create_relationship_invite(client)
        token = res.json()["token"]
        _set_claims(
            {
                "sub": str(invitee["supabase_user_id"]),
                "email": invitee["email"],
                "aud": "authenticated",
                "iss": "https://fakereference.supabase.co/auth/v1",
            }
        )
        await client.post(
            "/relationships",
            json={"type": "romantic", "status": "active", "role": "partner", "invite_token": token},
        )
        # Give the inviter (the partner from invitee's POV) a push token.
        await _add_push_token_for(db_session, inviter["email"], "ExponentPushToken[inviter]")

        res = await client.patch(
            "/relationships", json={"next_meet_at": "2026-12-01T10:00:00+00:00"}
        )
        assert res.status_code == 200, res.text

        assert len(fake_push) == 1
        sent = fake_push[0]
        assert sent["tokens"] == ["ExponentPushToken[inviter]"]
        assert sent["title"] == "Countdown updated"
        assert "Test Name" in sent["body"]
        assert sent["data"]["type"] == NotificationKey.countdown_updated.value

    async def test_clearing_next_meet_at_notifies_partner(
        self, client: AsyncClient, db_session, fake_push
    ):
        from tests.api.test_utils import _create_relationship_invite

        res, inviter, invitee = await _create_relationship_invite(client)
        token = res.json()["token"]
        _set_claims(
            {
                "sub": str(invitee["supabase_user_id"]),
                "email": invitee["email"],
                "aud": "authenticated",
                "iss": "https://fakereference.supabase.co/auth/v1",
            }
        )
        await client.post(
            "/relationships",
            json={"type": "romantic", "status": "active", "role": "partner", "invite_token": token},
        )
        await _add_push_token_for(db_session, inviter["email"], "ExponentPushToken[inviter]")

        # Set first, then clear.
        await client.patch("/relationships", json={"next_meet_at": "2026-12-01T10:00:00+00:00"})
        fake_push.clear()
        res = await client.patch("/relationships", json={"next_meet_at": None})
        assert res.status_code == 200, res.text

        assert len(fake_push) == 1
        assert fake_push[0]["title"] == "Countdown cleared"

    async def test_status_only_update_does_not_notify(
        self, client: AsyncClient, db_session, fake_push
    ):
        from tests.api.test_utils import _create_relationship_invite

        res, inviter, invitee = await _create_relationship_invite(client)
        token = res.json()["token"]
        _set_claims(
            {
                "sub": str(invitee["supabase_user_id"]),
                "email": invitee["email"],
                "aud": "authenticated",
                "iss": "https://fakereference.supabase.co/auth/v1",
            }
        )
        await client.post(
            "/relationships",
            json={"type": "romantic", "status": "active", "role": "partner", "invite_token": token},
        )
        await _add_push_token_for(db_session, inviter["email"], "ExponentPushToken[inviter]")

        res = await client.patch("/relationships", json={"type": "friendship"})
        assert res.status_code == 200, res.text
        assert fake_push == []

    async def test_partner_opt_out_suppresses_countdown_push(
        self, client: AsyncClient, db_session, fake_push
    ):
        from tests.api.test_utils import _create_relationship_invite

        res, inviter, invitee = await _create_relationship_invite(client)
        token = res.json()["token"]
        _set_claims(
            {
                "sub": str(invitee["supabase_user_id"]),
                "email": invitee["email"],
                "aud": "authenticated",
                "iss": "https://fakereference.supabase.co/auth/v1",
            }
        )
        await client.post(
            "/relationships",
            json={"type": "romantic", "status": "active", "role": "partner", "invite_token": token},
        )
        inviter_user = await _add_push_token_for(
            db_session, inviter["email"], "ExponentPushToken[inviter]"
        )
        db_session.add(
            NotificationOptOut(user_id=inviter_user.id, key=NotificationKey.countdown_updated.value)
        )
        await db_session.commit()

        res = await client.patch(
            "/relationships", json={"next_meet_at": "2026-12-01T10:00:00+00:00"}
        )
        assert res.status_code == 200, res.text
        assert fake_push == []

    async def test_update_relationship_404(self, client: AsyncClient):
        user = await _create_user(client)

        _set_claims(
            {
                "sub": str(user["supabase_user_id"]),
                "email": user["email"],
                "aud": "authenticated",
                "iss": "https://fakereference.supabase.co/auth/v1",
            }
        )
        patch_payload = {"status": "active", "type": "friendship"}
        res = await client.patch("/relationships", json=patch_payload)
        assert res.status_code == 404, res.text
        body = res.json()
        assert body["detail"].get("message") == "Relationship member not found"


@pytest.mark.asyncio
class TestRelationshipsDelete:
    async def test_delete_relationship_success(self, client: AsyncClient):
        result = await _create_authed_relationship(client)
        assert result.status_code == 201, result.text
        body = result.json()
        relationship_id = body["id"]
        deleted_relationship = await client.delete("/relationships")
        assert deleted_relationship.status_code == 204, (
            deleted_relationship.text or deleted_relationship.content
        )

        relationship = await client.get(f"/relationships/{relationship_id}")
        assert relationship.status_code == 404, relationship.text

    async def test_delete_relationship_when_headers_not_passed_in_delete(self, client: AsyncClient):
        res = await _create_authed_relationship(client)
        from app.api.auth.utils import get_current_claims
        from app.api.main import app

        prev = app.dependency_overrides.get(get_current_claims)
        app.dependency_overrides.pop(get_current_claims, None)

        deleted_relationship = await client.delete("/relationships")
        assert deleted_relationship.status_code == 401
        assert deleted_relationship.json()["detail"] == "Not authenticated"

        if prev is not None:
            app.dependency_overrides[get_current_claims] = prev

        rel_id = res.json()["id"]
        relationship = await client.get(f"/relationships/{rel_id}")
        assert relationship.status_code == 200, relationship.text

    async def test_delete_relationship_not_found(self, client: AsyncClient):
        from tests.api.test_utils import _set_claims

        user = await _create_user(client)
        _set_claims(
            {
                "sub": str(user["supabase_user_id"]),
                "email": user["email"],
                "aud": "authenticated",
                "iss": "https://fakereference.supabase.co/auth/v1",
            }
        )
        result = await client.delete("/relationships")
        assert result.status_code == 404, result.text
        assert result.json()["detail"]["message"] == "Relationship member not found"


@pytest.mark.asyncio
class TestRelationshipsPartnerGet:
    async def test_get_relationship_partner_success(self, client: AsyncClient):
        res = await _create_authed_relationship(client)
        assert res.status_code == 201

        res = await client.get("/relationships/partner")
        assert res.status_code == 200, res.text
        body = res.json()
        assert body["name"] == "Test Name"
        assert body["time_zone"] == "Europe/London"

    async def test_no_partner_found(self, client: AsyncClient):
        user = await _create_user(client)
        _set_claims(
            {
                "sub": str(user.get("supabase_user_id")),
                "email": user.get("email"),
                "aud": "authenticated",
                "iss": "https://fakereference.supabase.co/auth/v1",
            }
        )
        res = await client.get("/relationships/partner")
        assert res.status_code == 404
        assert res.json()["detail"].get("message") == "Relationship member not found"
