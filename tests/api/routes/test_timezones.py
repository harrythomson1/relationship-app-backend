import pytest
from httpx import AsyncClient

from tests.api.test_utils import (
    _create_authed_relationship,
)


@pytest.mark.asyncio
class TestTimezoneGet:
    async def test_get_partner_timezone_success(self, client: AsyncClient):
        res = await _create_authed_relationship(client)
        assert res.status_code == 201, res.text
        rel_id = res.json()["id"]

        get_res = await client.get("/relationships/timezones")
        assert get_res.status_code == 200, get_res.text
        body = get_res.json()
        assert body["id"] == rel_id
        assert body["type"] == "romantic"
        assert body["status"] == "active"
