"""add new models structure

Revision ID: c2608651c99d
Revises: 2ef36bf0c572
Create Date: 2025-10-05 12:42:11.531311

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'c2608651c99d'
down_revision: Union[str, Sequence[str], None] = '2ef36bf0c572'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create mcp_connectors table
    op.create_table('mcp_connectors',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('url', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('description', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('version', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('source_logo_url', sa.LargeBinary(), nullable=False),
        sa.Column('logo_url', sa.LargeBinary(), nullable=False),
        sa.Column('configuration', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Update mcp_servers table - add connector_id column
    op.add_column('mcp_servers', sa.Column('connector_id', sqlmodel.sql.sqltypes.AutoString(), nullable=True))
    
    # Update mcp_server_tools table - change tools column to new structure
    op.drop_column('mcp_server_tools', 'tools')
    op.add_column('mcp_server_tools', sa.Column('tools', postgresql.JSONB(astext_type=sa.Text()), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Drop mcp_connectors table
    op.drop_table('mcp_connectors')
    
    # Remove connector_id from mcp_servers
    op.drop_column('mcp_servers', 'connector_id')
    
    # Revert mcp_server_tools changes
    op.drop_column('mcp_server_tools', 'tools')
    op.add_column('mcp_server_tools', sa.Column('tool_collection', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
