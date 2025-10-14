"""add_cascade_delete_to_connector_access

Revision ID: a5d42366c591
Revises: 937bb56cd37e
Create Date: 2025-10-13 11:17:15.855534

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a5d42366c591'
down_revision: Union[str, Sequence[str], None] = '937bb56cd37e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Add CASCADE DELETE to connector_access.connector_id foreign key.
    This ensures that when a connector is deleted, all access grants are automatically deleted.
    """
    # Drop the existing foreign key constraint
    op.drop_constraint('connector_access_connector_id_fkey', 'connector_access', type_='foreignkey')
    
    # Recreate it with CASCADE DELETE
    op.create_foreign_key(
        'connector_access_connector_id_fkey',
        'connector_access', 'mcp_connectors',
        ['connector_id'], ['id'],
        ondelete='CASCADE'
    )


def downgrade() -> None:
    """
    Remove CASCADE DELETE from connector_access.connector_id foreign key.
    """
    # Drop the CASCADE foreign key
    op.drop_constraint('connector_access_connector_id_fkey', 'connector_access', type_='foreignkey')
    
    # Recreate without CASCADE
    op.create_foreign_key(
        'connector_access_connector_id_fkey',
        'connector_access', 'mcp_connectors',
        ['connector_id'], ['id']
    )
