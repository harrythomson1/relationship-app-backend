from logging.config import fileConfig

import psycopg
from alembic import context
from sqlalchemy import create_engine
from sqlalchemy.engine.url import make_url

from app.api import models  # noqa: F401
from app.api.db import Base
from migrations.env_settings import db_url

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata

target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


# Helper to get a sync DB URL from async one (for Alembic)
def db_sync_url():
    u = make_url(db_url())
    if u.drivername.endswith("+asyncpg"):
        u = u.set(drivername="postgresql+psycopg")
    u = u.set(host="127.0.0.1")  # force IPv4 like your working psql test
    return u


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    u = db_sync_url()
    url = u.render_as_string(hide_password=True)
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    u = db_sync_url()
    print(f"[alembic] Creating engine with URL: {u.render_as_string(hide_password=True)}")
    # Use a creator so SQLAlchemy uses our proven-good psycopg connection
    dsn = u.render_as_string(hide_password=False).replace("+psycopg", "")
    connectable = create_engine(
        "postgresql+psycopg://",
        creator=lambda: psycopg.connect(dsn),
        pool_pre_ping=True,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
