import asyncio
from collections import OrderedDict
import logging
from typing import Any, Dict, Optional, List
import snowflake.connector
from schema import SnowflakeConfig


logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self, global_max_connections=500, per_target_max=20, idle_ttl=300):
        self.global_max = global_max_connections
        self.per_target_max = per_target_max
        self.idle_ttl = idle_ttl
        self.connections = OrderedDict()
        self.total_connections = 0
        self.lock = asyncio.Lock()

    def _create_connection(self, server_config: SnowflakeConfig):
        """Create a Snowflake connection (synchronous)"""
        connection_params = {
            "account": server_config.account,
            "user": server_config.user,
            "password": server_config.password,
        }
        
        if server_config.warehouse:
            connection_params["warehouse"] = server_config.warehouse
        if server_config.database:
            connection_params["database"] = server_config.database
        if server_config.schema_name:
            connection_params["schema"] = server_config.schema_name
        if server_config.role:
            connection_params["role"] = server_config.role
            
        return snowflake.connector.connect(**connection_params)

    async def get_connection(self, server_id: str, server_config: SnowflakeConfig):
        """Get or create connection for a server"""
        key = server_id
        async with self.lock:
            if key in self.connections:
                conn, _, _ = self.connections.pop(key)
                self.connections[key] = (
                    conn,
                    asyncio.get_event_loop().time(),
                    server_config
                )
                return conn
            
            if self.total_connections + self.per_target_max > self.global_max:
                await self.evict_one()
            
            conn = await asyncio.to_thread(
                self._create_connection,
                server_config
            )
            self.connections[key] = (
                conn,
                asyncio.get_event_loop().time(),
                server_config
            )
            self.total_connections += self.per_target_max
            return conn

    async def evict_one(self):
        """Evict least recently used connection"""
        for key, (conn, last_used, _) in list(self.connections.items()):
            await asyncio.to_thread(conn.close)
            self.total_connections -= self.per_target_max
            del self.connections[key]
            return

    async def cleanup_loop(self):
        """Background task to cleanup idle connections"""
        while True:
            await asyncio.sleep(self.idle_ttl / 2)
            now = asyncio.get_event_loop().time()
            async with self.lock:
                for key, (conn, last_used, _) in list(self.connections.items()):
                    if now - last_used > self.idle_ttl:
                        await asyncio.to_thread(conn.close)
                        self.total_connections -= self.per_target_max
                        del self.connections[key]

    async def close_connection(self, server_id: str):
        """Close connections for a server"""
        async with self.lock:
            closed = False
            if server_id in self.connections:
                conn, _, _ = self.connections.pop(server_id)
                await asyncio.to_thread(conn.close)
                self.total_connections -= self.per_target_max
                closed = True
            return closed

    async def execute_query(
        self,
        server_id: str,
        server_config: SnowflakeConfig,
        query: str,
        params: Optional[List[Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Execute a SQL query and return results"""
        try:
            connection = await self.get_connection(server_id, server_config)
            
            def _execute():
                with connection.cursor() as cursor:
                    if params:
                        cursor.execute(query, params)
                    else:
                        cursor.execute(query)
                    
                    query_upper = query.strip().upper()
                    is_select = (
                        query_upper.startswith('SELECT') or 
                        query_upper.startswith('WITH') or 
                        query_upper.startswith('SHOW') or 
                        query_upper.startswith('DESCRIBE') or
                        query_upper.startswith('LIST')
                    )
                    
                    if is_select:
                        rows = cursor.fetchall()
                        columns = [desc[0] for desc in cursor.description] if cursor.description else []
                        return [dict(zip(columns, row)) for row in rows]
                    else:
                        return [{"affected_rows": cursor.rowcount if cursor.rowcount else 0}]
            
            return await asyncio.to_thread(_execute)
        except Exception as e:
            logger.error(f"Query execution failed: {str(e)}")
            raise

    async def list_databases(
        self,
        server_id: str,
        server_config: SnowflakeConfig
    ) -> List[Dict[str, Any]]:
        """List all accessible databases"""
        try:
            query = "SHOW DATABASES"
            results = await self.execute_query(server_id, server_config, query)
            
            databases = []
            for row in results:
                databases.append({
                    "name": row.get("name"),
                    "owner": row.get("owner"),
                    "comment": row.get("comment"),
                    "created_on": str(row.get("created_on")) if row.get("created_on") else None,
                    "origin": row.get("origin"),
                })
            return databases
        except Exception as e:
            logger.error(f"Failed to list databases: {str(e)}")
            raise

    async def list_schemas(
        self,
        server_id: str,
        server_config: SnowflakeConfig,
        database_name: str
    ) -> List[Dict[str, Any]]:
        """List schemas in a database"""
        try:
            query = f"SHOW SCHEMAS IN DATABASE {database_name}"
            results = await self.execute_query(server_id, server_config, query)
            
            schemas = []
            for row in results:
                schemas.append({
                    "name": row.get("name"),
                    "database_name": database_name,
                    "owner": row.get("owner"),
                    "comment": row.get("comment"),
                    "created_on": str(row.get("created_on")) if row.get("created_on") else None,
                })
            return schemas
        except Exception as e:
            logger.error(f"Failed to list schemas: {str(e)}")
            raise

    async def list_tables(
        self,
        server_id: str,
        server_config: SnowflakeConfig,
        database_name: str,
        schema_name: str
    ) -> List[Dict[str, Any]]:
        """List tables in a database.schema"""
        try:
            query = f"SHOW TABLES IN {database_name}.{schema_name}"
            results = await self.execute_query(server_id, server_config, query)
            
            tables = []
            for row in results:
                tables.append({
                    "name": row.get("name"),
                    "database_name": database_name,
                    "schema_name": schema_name,
                    "kind": row.get("kind"),
                    "owner": row.get("owner"),
                    "comment": row.get("comment"),
                    "rows": row.get("rows"),
                    "created_on": str(row.get("created_on")) if row.get("created_on") else None,
                })
            return tables
        except Exception as e:
            logger.error(f"Failed to list tables: {str(e)}")
            raise

    async def get_table_schema(
        self,
        server_id: str,
        server_config: SnowflakeConfig,
        database_name: str,
        schema_name: str,
        table_name: str
    ) -> Dict[str, Any]:
        """Get detailed schema information for a table"""
        try:
            query = f"DESCRIBE TABLE {database_name}.{schema_name}.{table_name}"
            results = await self.execute_query(server_id, server_config, query)
            
            columns = []
            for row in results:
                columns.append({
                    "name": row.get("name"),
                    "type": row.get("type"),
                    "kind": row.get("kind"),
                    "nullable": row.get("null?") == "Y",
                    "default": row.get("default"),
                    "primary_key": row.get("primary key") == "Y",
                    "comment": row.get("comment"),
                })
            
            return {
                "name": table_name,
                "database_name": database_name,
                "schema_name": schema_name,
                "full_name": f"{database_name}.{schema_name}.{table_name}",
                "columns": columns,
            }
        except Exception as e:
            logger.error(f"Failed to get table schema: {str(e)}")
            raise

    async def list_warehouses(
        self,
        server_id: str,
        server_config: SnowflakeConfig
    ) -> List[Dict[str, Any]]:
        """List all accessible warehouses"""
        try:
            query = "SHOW WAREHOUSES"
            results = await self.execute_query(server_id, server_config, query)
            
            warehouses = []
            for row in results:
                warehouses.append({
                    "name": row.get("name"),
                    "state": row.get("state"),
                    "size": row.get("size"),
                    "type": row.get("type"),
                    "owner": row.get("owner"),
                    "comment": row.get("comment"),
                })
            return warehouses
        except Exception as e:
            logger.error(f"Failed to list warehouses: {str(e)}")
            raise

    async def list_stages(
        self,
        server_id: str,
        server_config: SnowflakeConfig,
        database_name: str,
        schema_name: str
    ) -> List[Dict[str, Any]]:
        """List stages in a database.schema"""
        try:
            query = f"SHOW STAGES IN {database_name}.{schema_name}"
            results = await self.execute_query(server_id, server_config, query)
            
            stages = []
            for row in results:
                stages.append({
                    "name": row.get("name"),
                    "database_name": database_name,
                    "schema_name": schema_name,
                    "url": row.get("url"),
                    "type": row.get("type"),
                    "owner": row.get("owner"),
                    "comment": row.get("comment"),
                    "created_on": str(row.get("created_on")) if row.get("created_on") else None,
                })
            return stages
        except Exception as e:
            logger.error(f"Failed to list stages: {str(e)}")
            raise

    async def list_table_data(
        self,
        server_id: str,
        server_config: SnowflakeConfig,
        database_name: str,
        schema_name: str,
        table_name: str,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """List data from a table with pagination"""
        try:
            full_name = f"{database_name}.{schema_name}.{table_name}"
            query = f"SELECT * FROM {full_name} LIMIT {limit} OFFSET {offset}"
            
            rows = await self.execute_query(server_id, server_config, query)
            
            return {
                "rows": rows,
                "count": len(rows),
                "limit": limit,
                "offset": offset,
            }
        except Exception as e:
            logger.error(f"Failed to list table data: {str(e)}")
            raise

    async def test_connection(
        self,
        server_id: str,
        server_config: SnowflakeConfig
    ) -> Dict[str, Any]:
        """Test connection to Snowflake"""
        try:
            connection = await self.get_connection(server_id, server_config)
            
            def _test():
                with connection.cursor() as cursor:
                    cursor.execute("SELECT CURRENT_VERSION()")
                    version = cursor.fetchone()[0]
                    
                    cursor.execute("SELECT CURRENT_ACCOUNT()")
                    account = cursor.fetchone()[0]
                    
                    cursor.execute("SELECT CURRENT_USER()")
                    user = cursor.fetchone()[0]
                    
                    cursor.execute("SELECT CURRENT_WAREHOUSE()")
                    warehouse = cursor.fetchone()[0]
                    
                    cursor.execute("SELECT CURRENT_DATABASE()")
                    database = cursor.fetchone()[0]
                    
                    cursor.execute("SELECT CURRENT_SCHEMA()")
                    schema = cursor.fetchone()[0]
                    
                    cursor.execute("SELECT CURRENT_ROLE()")
                    role = cursor.fetchone()[0]
                    
                    return {
                        "version": version,
                        "account": account,
                        "user": user,
                        "warehouse": warehouse,
                        "database": database,
                        "schema": schema,
                        "role": role,
                    }
            
            info = await asyncio.to_thread(_test)
            
            return {
                "status": "connected",
                "connected": True,
                **info
            }
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return {
                "status": "error",
                "connected": False,
                "error": str(e)
            }
