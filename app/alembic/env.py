import os
import sys
from logging.config import fileConfig
import asyncio

from sqlalchemy import engine_from_config
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import pool
from sqlmodel import SQLModel


from alembic import context

# Add parent directory to path to import models
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


from src.models import *
from src.config import settings
from sqlalchemy import MetaData

combined_metadata = MetaData()

# Copy tables from SQLModel metadata
for table in SQLModel.metadata.tables.values():
    print(f"Copying table: {table.name}")
    table.tometadata(combined_metadata)

# Copy tables from UserBase metadata (which includes the User table)
for table in UserBase.metadata.tables.values():
    table.tometadata(combined_metadata)


config = context.config

# Override sqlalchemy.url with environment variable if set
database_url = settings.ASYNC_DATABASE_URL
if database_url:
    config.set_main_option("sqlalchemy.url", database_url)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = combined_metadata


def do_run_migrations(connection):
    print("Target metadata: ", target_metadata.tables.keys())
    context.configure(
        connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online():
    """Run migrations in 'online' mode.
    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    print("Running migrations online")
    connectable = create_async_engine(database_url, echo=True, future=True)

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
