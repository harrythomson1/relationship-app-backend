import os
from typing import cast

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from app.api.core.config import DATABASE_URL

_sql_echo = os.getenv("SQL_ECHO", "false").lower() == "true"
_pool_size = int(os.getenv("DB_POOL_SIZE", "10"))
_max_overflow = int(os.getenv("DB_POOL_MAX_OVERFLOW", "10"))
_pool_recycle = int(os.getenv("DB_POOL_RECYCLE_SECONDS", "300"))

engine = create_async_engine(
    cast(str, DATABASE_URL),
    echo=_sql_echo,
    pool_pre_ping=True,
    pool_size=_pool_size,
    max_overflow=_max_overflow,
    pool_recycle=_pool_recycle,
)

SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

Base = declarative_base()


async def get_db():
    async with SessionLocal() as session:
        yield session
