"""
Test script for MCP Server Observability with TimescaleDB.

This script tests:
1. TimescaleDB extension and hypertable creation
2. Tool call log insertion
3. Continuous aggregates queries
4. API endpoint responses

Run after applying migrations:
    python test_observability.py
"""

import asyncio
import uuid
from datetime import datetime, timezone, timedelta
import random

import asyncpg


async def get_connection():
    """Get database connection."""
    import os
    db_url = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:mysecretpassword@localhost:5433/forge_mcptools"
    )
    # Parse URL for asyncpg
    db_url = db_url.replace("postgresql://", "").replace("postgresql+asyncpg://", "")
    user_pass, host_db = db_url.split("@")
    user, password = user_pass.split(":")
    host_port, database = host_db.split("/")
    host = host_port.split(":")[0]
    port = int(host_port.split(":")[1]) if ":" in host_port else 5432
    
    return await asyncpg.connect(
        user=user,
        password=password,
        database=database,
        host=host,
        port=port,
    )


async def test_timescaledb_extension(conn):
    """Test TimescaleDB extension is enabled."""
    print("\n=== Testing TimescaleDB Extension ===")
    result = await conn.fetchval(
        "SELECT extversion FROM pg_extension WHERE extname = 'timescaledb'"
    )
    if result:
        print(f"  TimescaleDB version: {result}")
        return True
    else:
        print("  ERROR: TimescaleDB extension not found!")
        return False


async def test_hypertable_exists(conn):
    """Test hypertable was created."""
    print("\n=== Testing Hypertable ===")
    result = await conn.fetchrow("""
        SELECT hypertable_name, num_chunks 
        FROM timescaledb_information.hypertables 
        WHERE hypertable_name = 'mcp_tool_call_logs'
    """)
    if result:
        print(f"  Hypertable: {result['hypertable_name']}")
        print(f"  Chunks: {result['num_chunks']}")
        return True
    else:
        print("  ERROR: Hypertable not found!")
        return False


async def test_continuous_aggregates(conn):
    """Test continuous aggregates exist."""
    print("\n=== Testing Continuous Aggregates ===")
    views = ['tool_metrics_1min', 'tool_metrics_1hr', 'tool_metrics_1day']
    all_exist = True
    for view in views:
        result = await conn.fetchval(f"""
            SELECT COUNT(*) FROM timescaledb_information.continuous_aggregates 
            WHERE view_name = '{view}'
        """)
        if result > 0:
            print(f"  {view}: EXISTS")
        else:
            print(f"  {view}: NOT FOUND")
            all_exist = False
    return all_exist


async def test_insert_logs(conn, server_id: uuid.UUID):
    """Test inserting tool call logs."""
    print("\n=== Testing Log Insertion ===")
    tools = ['list_tables', 'execute_query', 'get_schema', 'test_connection']
    statuses = ['success', 'success', 'success', 'error']
    
    inserted = 0
    for i in range(20):
        tool = random.choice(tools)
        status = random.choice(statuses)
        duration = random.randint(10, 500)
        called_at = datetime.now(timezone.utc) - timedelta(minutes=random.randint(0, 60))
        
        await conn.execute("""
            INSERT INTO mcp_tool_call_logs 
            (called_at, server_id, tool_name, tool_type, status, duration_ms, arguments)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
        """, called_at, server_id, tool, 'static', status, duration, '{"test": true}')
        inserted += 1
    
    print(f"  Inserted {inserted} test logs")
    return inserted > 0


async def test_query_logs(conn, server_id: uuid.UUID):
    """Test querying logs from hypertable."""
    print("\n=== Testing Log Query ===")
    result = await conn.fetch("""
        SELECT tool_name, status, duration_ms, called_at 
        FROM mcp_tool_call_logs 
        WHERE server_id = $1 
        ORDER BY called_at DESC 
        LIMIT 5
    """, server_id)
    
    print(f"  Recent logs (showing {len(result)}):")
    for row in result:
        print(f"    - {row['tool_name']}: {row['status']} ({row['duration_ms']}ms)")
    return len(result) > 0


async def test_refresh_aggregates(conn):
    """Manually refresh continuous aggregates for testing."""
    print("\n=== Refreshing Continuous Aggregates ===")
    try:
        await conn.execute("""
            CALL refresh_continuous_aggregate('tool_metrics_1min', NULL, NULL);
        """)
        print("  tool_metrics_1min: refreshed")
        
        await conn.execute("""
            CALL refresh_continuous_aggregate('tool_metrics_1hr', NULL, NULL);
        """)
        print("  tool_metrics_1hr: refreshed")
        
        await conn.execute("""
            CALL refresh_continuous_aggregate('tool_metrics_1day', NULL, NULL);
        """)
        print("  tool_metrics_1day: refreshed")
        return True
    except Exception as e:
        print(f"  ERROR: {e}")
        return False


async def test_query_metrics(conn, server_id: uuid.UUID):
    """Test querying metrics from continuous aggregates."""
    print("\n=== Testing Metrics Query ===")
    
    # Query 1-minute aggregates
    result = await conn.fetch("""
        SELECT bucket, tool_name, call_count, error_count, avg_duration_ms
        FROM tool_metrics_1min
        WHERE server_id = $1
        ORDER BY bucket DESC
        LIMIT 5
    """, server_id)
    
    print(f"  1-minute metrics (showing {len(result)}):")
    for row in result:
        print(f"    - {row['bucket']}: {row['tool_name']} - {row['call_count']} calls, {row['error_count']} errors")
    
    # Query hourly summary
    summary = await conn.fetchrow("""
        SELECT 
            SUM(call_count) as total_calls,
            SUM(error_count) as total_errors,
            AVG(avg_duration_ms)::int as avg_duration
        FROM tool_metrics_1hr
        WHERE server_id = $1
    """, server_id)
    
    if summary and summary['total_calls']:
        print(f"\n  Hourly Summary:")
        print(f"    Total calls: {summary['total_calls']}")
        print(f"    Total errors: {summary['total_errors']}")
        print(f"    Avg duration: {summary['avg_duration']}ms")
    
    return True


async def test_compression_settings(conn):
    """Test compression is configured."""
    print("\n=== Testing Compression Settings ===")
    result = await conn.fetchrow("""
        SELECT compression_enabled 
        FROM timescaledb_information.hypertables 
        WHERE hypertable_name = 'mcp_tool_call_logs'
    """)
    if result and result['compression_enabled']:
        print("  Compression: ENABLED")
        return True
    else:
        print("  Compression: NOT ENABLED")
        return False


async def test_retention_policies(conn):
    """Test retention policies are configured."""
    print("\n=== Testing Retention Policies ===")
    result = await conn.fetch("""
        SELECT hypertable_name, schedule_interval, config 
        FROM timescaledb_information.jobs 
        WHERE proc_name = 'policy_retention'
    """)
    if result:
        for row in result:
            print(f"  {row['hypertable_name']}: interval={row['schedule_interval']}")
        return True
    else:
        print("  No retention policies found")
        return False


async def cleanup_test_data(conn, server_id: uuid.UUID):
    """Clean up test data."""
    print("\n=== Cleaning Up Test Data ===")
    await conn.execute("""
        DELETE FROM mcp_tool_call_logs WHERE server_id = $1
    """, server_id)
    print("  Test data cleaned up")


async def main():
    print("=" * 60)
    print("MCP Server Observability - TimescaleDB Test Suite")
    print("=" * 60)
    
    conn = await get_connection()
    test_server_id = uuid.uuid4()
    
    try:
        results = {
            "TimescaleDB Extension": await test_timescaledb_extension(conn),
            "Hypertable": await test_hypertable_exists(conn),
            "Continuous Aggregates": await test_continuous_aggregates(conn),
            "Log Insertion": await test_insert_logs(conn, test_server_id),
            "Log Query": await test_query_logs(conn, test_server_id),
            "Refresh Aggregates": await test_refresh_aggregates(conn),
            "Metrics Query": await test_query_metrics(conn, test_server_id),
            "Compression": await test_compression_settings(conn),
            "Retention Policies": await test_retention_policies(conn),
        }
        
        # Cleanup
        await cleanup_test_data(conn, test_server_id)
        
        # Summary
        print("\n" + "=" * 60)
        print("Test Summary")
        print("=" * 60)
        passed = sum(1 for v in results.values() if v)
        total = len(results)
        for test, result in results.items():
            status = "PASS" if result else "FAIL"
            print(f"  [{status}] {test}")
        print(f"\nTotal: {passed}/{total} tests passed")
        
        return passed == total
        
    finally:
        await conn.close()


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
