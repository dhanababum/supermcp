"""add_md5_constraint_to_secret

Revision ID: facb50928abc
Revises: e79dee610a78
Create Date: 2025-10-13 15:51:22.310744

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'facb50928abc'
down_revision: Union[str, Sequence[str], None] = 'e79dee610a78'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Add unique MD5 constraint on secret field."""
    # Add a unique constraint on MD5 hash of the secret
    # This ensures no two connectors can have the same secret value
    # Note: NULL secrets are allowed and considered distinct
    op.execute("""
        CREATE UNIQUE INDEX uq_mcp_connectors_secret_md5 
        ON mcp_connectors (md5(secret::text)) 
        WHERE secret IS NOT NULL
    """)


def downgrade() -> None:
    """Downgrade schema - Remove MD5 constraint."""
    op.execute("DROP INDEX IF EXISTS uq_mcp_connectors_secret_md5")
