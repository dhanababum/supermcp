from __future__ import with_statement
import asyncio
from logging.config import fileConfig
from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import create_async_engine
from alembic import context
import sys
import os
import pathlib

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from src.config import settings


# Import all models to ensure they're registered
from src.models import (
    User,
    UserBase,
    McpConnector, 
    McpServer, 
    McpServerTool, 
    McpServerToken, 
    ConnectorAccess
)

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
fileConfig(config.config_file_name)

# Combine all metadata
from sqlalchemy import MetaData
combined_metadata = MetaData()

# Copy tables from SQLModel metadata (all SQLModel tables)
print("=" * 80)
print("Registering models for Alembic...")
print("=" * 80)
print(f"\nSQLModel tables detected: {list(SQLModel.metadata.tables.keys())}")
for table in SQLModel.metadata.tables.values():
    print(f"  - Copying table: {table.name}")
    table.tometadata(combined_metadata)

# Copy tables from UserBase metadata (FastAPI Users table)
print(f"\nUserBase tables detected: {list(UserBase.metadata.tables.keys())}")
for table in UserBase.metadata.tables.values():
    print(f"  - Copying table: {table.name}")
    table.tometadata(combined_metadata)

print(f"\nTotal tables in combined metadata: {list(combined_metadata.tables.keys())}")
print("=" * 80)

target_metadata = combined_metadata

db_url = str(settings.ASYNC_DATABASE_URL)
# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline():
    """Run migrations in 'offline' mode.
    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.
    Calls to context.execute() here emit the given string to the
    script output.
    """
    context.configure(
        url=db_url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        dialect_opts={"paramstyle": "named"},
        include_schemas=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online():
    """Run migrations in 'online' mode.
    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    connectable = create_async_engine(db_url, echo=False, future=True)

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())