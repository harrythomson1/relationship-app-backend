from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.main import app


@pytest.mark.asyncio
async def test_create_user():
    email = f"harry+{uuid4().hex[:8]}@example.com"
    payload = {"email": email, "name": "Harry"}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/users", json=payload)
        assert response.status_code == 201
