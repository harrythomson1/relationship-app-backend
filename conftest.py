# conftest.py
import os
from collections.abc import AsyncIterator

import pytest
import pytest_asyncio

# ---- Alembic (run migrations once per test session)
from alembic import command
from alembic.config import Config as AlembicConfig
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
)
from sqlalchemy.orm import sessionmaker

from app.api.core.database_connection import get_db  # your normal dependency

# ---- Your app imports
from app.api.main import app as fastapi_app


def run_migrations_once() -> None:
    """Apply Alembic migrations to the test DB (sync URL) once per session."""
    sync_url = os.environ.get("SYNC_DATABASE_URL")
    if not sync_url:
        raise RuntimeError("SYNC_DATABASE_URL not set for migrations")

    cfg = AlembicConfig("alembic.ini")
    # Make sure env.py reads this or you override in env.py, as you did earlier
    cfg.set_main_option("sqlalchemy.url", sync_url)
    command.upgrade(cfg, "head")


@pytest.fixture(scope="session", autouse=True)
def _apply_migrations() -> None:
    run_migrations_once()


@pytest.fixture(scope="session")
def app() -> FastAPI:
    # You can do more app-level overrides here if needed
    return fastapi_app


@pytest.fixture(scope="session")
def anyio_backend():
    # httpx AsyncClient uses anyio; let pytest-anyio know we want asyncio
    return "asyncio"


@pytest.fixture(scope="session")
def async_engine():
    async_url = os.environ.get("DATABASE_URL")
    if not async_url:
        raise RuntimeError("DATABASE_URL not set for tests")
    engine = create_async_engine(async_url, echo=False, pool_pre_ping=True, future=True)
    return engine


@pytest_asyncio.fixture()
async def db_session(async_engine) -> AsyncIterator[AsyncSession]:
    """
    Function-scoped session running inside a SAVEPOINT.
    After each test, we roll back so the DB is clean.
    """
    # 1) Open a connection and begin a transaction
    async with async_engine.connect() as conn:
        trans = await conn.begin()

        # 2) Start a nested transaction (SAVEPOINT) for the test
        nested = await conn.begin_nested()

        # 3) Create an AsyncSession bound to this connection
        SessionLocal = sessionmaker(bind=conn, class_=AsyncSession, expire_on_commit=False)
        async with SessionLocal() as session:
            # 4) Listen for subtransactions so that each commit in app code
            #    doesn't break the outer test transaction; SQLAlchemy will
            #    auto-create a new SAVEPOINT after each one is ended.
            @conn.run_sync
            def _add_listener(sync_conn):
                from sqlalchemy import event

                @event.listens_for(sync_conn, "after_transaction_end")
                def restart_savepoint(conn, transaction):
                    if transaction.nested and not transaction._parent.nested:
                        conn.begin_nested()

            yield session

        # 5) Roll back to the outer transaction (cleans all changes)
        await nested.rollback()
        await trans.rollback()


@pytest_asyncio.fixture()
async def client(app: FastAPI, db_session: AsyncSession):
    """
    An HTTP client whose requests use the test session via dependency override.
    """

    # Override get_db to yield our per-test session
    async def _get_test_db() -> AsyncIterator[AsyncSession]:
        yield db_session

    app.dependency_overrides[get_db] = _get_test_db
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            yield ac
    finally:
        app.dependency_overrides.clear()
