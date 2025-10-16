"""fix_cascade_delete_constraints

Revision ID: 540d516e584e
Revises: a5d42366c591
Create Date: 2025-10-13 11:36:39.002187

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "540d516e584e"
down_revision: Union[str, Sequence[str], None] = "a5d42366c591"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Fix CASCADE DELETE constraints by dropping and recreating them.
    The previous migrations created the constraints but they ended up as NO ACTION.
    """
    # Fix mcp_servers.connector_id foreign key
    op.drop_constraint("fk_mcp_servers_connector_id", "mcp_servers", type_="foreignkey")
    op.create_foreign_key(
        "fk_mcp_servers_connector_id",
        "mcp_servers",
        "mcp_connectors",
        ["connector_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # Fix connector_access.connector_id foreign key
    op.drop_constraint(
        "connector_access_connector_id_fkey", "connector_access", type_="foreignkey"
    )
    op.create_foreign_key(
        "connector_access_connector_id_fkey",
        "connector_access",
        "mcp_connectors",
        ["connector_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    """
    Revert CASCADE DELETE constraints back to NO ACTION.
    """
    # Revert mcp_servers.connector_id foreign key
    op.drop_constraint("fk_mcp_servers_connector_id", "mcp_servers", type_="foreignkey")
    op.create_foreign_key(
        "fk_mcp_servers_connector_id",
        "mcp_servers",
        "mcp_connectors",
        ["connector_id"],
        ["id"],
    )

    # Revert connector_access.connector_id foreign key
    op.drop_constraint(
        "connector_access_connector_id_fkey", "connector_access", type_="foreignkey"
    )
    op.create_foreign_key(
        "connector_access_connector_id_fkey",
        "connector_access",
        "mcp_connectors",
        ["connector_id"],
        ["id"],
    )
