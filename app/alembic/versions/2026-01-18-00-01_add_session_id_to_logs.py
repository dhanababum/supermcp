"""add session_id to tool call logs

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-01-18 00:01:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add session_id column for tracking connected clients."""
    op.add_column(
        'mcp_tool_call_logs',
        sa.Column('session_id', sa.String(length=255), nullable=True)
    )
    op.execute("""
        CREATE INDEX idx_logs_session_time 
        ON mcp_tool_call_logs (session_id, called_at DESC)
        WHERE session_id IS NOT NULL;
    """)


def downgrade() -> None:
    """Remove session_id column."""
    op.execute("DROP INDEX IF EXISTS idx_logs_session_time;")
    op.drop_column('mcp_tool_call_logs', 'session_id')
