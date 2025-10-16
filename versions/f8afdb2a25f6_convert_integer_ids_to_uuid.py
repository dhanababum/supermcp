"""convert_integer_ids_to_uuid

Revision ID: f8afdb2a25f6
Revises: 540d516e584e
Create Date: 2025-10-13 12:20:50.814268

Converts ONLY mcp_servers.id from INTEGER to UUID.
All other tables keep integer IDs, but reference the UUID server_id via foreign keys.

Changes:
1. mcp_servers.id: INTEGER → UUID
2. mcp_server_tokens.mcp_server_id: INTEGER → UUID (FK reference)
3. mcp_server_tools.mcp_server_id: INTEGER → UUID (FK reference)
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "f8afdb2a25f6"
down_revision: Union[str, Sequence[str], None] = "540d516e584e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Convert mcp_servers.id from INTEGER to UUID.
    Also update foreign key references in mcp_server_tokens and mcp_server_tools.

    Strategy:
    1. Enable uuid-ossp extension
    2. Add UUID column to mcp_servers
    3. Generate UUIDs for existing servers
    4. Update foreign key references in child tables
    5. Drop old constraints and columns
    6. Rename UUID columns and recreate constraints
    """

    # Step 1: Enable UUID extension
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')

    # ============================================================================
    # STEP 2: MCP_SERVERS - Convert id to UUID
    # ============================================================================

    # Add new UUID column for server id
    op.add_column(
        "mcp_servers",
        sa.Column("id_uuid", postgresql.UUID(as_uuid=True), nullable=True),
    )

    # Generate UUIDs for existing servers
    op.execute(
        """
        UPDATE mcp_servers 
        SET id_uuid = uuid_generate_v4()
    """
    )

    # Make it NOT NULL
    op.alter_column("mcp_servers", "id_uuid", nullable=False)

    # ============================================================================
    # STEP 3: MCP_SERVER_TOKENS - Update foreign key to UUID
    # ============================================================================

    # Add new UUID column for server reference
    op.add_column(
        "mcp_server_tokens",
        sa.Column("mcp_server_id_uuid", postgresql.UUID(as_uuid=True), nullable=True),
    )

    # Copy UUID references from mcp_servers
    op.execute(
        """
        UPDATE mcp_server_tokens mst
        SET mcp_server_id_uuid = ms.id_uuid
        FROM mcp_servers ms
        WHERE mst.mcp_server_id = ms.id
    """
    )

    # Make it NOT NULL
    op.alter_column("mcp_server_tokens", "mcp_server_id_uuid", nullable=False)

    # ============================================================================
    # STEP 4: MCP_SERVER_TOOLS - Update foreign key to UUID
    # ============================================================================

    # Add new UUID column for server reference
    op.add_column(
        "mcp_server_tools",
        sa.Column("mcp_server_id_uuid", postgresql.UUID(as_uuid=True), nullable=True),
    )

    # Copy UUID references from mcp_servers
    op.execute(
        """
        UPDATE mcp_server_tools mst
        SET mcp_server_id_uuid = ms.id_uuid
        FROM mcp_servers ms
        WHERE mst.mcp_server_id = ms.id
    """
    )

    # Make it NOT NULL
    op.alter_column("mcp_server_tools", "mcp_server_id_uuid", nullable=False)

    # ============================================================================
    # STEP 5: DROP OLD CONSTRAINTS AND COLUMNS
    # ============================================================================

    # Drop foreign keys from child tables
    op.drop_constraint(
        "mcp_server_tools_mcp_server_id_fkey", "mcp_server_tools", type_="foreignkey"
    )
    op.drop_constraint(
        "mcp_server_tokens_mcp_server_id_fkey", "mcp_server_tokens", type_="foreignkey"
    )

    # Drop primary key from mcp_servers
    op.drop_constraint("mcp_servers_pkey", "mcp_servers", type_="primary")

    # Drop old integer id column from mcp_servers and rename UUID column
    op.drop_column("mcp_servers", "id")
    op.alter_column("mcp_servers", "id_uuid", new_column_name="id")
    op.create_primary_key("mcp_servers_pkey", "mcp_servers", ["id"])

    # Drop old integer foreign key columns from child tables and rename UUID columns
    # mcp_server_tokens
    op.drop_column("mcp_server_tokens", "mcp_server_id")
    op.alter_column(
        "mcp_server_tokens", "mcp_server_id_uuid", new_column_name="mcp_server_id"
    )
    op.create_foreign_key(
        "mcp_server_tokens_mcp_server_id_fkey",
        "mcp_server_tokens",
        "mcp_servers",
        ["mcp_server_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # mcp_server_tools
    op.drop_column("mcp_server_tools", "mcp_server_id")
    op.alter_column(
        "mcp_server_tools", "mcp_server_id_uuid", new_column_name="mcp_server_id"
    )
    op.create_foreign_key(
        "mcp_server_tools_mcp_server_id_fkey",
        "mcp_server_tools",
        "mcp_servers",
        ["mcp_server_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    """
    Revert mcp_servers.id from UUID back to INTEGER.

    WARNING: This will generate new integer IDs and lose UUID references!
    Use only for testing/development.
    """

    # Drop foreign keys from child tables
    op.drop_constraint(
        "mcp_server_tools_mcp_server_id_fkey", "mcp_server_tools", type_="foreignkey"
    )
    op.drop_constraint(
        "mcp_server_tokens_mcp_server_id_fkey", "mcp_server_tokens", type_="foreignkey"
    )

    # Drop primary key from mcp_servers
    op.drop_constraint("mcp_servers_pkey", "mcp_servers", type_="primary")

    # Rename UUID columns and add integer columns with sequences
    # mcp_servers
    op.alter_column("mcp_servers", "id", new_column_name="id_uuid")
    op.add_column(
        "mcp_servers",
        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("nextval('mcp_servers_id_seq'::regclass)"),
        ),
    )
    op.create_primary_key("mcp_servers_pkey", "mcp_servers", ["id"])

    # mcp_server_tokens
    op.alter_column(
        "mcp_server_tokens", "mcp_server_id", new_column_name="mcp_server_id_uuid"
    )
    op.add_column(
        "mcp_server_tokens", sa.Column("mcp_server_id", sa.Integer(), nullable=True)
    )

    # mcp_server_tools
    op.alter_column(
        "mcp_server_tools", "mcp_server_id", new_column_name="mcp_server_id_uuid"
    )
    op.add_column(
        "mcp_server_tools", sa.Column("mcp_server_id", sa.Integer(), nullable=True)
    )

    # Drop UUID columns
    op.drop_column("mcp_server_tools", "mcp_server_id_uuid")
    op.drop_column("mcp_server_tokens", "mcp_server_id_uuid")
    op.drop_column("mcp_servers", "id_uuid")
