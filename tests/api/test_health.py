import pytest

from app.api.core.database_connection import get_db


@pytest.mark.asyncio
async def test_health(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "db": "ok"}


@pytest.mark.asyncio
async def test_health_returns_503_when_db_unavailable(app, client):
    class _BoomSession:
        async def execute(self, *args, **kwargs):
            raise RuntimeError("db down")

    async def _broken_db():
        yield _BoomSession()

    app.dependency_overrides[get_db] = _broken_db
    try:
        response = await client.get("/health")
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 503
    assert response.json() == {"status": "error", "db": "down"}
