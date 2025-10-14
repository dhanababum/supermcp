"""fix_connector_id_type_to_integer

Revision ID: 937bb56cd37e
Revises: 75ec8f84a2b1
Create Date: 2025-10-13 11:11:32.356329

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '937bb56cd37e'
down_revision: Union[str, Sequence[str], None] = '75ec8f84a2b1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Convert mcp_servers.connector_id from VARCHAR to INTEGER.
    This fixes the type mismatch where connector_id was a string but should be an integer foreign key.
    """
    # Step 1: Rename the old column
    op.alter_column('mcp_servers', 'connector_id', 
                    new_column_name='connector_id_old',
                    existing_type=sa.String(),
                    existing_nullable=False)
    
    # Step 2: Add new connector_id column as integer (nullable temporarily)
    op.add_column('mcp_servers', 
                  sa.Column('connector_id', sa.Integer(), nullable=True))
    
    # Step 3: Migrate data - convert string IDs to integer IDs
    # This assumes the old connector_id values were actually integer IDs stored as strings
    op.execute("""
        UPDATE mcp_servers 
        SET connector_id = CAST(connector_id_old AS INTEGER)
        WHERE connector_id_old ~ '^[0-9]+$'
    """)
    
    # Step 4: Make connector_id NOT NULL
    op.alter_column('mcp_servers', 'connector_id',
                    existing_type=sa.Integer(),
                    nullable=False)
    
    # Step 5: Add foreign key constraint with CASCADE DELETE
    op.create_foreign_key(
        'fk_mcp_servers_connector_id',
        'mcp_servers', 'mcp_connectors',
        ['connector_id'], ['id'],
        ondelete='CASCADE'  # Automatically delete servers when connector is deleted
    )
    
    # Step 6: Drop the old column
    op.drop_column('mcp_servers', 'connector_id_old')


def downgrade() -> None:
    """
    Revert mcp_servers.connector_id back to VARCHAR.
    """
    # Step 1: Drop foreign key constraint
    op.drop_constraint('fk_mcp_servers_connector_id', 'mcp_servers', type_='foreignkey')
    
    # Step 2: Rename current column
    op.alter_column('mcp_servers', 'connector_id',
                    new_column_name='connector_id_new',
                    existing_type=sa.Integer(),
                    existing_nullable=False)
    
    # Step 3: Add old VARCHAR column
    op.add_column('mcp_servers',
                  sa.Column('connector_id', sa.VARCHAR(), nullable=True))
    
    # Step 4: Migrate data back
    op.execute("""
        UPDATE mcp_servers 
        SET connector_id = CAST(connector_id_new AS VARCHAR)
    """)
    
    # Step 5: Make it NOT NULL
    op.alter_column('mcp_servers', 'connector_id',
                    existing_type=sa.String(),
                    nullable=False)
    
    # Step 6: Drop the integer column
    op.drop_column('mcp_servers', 'connector_id_new')
