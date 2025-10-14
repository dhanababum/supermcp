"""convert_connector_id_to_uuid

Revision ID: 543a0ca15c86
Revises: facb50928abc
Create Date: 2025-10-13 17:32:35.535177

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '543a0ca15c86'
down_revision: Union[str, Sequence[str], None] = 'facb50928abc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Convert connector IDs to UUID."""
    from sqlalchemy.dialects import postgresql
    
    # Enable UUID extension if not already enabled
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')
    
    # Step 1: Add UUID columns
    op.add_column('mcp_connectors', sa.Column('id_uuid', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('connector_access', sa.Column('connector_id_uuid', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('mcp_servers', sa.Column('connector_id_uuid', postgresql.UUID(as_uuid=True), nullable=True))
    
    # Step 2: Generate UUIDs for existing connectors
    op.execute("""
        UPDATE mcp_connectors 
        SET id_uuid = uuid_generate_v4()
    """)
    
    # Step 3: Update foreign key references
    op.execute("""
        UPDATE connector_access ca
        SET connector_id_uuid = mc.id_uuid
        FROM mcp_connectors mc
        WHERE ca.connector_id = mc.id
    """)
    
    op.execute("""
        UPDATE mcp_servers ms
        SET connector_id_uuid = mc.id_uuid
        FROM mcp_connectors mc
        WHERE ms.connector_id = mc.id
    """)
    
    # Step 4: Make UUID columns NOT NULL
    op.alter_column('mcp_connectors', 'id_uuid', nullable=False)
    op.alter_column('connector_access', 'connector_id_uuid', nullable=False)
    op.alter_column('mcp_servers', 'connector_id_uuid', nullable=False)
    
    # Step 5: Drop old constraints and columns
    op.drop_constraint('connector_access_connector_id_fkey', 'connector_access', type_='foreignkey')
    op.drop_constraint('fk_mcp_servers_connector_id', 'mcp_servers', type_='foreignkey')
    op.drop_constraint('mcp_connectors_pkey', 'mcp_connectors', type_='primary')
    
    # Step 6: Drop old columns
    op.drop_column('connector_access', 'connector_id')
    op.drop_column('mcp_servers', 'connector_id')
    op.drop_column('mcp_connectors', 'id')
    
    # Step 7: Rename UUID columns
    op.alter_column('mcp_connectors', 'id_uuid', new_column_name='id')
    op.alter_column('connector_access', 'connector_id_uuid', new_column_name='connector_id')
    op.alter_column('mcp_servers', 'connector_id_uuid', new_column_name='connector_id')
    
    # Step 8: Recreate primary key and foreign keys
    op.create_primary_key('mcp_connectors_pkey', 'mcp_connectors', ['id'])
    
    op.create_foreign_key(
        'connector_access_connector_id_fkey',
        'connector_access', 'mcp_connectors',
        ['connector_id'], ['id'],
        ondelete='CASCADE'
    )
    
    op.create_foreign_key(
        'fk_mcp_servers_connector_id',
        'mcp_servers', 'mcp_connectors',
        ['connector_id'], ['id'],
        ondelete='CASCADE'
    )
    
    # Step 9: Recreate MD5 secret index (if not exists)
    op.execute("""
        DROP INDEX IF EXISTS uq_mcp_connectors_secret_md5;
        CREATE UNIQUE INDEX uq_mcp_connectors_secret_md5 
        ON mcp_connectors (md5(secret::text)) 
        WHERE secret IS NOT NULL
    """)


def downgrade() -> None:
    """Downgrade schema - Convert connector IDs back to INTEGER."""
    # WARNING: This downgrade will lose UUID data!
    # It's recommended to backup before downgrading.
    
    # Drop MD5 index
    op.execute("DROP INDEX IF EXISTS uq_mcp_connectors_secret_md5")
    
    # Drop foreign keys
    op.drop_constraint('fk_mcp_servers_connector_id', 'mcp_servers', type_='foreignkey')
    op.drop_constraint('connector_access_connector_id_fkey', 'connector_access', type_='foreignkey')
    op.drop_constraint('mcp_connectors_pkey', 'mcp_connectors', type_='primary')
    
    # Rename UUID columns
    op.alter_column('mcp_connectors', 'id', new_column_name='id_uuid')
    op.alter_column('connector_access', 'connector_id', new_column_name='connector_id_uuid')
    op.alter_column('mcp_servers', 'connector_id', new_column_name='connector_id_uuid')
    
    # Add INTEGER columns
    op.add_column('mcp_connectors', sa.Column('id', sa.INTEGER(), nullable=False, server_default=sa.text("nextval('mcp_connectors_id_seq'::regclass)")))
    op.add_column('connector_access', sa.Column('connector_id', sa.INTEGER(), nullable=True))
    op.add_column('mcp_servers', sa.Column('connector_id', sa.INTEGER(), nullable=True))
    
    # Recreate primary key and constraints
    op.create_primary_key('mcp_connectors_pkey', 'mcp_connectors', ['id'])
    
    op.create_foreign_key(
        'connector_access_connector_id_fkey',
        'connector_access', 'mcp_connectors',
        ['connector_id'], ['id'],
        ondelete='CASCADE'
    )
    
    op.create_foreign_key(
        'fk_mcp_servers_connector_id',
        'mcp_servers', 'mcp_connectors',
        ['connector_id'], ['id'],
        ondelete='CASCADE'
    )
    
    # Drop UUID columns
    op.drop_column('mcp_servers', 'connector_id_uuid')
    op.drop_column('connector_access', 'connector_id_uuid')
    op.drop_column('mcp_connectors', 'id_uuid')
    
    # Recreate MD5 index
    op.execute("""
        CREATE UNIQUE INDEX uq_mcp_connectors_secret_md5 
        ON mcp_connectors (md5(secret::text)) 
        WHERE secret IS NOT NULL
    """)
