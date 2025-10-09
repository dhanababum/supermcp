import os
import logging
from sqlmodel import create_engine, Session
from typing import Generator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from collections.abc import AsyncGenerator

# Get database URL from environment variable or use default
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:mysecretpassword@localhost:5432/forge_mcptools"
)

# Async database URL for fastapi_users
ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

# Disable SQLAlchemy logging
logging.getLogger('sqlalchemy').setLevel(logging.WARNING)
logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
logging.getLogger('sqlalchemy.pool').setLevel(logging.WARNING)
logging.getLogger('sqlalchemy.dialects').setLevel(logging.WARNING)

# Create engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    echo=False,  # Disabled to prevent verbose logging
    pool_pre_ping=True,  # Verify connections before using them
    pool_size=5,
    max_overflow=10
)

# Create async engine for fastapi_users
async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10
)

# Create async session maker
async_session_maker = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)


def create_db_and_tables():
    """
    Create all database tables.
    NOTE: This is now handled by Alembic migrations.
    Use: alembic upgrade head
    """
    # SQLModel.metadata.create_all(engine)
    # Commented out - use Alembic migrations instead
    pass


def get_session() -> Generator[Session, None, None]:
    """
    Dependency function to get database session.
    Use this in FastAPI endpoints with Depends().
    """
    with Session(engine) as session:
        yield session


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session