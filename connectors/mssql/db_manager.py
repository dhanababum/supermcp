# MSSQL Database Manager with Connection Pooling
import asyncio
from collections import OrderedDict
import logging
from typing import Any, Dict, Optional, List
import aioodbc
from schema import MSSQLConfig


logger = logging.getLogger(__name__)


class PoolManager:
    def __init__(
        self,
        global_max_connections=500,
        per_target_max=20,
        idle_ttl=300
    ):
        self.global_max = global_max_connections
        self.per_target_max = per_target_max
        self.idle_ttl = idle_ttl
        # key -> (pool, last_used, conn_count, config)
        self.pools = OrderedDict()
        self.total_connections = 0
        self.lock = asyncio.Lock()

    def _build_connection_string(
        self, server_config: MSSQLConfig
    ) -> str:
        """Build ODBC connection string for MSSQL/Azure SQL"""
        # Use fixed ODBC Driver 18 for SQL Server
        conn_parts = [
            "DRIVER={ODBC Driver 18 for SQL Server}",
            f"SERVER={server_config.host},{server_config.port}",
            f"DATABASE={server_config.database}",
            f"UID={server_config.username}",
            f"PWD={server_config.password}",
        ]

        # Encryption and certificate settings
        if server_config.encrypt:
            conn_parts.append("Encrypt=yes")
        else:
            conn_parts.append("Encrypt=no")

        if server_config.trust_server_certificate:
            conn_parts.append("TrustServerCertificate=yes")
        else:
            conn_parts.append("TrustServerCertificate=no")

        # Azure SQL specific settings
        if server_config.azure_auth:
            conn_parts.append("Authentication=ActiveDirectoryPassword")

        # Additional parameters
        if server_config.additional_params:
            for key, value in server_config.additional_params.items():
                conn_parts.append(f"{key}={value}")

        return ";".join(conn_parts)

    async def _create_pool(self, server_config: MSSQLConfig):
        """Create a new connection pool"""
        connection_string = self._build_connection_string(server_config)

        # Create pool with specified size
        pool_size = min(server_config.pool_size, self.per_target_max)

        # aioodbc doesn't have built-in pooling like asyncpg,
        # so we use a simple pool implementation
        pool = await aioodbc.create_pool(
            dsn=connection_string,
            minsize=0,
            maxsize=pool_size,
            autocommit=True
        )

        return pool

    async def get_pool(self, server_id: str, server_config: MSSQLConfig):
        key = server_id
        async with self.lock:
            if key in self.pools:
                pool, _, _, _ = self.pools.pop(key)
                self.pools[key] = (
                    pool,
                    asyncio.get_event_loop().time(),
                    pool.maxsize,
                    server_config
                )
                return pool

            # Create pool lazily, but enforce global limits
            conn_limit = self.total_connections + self.per_target_max
            if conn_limit > self.global_max:
                await self.evict_one()

            pool = await self._create_pool(server_config)
            self.pools[key] = (
                pool,
                asyncio.get_event_loop().time(),
                pool.maxsize,
                server_config
            )
            self.total_connections += pool.maxsize
            return pool

    async def evict_one(self):
        """Evict least recently used idle pool"""
        for key, (pool, last_used, maxsize, _) in list(self.pools.items()):
            # Close the pool
            pool.close()
            await pool.wait_closed()
            self.total_connections -= maxsize
            del self.pools[key]
            return

    async def cleanup_loop(self):
        """Periodically cleanup idle connections"""
        while True:
            await asyncio.sleep(self.idle_ttl / 2)
            now = asyncio.get_event_loop().time()
            async with self.lock:
                items = list(self.pools.items())
                for key, (pool, last_used, maxsize, _) in items:
                    if now - last_used > self.idle_ttl:
                        pool.close()
                        await pool.wait_closed()
                        self.total_connections -= maxsize
                        del self.pools[key]

    async def close_pool(self, server_id: str):
        """Close pool based on server_id"""
        async with self.lock:
            if server_id in self.pools:
                pool, _, _, _ = self.pools.pop(server_id)
                pool.close()
                await pool.wait_closed()
                self.total_connections -= pool.maxsize
                return True
            return False

    async def execute_query(
        self,
        server_id: str,
        server_config: MSSQLConfig,
        query: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> list:
        """
        Execute a SQL query and return results.

        Args:
            query: SQL query to execute
            params: Query parameters (for parameterized queries)

        Returns:
            List of row dictionaries
        """
        try:
            pool = await self.get_pool(server_id, server_config)
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    # Determine if it's a SELECT query
                    query_upper = query.strip().upper()
                    is_select = (
                        query_upper.startswith('SELECT') or
                        query_upper.startswith('WITH')
                    )

                    if params:
                        # Convert dict params to positional for ODBC
                        if isinstance(params, dict):
                            param_values = tuple(params.values())
                        else:
                            param_values = params
                        await cursor.execute(query, param_values)
                    else:
                        await cursor.execute(query)

                    if is_select:
                        # Fetch all results for SELECT queries
                        rows = await cursor.fetchall()
                        if rows:
                            # Get column names
                            columns = [
                                desc[0] for desc in cursor.description
                            ]
                            # Convert to list of dictionaries
                            return [
                                dict(zip(columns, row)) for row in rows
                            ]
                        return []
                    else:
                        # For INSERT/UPDATE/DELETE, return affected rows
                        if cursor.rowcount >= 0:
                            affected_rows = cursor.rowcount
                        else:
                            affected_rows = 0
                        return [{"affected_rows": affected_rows}]

        except Exception as e:
            logger.error(f"Query execution failed: {str(e)}")
            raise

    async def get_tables(
        self, server_id: str, server_config: MSSQLConfig
    ) -> List[str]:
        """Get list of all tables in the database"""
        pool = await self.get_pool(server_id, server_config)
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                # Query sys.tables to get table names
                query = """
                    SELECT name
                    FROM sys.tables
                    WHERE type = 'U'
                    ORDER BY name
                """
                await cursor.execute(query)
                rows = await cursor.fetchall()
                return [row[0] for row in rows]

    async def get_table_schema(
        self,
        server_id: str,
        server_config: MSSQLConfig,
        table_name: str
    ) -> Dict[str, Any]:
        """Get schema information for a specific table"""
        pool = await self.get_pool(server_id, server_config)
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                # Get column information
                columns_query = """
                    SELECT
                        c.name AS column_name,
                        t.name AS data_type,
                        c.is_nullable,
                        c.max_length,
                        dc.definition AS column_default
                    FROM sys.columns c
                    INNER JOIN sys.types t
                        ON c.user_type_id = t.user_type_id
                    LEFT JOIN sys.default_constraints dc
                        ON c.default_object_id = dc.object_id
                    WHERE c.object_id = OBJECT_ID(?)
                    ORDER BY c.column_id
                """
                await cursor.execute(columns_query, (table_name,))
                column_rows = await cursor.fetchall()
                columns = [
                    {
                        "name": row[0],
                        "type": row[1],
                        "nullable": bool(row[2]),
                        "max_length": row[3],
                        "default": row[4]
                    }
                    for row in column_rows
                ]

                # Get primary key information
                pk_query = """
                    SELECT c.name
                    FROM sys.indexes i
                    INNER JOIN sys.index_columns ic
                        ON i.object_id = ic.object_id
                        AND i.index_id = ic.index_id
                    INNER JOIN sys.columns c
                        ON ic.object_id = c.object_id
                        AND ic.column_id = c.column_id
                    WHERE i.object_id = OBJECT_ID(?)
                        AND i.is_primary_key = 1
                """
                await cursor.execute(pk_query, (table_name,))
                pk_rows = await cursor.fetchall()
                primary_keys = {
                    "constrained_columns": [row[0] for row in pk_rows]
                }

                # Get foreign key information
                fk_query = """
                    SELECT
                        fk.name AS constraint_name,
                        COL_NAME(
                            fc.parent_object_id,
                            fc.parent_column_id
                        ) AS column_name,
                        OBJECT_NAME(
                            fc.referenced_object_id
                        ) AS foreign_table_name,
                        COL_NAME(
                            fc.referenced_object_id,
                            fc.referenced_column_id
                        ) AS foreign_column_name
                    FROM sys.foreign_keys fk
                    INNER JOIN sys.foreign_key_columns fc
                        ON fk.object_id = fc.constraint_object_id
                    WHERE fk.parent_object_id = OBJECT_ID(?)
                """
                await cursor.execute(fk_query, (table_name,))
                fk_rows = await cursor.fetchall()
                foreign_keys = [
                    {
                        "name": row[0],
                        "constrained_columns": [row[1]],
                        "referred_table": row[2],
                        "referred_columns": [row[3]]
                    }
                    for row in fk_rows
                ]

                # Get index information
                idx_query = """
                    SELECT
                        i.name AS index_name,
                        c.name AS column_name,
                        i.is_unique
                    FROM sys.indexes i
                    INNER JOIN sys.index_columns ic
                        ON i.object_id = ic.object_id
                        AND i.index_id = ic.index_id
                    INNER JOIN sys.columns c
                        ON ic.object_id = c.object_id
                        AND ic.column_id = c.column_id
                    WHERE i.object_id = OBJECT_ID(?)
                        AND i.is_primary_key = 0
                """
                await cursor.execute(idx_query, (table_name,))
                idx_rows = await cursor.fetchall()
                indexes = [
                    {
                        "name": row[0],
                        "column": row[1],
                        "unique": bool(row[2])
                    }
                    for row in idx_rows
                ]

                return {
                    "table_name": table_name,
                    "columns": columns,
                    "primary_keys": primary_keys,
                    "foreign_keys": foreign_keys,
                    "indexes": indexes,
                }

    async def test_connection(
        self, server_id: str, server_config: MSSQLConfig
    ) -> Dict[str, Any]:
        """
        Test database connection and return connection information.

        Returns:
            Dictionary with connection status and database information
        """
        try:
            pool = await self.get_pool(server_id, server_config)
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    # Execute a simple test query
                    await cursor.execute("SELECT 1")
                    result = await cursor.fetchone()
                    assert result[0] == 1

                    # Get SQL Server version
                    await cursor.execute("SELECT @@VERSION")
                    version_row = await cursor.fetchone()
                    if version_row:
                        version = version_row[0]
                    else:
                        version = "Unknown"

            return {
                "status": "connected",
                "connected": True,
                "db_type": "mssql",
                "database": server_config.database,
                "host": server_config.host,
                "port": server_config.port,
                "pool_size": server_config.pool_size,
                "max_overflow": server_config.max_overflow,
                "version": version,
                "azure_auth": server_config.azure_auth
            }
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return {
                "status": "error",
                "connected": False,
                "db_type": "mssql",
                "database": server_config.database,
                "error": str(e)
            }
