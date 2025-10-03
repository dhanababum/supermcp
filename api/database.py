import os
from sqlmodel import SQLModel, create_engine, Session
from typing import Generator

# Get database URL from environment variable or use default
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:mysecretpassword@localhost:5432/forge_mcptools"
)

# Create engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    echo=True,  # Set to False in production
    pool_pre_ping=True,  # Verify connections before using them
    pool_size=5,
    max_overflow=10
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

