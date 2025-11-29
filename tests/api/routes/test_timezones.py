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

        res = await client.get("/relationships/timezones")

        assert res.status_code == 200, res.text
        body = res.json()

        assert body["time_zone"] == "Europe/London"
        assert body["name"] == "Test Name"
