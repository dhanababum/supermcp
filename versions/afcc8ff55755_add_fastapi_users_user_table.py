"""add_fastapi_users_user_table

Revision ID: afcc8ff55755
Revises: 0c86ec73bbae
Create Date: 2025-10-08 21:22:20.107069

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "afcc8ff55755"
down_revision: Union[str, Sequence[str], None] = "0c86ec73bbae"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create the user table for fastapi_users
    op.create_table(
        "user",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("hashed_password", sa.String(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("is_superuser", sa.Boolean(), nullable=False),
        sa.Column("is_verified", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_user_email"), "user", ["email"], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop the user table
    op.drop_index(op.f("ix_user_email"), table_name="user")
    op.drop_table("user")
