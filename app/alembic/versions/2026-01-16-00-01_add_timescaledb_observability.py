"""add timescaledb observability

Revision ID: a1b2c3d4e5f6
Revises: 6c24970ed06d
Create Date: 2026-01-16 00:01:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '6c24970ed06d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create TimescaleDB observability infrastructure."""
    
    # 1. Enable TimescaleDB extension
    op.execute("CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;")
    
    # 2. Create the tool call logs table
    op.create_table(
        'mcp_tool_call_logs',
        sa.Column('called_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('server_id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=True),
        sa.Column('tool_name', sa.String(length=255), nullable=False),
        sa.Column('tool_type', sa.String(length=20), nullable=False),
        sa.Column('arguments', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('result_summary', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('called_at', 'id')
    )
    
    # 3. Convert to hypertable (7-day chunks)
    op.execute("""
        SELECT create_hypertable(
            'mcp_tool_call_logs',
            'called_at',
            chunk_time_interval => INTERVAL '7 days',
            if_not_exists => TRUE
        );
    """)
    
    # 4. Create indexes for common queries
    op.execute("""
        CREATE INDEX idx_logs_server_time 
        ON mcp_tool_call_logs (server_id, called_at DESC);
    """)
    op.execute("""
        CREATE INDEX idx_logs_tool_time 
        ON mcp_tool_call_logs (tool_name, called_at DESC);
    """)
    op.execute("""
        CREATE INDEX idx_logs_status 
        ON mcp_tool_call_logs (status, called_at DESC);
    """)
    
    # 5. Create 1-minute continuous aggregate for real-time metrics
    op.execute("""
        CREATE MATERIALIZED VIEW tool_metrics_1min
        WITH (timescaledb.continuous) AS
        SELECT
            time_bucket('1 minute', called_at) AS bucket,
            server_id,
            tool_name,
            COUNT(*) AS call_count,
            COUNT(*) FILTER (WHERE status = 'error') AS error_count,
            AVG(duration_ms)::integer AS avg_duration_ms,
            MAX(duration_ms) AS max_duration_ms,
            MIN(duration_ms) AS min_duration_ms
        FROM mcp_tool_call_logs
        GROUP BY bucket, server_id, tool_name
        WITH NO DATA;
    """)
    
    # 6. Create 1-hour continuous aggregate for historical views
    op.execute("""
        CREATE MATERIALIZED VIEW tool_metrics_1hr
        WITH (timescaledb.continuous) AS
        SELECT
            time_bucket('1 hour', called_at) AS bucket,
            server_id,
            tool_name,
            COUNT(*) AS call_count,
            COUNT(*) FILTER (WHERE status = 'error') AS error_count,
            AVG(duration_ms)::integer AS avg_duration_ms,
            MAX(duration_ms) AS max_duration_ms,
            MIN(duration_ms) AS min_duration_ms
        FROM mcp_tool_call_logs
        GROUP BY bucket, server_id, tool_name
        WITH NO DATA;
    """)
    
    # 7. Create 1-day continuous aggregate for long-term trends
    op.execute("""
        CREATE MATERIALIZED VIEW tool_metrics_1day
        WITH (timescaledb.continuous) AS
        SELECT
            time_bucket('1 day', called_at) AS bucket,
            server_id,
            tool_name,
            COUNT(*) AS call_count,
            COUNT(*) FILTER (WHERE status = 'error') AS error_count,
            AVG(duration_ms)::integer AS avg_duration_ms,
            MAX(duration_ms) AS max_duration_ms,
            MIN(duration_ms) AS min_duration_ms
        FROM mcp_tool_call_logs
        GROUP BY bucket, server_id, tool_name
        WITH NO DATA;
    """)
    
    # 8. Add refresh policies for continuous aggregates
    op.execute("""
        SELECT add_continuous_aggregate_policy('tool_metrics_1min',
            start_offset => INTERVAL '10 minutes',
            end_offset => INTERVAL '1 minute',
            schedule_interval => INTERVAL '30 seconds'
        );
    """)
    op.execute("""
        SELECT add_continuous_aggregate_policy('tool_metrics_1hr',
            start_offset => INTERVAL '3 hours',
            end_offset => INTERVAL '1 hour',
            schedule_interval => INTERVAL '1 hour'
        );
    """)
    op.execute("""
        SELECT add_continuous_aggregate_policy('tool_metrics_1day',
            start_offset => INTERVAL '3 days',
            end_offset => INTERVAL '1 day',
            schedule_interval => INTERVAL '1 day'
        );
    """)
    
    # 9. Add retention policies
    # Keep raw logs for 7 days
    op.execute("""
        SELECT add_retention_policy('mcp_tool_call_logs', INTERVAL '7 days');
    """)
    # Keep 1-minute aggregates for 30 days
    op.execute("""
        SELECT add_retention_policy('tool_metrics_1min', INTERVAL '30 days');
    """)
    # Keep 1-hour aggregates for 1 year
    op.execute("""
        SELECT add_retention_policy('tool_metrics_1hr', INTERVAL '365 days');
    """)
    # 1-day aggregates kept indefinitely (no retention policy)
    
    # 10. Enable compression on raw logs (compress chunks older than 1 day)
    op.execute("""
        ALTER TABLE mcp_tool_call_logs SET (
            timescaledb.compress,
            timescaledb.compress_segmentby = 'server_id'
        );
    """)
    op.execute("""
        SELECT add_compression_policy('mcp_tool_call_logs', INTERVAL '1 day');
    """)


def downgrade() -> None:
    """Remove TimescaleDB observability infrastructure."""
    
    # Remove compression policy
    op.execute("""
        SELECT remove_compression_policy('mcp_tool_call_logs', if_exists => true);
    """)
    
    # Remove retention policies
    op.execute("""
        SELECT remove_retention_policy('mcp_tool_call_logs', if_exists => true);
    """)
    op.execute("""
        SELECT remove_retention_policy('tool_metrics_1min', if_exists => true);
    """)
    op.execute("""
        SELECT remove_retention_policy('tool_metrics_1hr', if_exists => true);
    """)
    
    # Remove continuous aggregate policies
    op.execute("""
        SELECT remove_continuous_aggregate_policy('tool_metrics_1min', if_not_exists => true);
    """)
    op.execute("""
        SELECT remove_continuous_aggregate_policy('tool_metrics_1hr', if_not_exists => true);
    """)
    op.execute("""
        SELECT remove_continuous_aggregate_policy('tool_metrics_1day', if_not_exists => true);
    """)
    
    # Drop continuous aggregates (materialized views)
    op.execute("DROP MATERIALIZED VIEW IF EXISTS tool_metrics_1day CASCADE;")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS tool_metrics_1hr CASCADE;")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS tool_metrics_1min CASCADE;")
    
    # Drop indexes
    op.execute("DROP INDEX IF EXISTS idx_logs_server_time;")
    op.execute("DROP INDEX IF EXISTS idx_logs_tool_time;")
    op.execute("DROP INDEX IF EXISTS idx_logs_status;")
    
    # Drop table (this also removes the hypertable)
    op.drop_table('mcp_tool_call_logs')
    
    # Note: We don't drop the TimescaleDB extension as other tables may use it
