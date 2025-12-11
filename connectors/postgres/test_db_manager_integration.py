"""
Integration tests for PoolManager class using real PostgreSQL database

These tests require a running PostgreSQL instance.
Connection: postgresql+asyncpg://postgres:mysecretpassword@localhost:5432/blackout

Run with: uv run pytest test_db_manager_integration.py -v
Skip if DB unavailable: pytest test_db_manager_integration.py -v -m "not integration"
"""

import asyncio
import pytest
from connectors.postgres.db_manager import PoolManager
from connectors.postgres.schema import PostgresConfig


# Database configuration from connection string
DB_CONFIG = PostgresConfig(
    host="localhost",
    port=5432,
    database="blackout",
    username="postgres",
    password="mysecretpassword",
    pool_size=5,
    max_overflow=10
)


@pytest.fixture(scope="function")
async def pool_manager():
    """Create a PoolManager instance for integration tests"""
    pm = PoolManager(
        global_max_connections=100,
        per_target_max=10,
        idle_ttl=300
    )
    yield pm
    # Cleanup: close all pools after each test
    try:
        for server_id in list(pm.pools.keys()):
            try:
                await pm.close_pool(server_id)
            except Exception:
                pass  # Ignore errors during cleanup
    except Exception:
        pass


@pytest.fixture(scope="function")
async def db_connection_available(pool_manager):
    """Check if database is available before running tests"""
    try:
        result = await pool_manager.test_connection("test_server", DB_CONFIG)
        if result.get("connected"):
            return True
        pytest.skip("Database connection failed: " + result.get("error", "Unknown"))
    except Exception as e:
        pytest.skip(f"Database not available: {str(e)}")


@pytest.mark.integration
@pytest.mark.asyncio
class TestDatabaseConnection:
    """Test real database connection"""

    async def test_connection_success(self, pool_manager, db_connection_available):
        """Test that we can connect to the database"""
        result = await pool_manager.test_connection("test_server", DB_CONFIG)
        
        assert result["connected"] is True
        assert result["status"] == "connected"
        assert result["database"] == "blackout"
        assert result["host"] == "localhost"
        assert result["port"] == 5432

    async def test_pool_creation(self, pool_manager, db_connection_available):
        """Test creating a connection pool"""
        pool = await pool_manager.get_pool("integration_test", DB_CONFIG)
        
        assert pool is not None
        assert "integration_test" in pool_manager.pools
        assert pool_manager.total_connections > 0


@pytest.mark.integration
@pytest.mark.asyncio
class TestTableOperations:
    """Test table listing and schema operations"""

    async def test_list_tables(self, pool_manager, db_connection_available):
        """Test listing all tables in the database"""
        tables = await pool_manager.get_tables("integration_test", DB_CONFIG)
        
        assert isinstance(tables, list)
        print(f"\n✓ Found {len(tables)} tables in database: {tables}")

    async def test_get_table_schema(self, pool_manager, db_connection_available):
        """Test getting schema for a table if any exist"""
        tables = await pool_manager.get_tables("integration_test", DB_CONFIG)
        
        if tables:
            # Get schema for the first table
            table_name = tables[0]
            schema = await pool_manager.get_table_schema(
                "integration_test",
                DB_CONFIG,
                table_name
            )
            
            assert schema["table_name"] == table_name
            assert "columns" in schema
            assert "primary_keys" in schema
            assert "foreign_keys" in schema
            assert "indexes" in schema
            assert isinstance(schema["columns"], list)
            
            print(f"\n✓ Table '{table_name}' has {len(schema['columns'])} columns")
        else:
            print("\n⚠ No tables found in database, skipping schema test")


@pytest.mark.integration
@pytest.mark.asyncio
class TestQueryExecution:
    """Test actual query execution"""

    async def test_simple_select(self, pool_manager, db_connection_available):
        """Test executing a simple SELECT query"""
        result = await pool_manager.execute_query(
            "integration_test",
            DB_CONFIG,
            "SELECT 1 as test_value, 'Hello' as test_text"
        )
        
        assert len(result) == 1
        assert result[0]["test_value"] == 1
        assert result[0]["test_text"] == "Hello"
        print(f"\n✓ Simple SELECT executed successfully: {result}")

    async def test_database_version(self, pool_manager, db_connection_available):
        """Test getting PostgreSQL version"""
        result = await pool_manager.execute_query(
            "integration_test",
            DB_CONFIG,
            "SELECT version() as pg_version"
        )
        
        assert len(result) == 1
        assert "PostgreSQL" in result[0]["pg_version"]
        print(f"\n✓ PostgreSQL version: {result[0]['pg_version']}")

    async def test_current_database(self, pool_manager, db_connection_available):
        """Test getting current database name"""
        result = await pool_manager.execute_query(
            "integration_test",
            DB_CONFIG,
            "SELECT current_database() as db_name"
        )
        
        assert len(result) == 1
        assert result[0]["db_name"] == "blackout"
        print(f"\n✓ Current database: {result[0]['db_name']}")

    async def test_table_count(self, pool_manager, db_connection_available):
        """Test counting tables in the database"""
        result = await pool_manager.execute_query(
            "integration_test",
            DB_CONFIG,
            """
            SELECT COUNT(*) as table_count 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            """
        )
        
        assert len(result) == 1
        table_count = result[0]["table_count"]
        print(f"\n✓ Found {table_count} tables in public schema")


@pytest.mark.integration
@pytest.mark.asyncio
class TestCreateDropTable:
    """Test creating and dropping a test table"""

    @pytest.fixture(scope="function")
    def test_table_name(self):
        """Generate unique test table name"""
        import time
        return f"test_pool_manager_temp_{int(time.time())}"

    async def test_create_table(self, pool_manager, db_connection_available, test_table_name):
        """Test creating a temporary test table"""
        # Drop table if it exists
        await pool_manager.execute_query(
            "integration_test",
            DB_CONFIG,
            f"DROP TABLE IF EXISTS {test_table_name}"
        )
        
        # Create table
        result = await pool_manager.execute_query(
            "integration_test",
            DB_CONFIG,
            f"""
            CREATE TABLE {test_table_name} (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                value INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        
        assert result[0]["affected_rows"] == 0  # CREATE TABLE returns 0 affected rows
        print(f"\n✓ Created test table: {test_table_name}")

    async def test_insert_data(self, pool_manager, db_connection_available, test_table_name):
        """Test inserting data into test table"""
        result = await pool_manager.execute_query(
            "integration_test",
            DB_CONFIG,
            f"""
            INSERT INTO {test_table_name} (name, value) 
            VALUES ('Test 1', 100), ('Test 2', 200), ('Test 3', 300)
            """
        )
        
        assert result[0]["affected_rows"] == 3
        print(f"\n✓ Inserted 3 rows into {test_table_name}")

    async def test_select_data(self, pool_manager, db_connection_available, test_table_name):
        """Test selecting data from test table"""
        result = await pool_manager.execute_query(
            "integration_test",
            DB_CONFIG,
            f"SELECT id, name, value FROM {test_table_name} ORDER BY id"
        )
        
        assert len(result) == 3
        assert result[0]["name"] == "Test 1"
        assert result[0]["value"] == 100
        assert result[1]["name"] == "Test 2"
        assert result[1]["value"] == 200
        assert result[2]["name"] == "Test 3"
        assert result[2]["value"] == 300
        print(f"\n✓ Retrieved {len(result)} rows from {test_table_name}")

    async def test_update_data(self, pool_manager, db_connection_available, test_table_name):
        """Test updating data in test table"""
        result = await pool_manager.execute_query(
            "integration_test",
            DB_CONFIG,
            f"UPDATE {test_table_name} SET value = value + 10 WHERE name = 'Test 1'"
        )
        
        assert result[0]["affected_rows"] == 1
        
        # Verify update
        verify = await pool_manager.execute_query(
            "integration_test",
            DB_CONFIG,
            f"SELECT value FROM {test_table_name} WHERE name = 'Test 1'"
        )
        
        assert verify[0]["value"] == 110
        print(f"\n✓ Updated data in {test_table_name}")

    async def test_delete_data(self, pool_manager, db_connection_available, test_table_name):
        """Test deleting data from test table"""
        result = await pool_manager.execute_query(
            "integration_test",
            DB_CONFIG,
            f"DELETE FROM {test_table_name} WHERE name = 'Test 2'"
        )
        
        assert result[0]["affected_rows"] == 1
        
        # Verify deletion
        verify = await pool_manager.execute_query(
            "integration_test",
            DB_CONFIG,
            f"SELECT COUNT(*) as count FROM {test_table_name}"
        )
        
        assert verify[0]["count"] == 2
        print(f"\n✓ Deleted data from {test_table_name}")

    async def test_drop_table(self, pool_manager, db_connection_available, test_table_name):
        """Test dropping the test table"""
        result = await pool_manager.execute_query(
            "integration_test",
            DB_CONFIG,
            f"DROP TABLE {test_table_name}"
        )
        
        assert result[0]["affected_rows"] == 0  # DROP TABLE returns 0
        print(f"\n✓ Dropped test table: {test_table_name}")


@pytest.mark.integration
@pytest.mark.asyncio
class TestParameterizedQueries:
    """Test parameterized queries"""

    async def test_parameterized_select(self, pool_manager, db_connection_available):
        """Test SELECT with parameters (PostgreSQL uses $1, $2 syntax)"""
        result = await pool_manager.execute_query(
            "integration_test",
            DB_CONFIG,
            "SELECT $1::int as num1, $2::text as text1",
            params={"value1": 42, "value2": "test"}
        )
        
        assert len(result) == 1
        assert result[0]["num1"] == 42
        assert result[0]["text1"] == "test"
        print(f"\n✓ Parameterized query executed: {result}")


@pytest.mark.integration
@pytest.mark.asyncio
class TestConcurrentQueries:
    """Test concurrent query execution"""

    async def test_concurrent_simple_queries(self, pool_manager, db_connection_available):
        """Test executing multiple queries concurrently"""
        queries = [
            pool_manager.execute_query(
                "integration_test",
                DB_CONFIG,
                f"SELECT {i} as value"
            )
            for i in range(10)
        ]
        
        results = await asyncio.gather(*queries)
        
        assert len(results) == 10
        for i, result in enumerate(results):
            assert result[0]["value"] == i
        
        print(f"\n✓ Executed 10 concurrent queries successfully")

    async def test_multiple_pool_connections(self, pool_manager, db_connection_available):
        """Test creating multiple pools and executing queries"""
        tasks = []
        for i in range(5):
            task = pool_manager.execute_query(
                f"integration_test_{i}",
                DB_CONFIG,
                f"SELECT {i} as server_id, current_database() as db"
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 5
        for i, result in enumerate(results):
            assert result[0]["server_id"] == i
            assert result[0]["db"] == "blackout"
        
        # Check that multiple pools were created
        assert len(pool_manager.pools) >= 5
        print(f"\n✓ Created {len(pool_manager.pools)} pools for concurrent operations")


@pytest.mark.integration
@pytest.mark.asyncio
class TestPoolManagement:
    """Test pool management operations"""

    async def test_pool_reuse(self, pool_manager, db_connection_available):
        """Test that pools are reused correctly"""
        # Execute query with server1
        await pool_manager.execute_query(
            "server1",
            DB_CONFIG,
            "SELECT 1"
        )
        
        pool_count_before = pool_manager.total_connections
        
        # Execute another query with same server - should reuse pool
        await pool_manager.execute_query(
            "server1",
            DB_CONFIG,
            "SELECT 2"
        )
        
        pool_count_after = pool_manager.total_connections
        
        # Connection count should not increase
        assert pool_count_before == pool_count_after
        print(f"\n✓ Pool reused successfully (connections: {pool_count_after})")

    async def test_close_pool(self, pool_manager, db_connection_available):
        """Test closing a specific pool"""
        # Create a pool
        await pool_manager.execute_query(
            "temp_server",
            DB_CONFIG,
            "SELECT 1"
        )
        
        assert "temp_server" in pool_manager.pools
        
        # Close the pool
        result = await pool_manager.close_pool("temp_server")
        
        assert result is True
        assert "temp_server" not in pool_manager.pools
        print(f"\n✓ Pool closed successfully")


@pytest.mark.integration
@pytest.mark.asyncio
class TestErrorHandling:
    """Test error handling with real database"""

    async def test_invalid_sql(self, pool_manager, db_connection_available):
        """Test handling of invalid SQL"""
        with pytest.raises(Exception):
            await pool_manager.execute_query(
                "integration_test",
                DB_CONFIG,
                "SELECT * FROM nonexistent_table_12345"
            )
        print("\n✓ Invalid SQL properly raises exception")

    async def test_syntax_error(self, pool_manager, db_connection_available):
        """Test handling of SQL syntax errors"""
        with pytest.raises(Exception):
            await pool_manager.execute_query(
                "integration_test",
                DB_CONFIG,
                "INVALID SQL SYNTAX HERE"
            )
        print("\n✓ Syntax error properly raises exception")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--tb=short"])

