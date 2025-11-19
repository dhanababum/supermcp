# conceptual — not production-ready
import asyncio
from collections import OrderedDict
import logging
from typing import Any, Dict, Optional, List
import asyncpg
from schema import PostgresConfig  # example for Postgres


logger = logging.getLogger(__name__)


class PoolManager:
    def __init__(self, global_max_connections=500, per_target_max=20, idle_ttl=300):
        self.global_max = global_max_connections
        self.per_target_max = per_target_max
        self.idle_ttl = idle_ttl
        self.pools = OrderedDict()   # key -> (pool, last_used, conn_count)
        self.total_connections = 0
        self.lock = asyncio.Lock()
        self._is_sync = True  # Always use sync engine for PostgreSQL

    async def _create_pool(self, server_config: PostgresConfig):
        # Build pool creation parameters
        pool_params = {
            "user": server_config.username,
            "password": server_config.password,
            "database": server_config.database,
            "host": server_config.host,
            "port": server_config.port,
            "min_size": 0,
            "max_size": min(server_config.pool_size, self.per_target_max)
        }
        
        # Add any additional asyncpg-specific parameters if provided
        if server_config.additional_params:
            # Filter out params that asyncpg.create_pool doesn't support
            supported_params = {
                'command_timeout', 'timeout', 'statement_cache_size',
                'max_cached_statement_lifetime', 'max_cacheable_statement_size',
                'server_settings'
            }
            for key, value in server_config.additional_params.items():
                if key in supported_params:
                    pool_params[key] = value
        
        pool = await asyncpg.create_pool(**pool_params)
        return pool

    async def get_pool(self, server_id: str, server_config: PostgresConfig):
        key = server_id
        async with self.lock:
            if key in self.pools:
                pool, _, _, _ = self.pools.pop(key)
                self.pools[key] = (
                    pool,
                    asyncio.get_event_loop().time(),
                    pool._maxsize,
                    server_config
                )
                return pool
            # create pool lazily, but enforce global limits:
            if self.total_connections + self.per_target_max > self.global_max:
                await self.evict_one()
            pool = await self._create_pool(server_config)
            self.pools[key] = (pool, asyncio.get_event_loop().time(), pool._maxsize, server_config)
            self.total_connections += pool._maxsize
            return pool

    async def evict_one(self):
        # evict least recently used idle pool
        for key, (pool, last_used, maxsize, _) in list(self.pools.items()):
            # close the pool
            await pool.close()
            self.total_connections -= maxsize
            del self.pools[key]
            return

    async def cleanup_loop(self):
        while True:
            await asyncio.sleep(self.idle_ttl/2)
            now = asyncio.get_event_loop().time()
            async with self.lock:
                for key, (pool, last_used, maxsize, _) in list(self.pools.items()):
                    if now - last_used > self.idle_ttl:
                        await pool.close()
                        self.total_connections -= maxsize
                        del self.pools[key]

    # close pool based on server_id
    async def close_pool(self, server_id: str):
        async with self.lock:
            if server_id in self.pools:
                pool, _, _, _ = self.pools.pop(server_id)
                await pool.close()
                self.total_connections -= pool._maxsize
                return True
            return False

    async def execute_query(
        self, server_id: str,
        server_config: PostgresConfig,
        query: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> list:
        """
        Execute a SQL query and return results.

        Args:
            query: SQL query to execute
            params: Query parameters (for parameterized queries with $1, $2 syntax)

        Returns:
            List of row dictionaries
        """

        try:
            pool = await self.get_pool(server_id, server_config)
            async with pool.acquire() as conn:
                # Determine if it's a SELECT query
                query_upper = query.strip().upper()
                is_select = query_upper.startswith('SELECT') or query_upper.startswith('WITH')
                
                if is_select:
                    # Execute SELECT query and fetch results
                    if params:
                        # Convert named params to positional if needed
                        rows = await conn.fetch(query, *params.values() if isinstance(params, dict) else params)
                    else:
                        rows = await conn.fetch(query)
                    
                    # Convert asyncpg.Record objects to dictionaries
                    return [dict(row) for row in rows]
                else:
                    # For INSERT/UPDATE/DELETE/CREATE/DROP, execute and return affected rows
                    if params:
                        result = await conn.execute(query, *params.values() if isinstance(params, dict) else params)
                    else:
                        result = await conn.execute(query)
                    
                    # Parse affected rows from result string (e.g., "INSERT 0 5" -> 5)
                    try:
                        parts = result.split()
                        affected_rows = int(parts[-1]) if parts else 0
                    except (ValueError, IndexError):
                        affected_rows = 0
                    
                    return [{"affected_rows": affected_rows}]

        except Exception as e:
            logger.error(f"Query execution failed: {str(e)}")
            raise

    async def get_tables(
        self, server_id: str, server_config: PostgresConfig
    ) -> List[str]:
        """Get list of all tables in the database"""
        pool = await self.get_pool(server_id, server_config)
        async with pool.acquire() as conn:
            # Query information_schema to get table names
            query = """
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """
            rows = await conn.fetch(query)
            return [row['table_name'] for row in rows]

    async def get_table_schema(
        self,
        server_id: str,
        server_config: PostgresConfig,
        table_name: str
    ) -> Dict[str, Any]:
        """Get schema information for a specific table"""
        pool = await self.get_pool(server_id, server_config)
        async with pool.acquire() as conn:
            # Get column information
            columns_query = """
                SELECT 
                    column_name,
                    data_type,
                    is_nullable,
                    column_default,
                    character_maximum_length
                FROM information_schema.columns
                WHERE table_schema = 'public' 
                AND table_name = $1
                ORDER BY ordinal_position
            """
            column_rows = await conn.fetch(columns_query, table_name)
            columns = [
                {
                    "name": row["column_name"],
                    "type": row["data_type"],
                    "nullable": row["is_nullable"] == "YES",
                    "default": row["column_default"],
                    "max_length": row["character_maximum_length"]
                }
                for row in column_rows
            ]
            
            # Get primary key information
            pk_query = """
                SELECT a.attname
                FROM pg_index i
                JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
                WHERE i.indrelid = $1::regclass AND i.indisprimary
            """
            pk_rows = await conn.fetch(pk_query, table_name)
            primary_keys = {"constrained_columns": [row["attname"] for row in pk_rows]}
            
            # Get foreign key information
            fk_query = """
                SELECT
                    tc.constraint_name,
                    kcu.column_name,
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name
                FROM information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                    ON tc.constraint_name = kcu.constraint_name
                JOIN information_schema.constraint_column_usage AS ccu
                    ON ccu.constraint_name = tc.constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_name = $1
            """
            fk_rows = await conn.fetch(fk_query, table_name)
            foreign_keys = [
                {
                    "name": row["constraint_name"],
                    "constrained_columns": [row["column_name"]],
                    "referred_table": row["foreign_table_name"],
                    "referred_columns": [row["foreign_column_name"]]
                }
                for row in fk_rows
            ]
            
            # Get index information
            idx_query = """
                SELECT
                    i.relname AS index_name,
                    a.attname AS column_name,
                    ix.indisunique AS is_unique
                FROM pg_class t
                JOIN pg_index ix ON t.oid = ix.indrelid
                JOIN pg_class i ON i.oid = ix.indexrelid
                JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = ANY(ix.indkey)
                WHERE t.relname = $1
                AND t.relkind = 'r'
            """
            idx_rows = await conn.fetch(idx_query, table_name)
            indexes = [
                {
                    "name": row["index_name"],
                    "column": row["column_name"],
                    "unique": row["is_unique"]
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

    async def test_connection(self, server_id, server_config: PostgresConfig) -> Dict[str, Any]:
        """
        Test database connection and return connection information.

        Returns:
            Dictionary with connection status and database information
        """
        try:
            pool = await self.get_pool(server_id, server_config)
            async with pool.acquire() as conn:
                # Execute a simple test query
                result = await conn.fetchval("SELECT 1")
                assert result == 1

            return {
                "status": "connected",
                "connected": True,
                "db_type": "postgresql",
                "database": server_config.database,
                "host": server_config.host,
                "port": server_config.port,
                "pool_size": server_config.pool_size,
                "max_overflow": server_config.max_overflow,
            }
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return {
                "status": "error",
                "connected": False,
                "db_type": "postgresql",
                "database": server_config.database,
                "error": str(e)
            }
