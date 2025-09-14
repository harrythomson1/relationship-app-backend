import pytest
from httpx import AsyncClient

from tests.api.test_utils import (
    _create_user,
    dev_login,
)


class TestRelationshipInvite:
    @pytest.mark.asyncio
    async def test_invite_success(self, client: AsyncClient):
        token, _ = await dev_login(client)
        headers = {"Authorization": f"Bearer {token}"}
        user_2 = await _create_user(client)
        res = await client.post(
            "/relationships/invites", headers=headers, json={"invitee_email": user_2["email"]}
        )
        assert res.status_code == 201

    @pytest.mark.asyncio
    async def test_invite_duplication(self, client: AsyncClient):
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
