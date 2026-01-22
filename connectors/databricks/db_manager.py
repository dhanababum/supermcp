import asyncio
from collections import OrderedDict
import logging
from typing import Any, Dict, Optional, List
from databricks import sql
from databricks.sdk import WorkspaceClient
from databricks.sdk.core import Config
from schema import DatabricksConfig


logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self, global_max_connections=500, per_target_max=20, idle_ttl=300):
        self.global_max = global_max_connections
        self.per_target_max = per_target_max
        self.idle_ttl = idle_ttl
        self.sql_connections = OrderedDict()  # key -> (connection_pool, last_used, conn_count)
        self.workspace_clients = {}  # key -> WorkspaceClient
        self.total_connections = 0
        self.lock = asyncio.Lock()

    def _create_workspace_client(self, server_config: DatabricksConfig) -> WorkspaceClient:
        """Create a WorkspaceClient for Unity Catalog operations"""
        config = Config(
            host=f"https://{server_config.server_hostname}",
            token=server_config.access_token
        )
        return WorkspaceClient(config=config)

    async def get_workspace_client(self, server_id: str, server_config: DatabricksConfig) -> WorkspaceClient:
        """Get or create WorkspaceClient for a server"""
        async with self.lock:
            if server_id not in self.workspace_clients:
                self.workspace_clients[server_id] = self._create_workspace_client(server_config)
            return self.workspace_clients[server_id]

    async def get_sql_connection(self, server_id: str, server_config: DatabricksConfig):
        """Get or create SQL connection for a server"""
        key = server_id
        async with self.lock:
            if key in self.sql_connections:
                conn_pool, _, _ = self.sql_connections.pop(key)
                self.sql_connections[key] = (
                    conn_pool,
                    asyncio.get_event_loop().time(),
                    server_config
                )
                return conn_pool
            
            if self.total_connections + self.per_target_max > self.global_max:
                await self.evict_one()
            
            conn_pool = await asyncio.to_thread(
                self._create_sql_connection,
                server_config
            )
            self.sql_connections[key] = (
                conn_pool,
                asyncio.get_event_loop().time(),
                server_config
            )
            self.total_connections += self.per_target_max
            return conn_pool

    def _create_sql_connection(self, server_config: DatabricksConfig):
        """Create a SQL connection (synchronous)"""
        connection_params = {
            "server_hostname": server_config.server_hostname,
            "http_path": server_config.http_path,
            "access_token": server_config.access_token
        }
        
        # Disable SSL verification if requested
        if not server_config.verify_ssl:
            connection_params["_tls_no_verify"] = True
        return sql.connect(**connection_params)

    async def evict_one(self):
        """Evict least recently used connection"""
        for key, (conn_pool, last_used, _) in list(self.sql_connections.items()):
            await asyncio.to_thread(conn_pool.close)
            self.total_connections -= self.per_target_max
            del self.sql_connections[key]
            return

    async def cleanup_loop(self):
        """Background task to cleanup idle connections"""
        while True:
            await asyncio.sleep(self.idle_ttl / 2)
            now = asyncio.get_event_loop().time()
            async with self.lock:
                for key, (conn_pool, last_used, _) in list(self.sql_connections.items()):
                    if now - last_used > self.idle_ttl:
                        await asyncio.to_thread(conn_pool.close)
                        self.total_connections -= self.per_target_max
                        del self.sql_connections[key]

    async def close_connection(self, server_id: str):
        """Close connections for a server"""
        async with self.lock:
            closed = False
            if server_id in self.sql_connections:
                conn_pool, _, _ = self.sql_connections.pop(server_id)
                await asyncio.to_thread(conn_pool.close)
                self.total_connections -= self.per_target_max
                closed = True
            
            if server_id in self.workspace_clients:
                del self.workspace_clients[server_id]
            
            return closed

    async def execute_query(
        self,
        server_id: str,
        server_config: DatabricksConfig,
        query: str,
        params: Optional[List[Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Execute a SQL query and return results"""
        try:
            connection = await self.get_sql_connection(server_id, server_config)
            
            def _execute():
                with connection.cursor() as cursor:
                    if params:
                        cursor.execute(query, params)
                    else:
                        cursor.execute(query)
                    
                    query_upper = query.strip().upper()
                    is_select = query_upper.startswith('SELECT') or query_upper.startswith('WITH') or query_upper.startswith('SHOW') or query_upper.startswith('DESCRIBE')
                    
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

    async def list_catalogs(
        self,
        server_id: str,
        server_config: DatabricksConfig
    ) -> List[Dict[str, Any]]:
        """List all Unity Catalog catalogs"""
        try:
            client = await self.get_workspace_client(server_id, server_config)
            
            def _list():
                catalogs = []
                for catalog in client.catalogs.list(include_browse=True, max_results=1000):
                    catalogs.append({
                        "name": catalog.name,
                        "owner": catalog.owner,
                        "comment": catalog.comment,
                        "storage_root": catalog.storage_root,
                        "provider_name": catalog.provider_name,
                        "share_name": catalog.share_name,
                    })
                return catalogs
            
            return await asyncio.to_thread(_list)
        except Exception as e:
            logger.error(f"Failed to list catalogs: {str(e)}")
            raise

    async def list_schemas(
        self,
        server_id: str,
        server_config: DatabricksConfig,
        catalog_name: str
    ) -> List[Dict[str, Any]]:
        """List schemas in a catalog"""
        try:
            client = await self.get_workspace_client(server_id, server_config)
            
            def _list():
                schemas = []
                for schema in client.schemas.list(catalog_name=catalog_name, include_browse=True, max_results=1000):
                    schemas.append({
                        "name": schema.name,
                        "full_name": schema.full_name,
                        "catalog_name": schema.catalog_name,
                        "owner": schema.owner,
                        "comment": schema.comment,
                    })
                return schemas
            
            return await asyncio.to_thread(_list)
        except Exception as e:
            logger.error(f"Failed to list schemas: {str(e)}")
            raise

    async def list_tables(
        self,
        server_id: str,
        server_config: DatabricksConfig,
        catalog_name: str,
        schema_name: str
    ) -> List[Dict[str, Any]]:
        """List tables in a catalog.schema"""
        try:
            client = await self.get_workspace_client(server_id, server_config)
            
            def _list():
                tables = []
                for table in client.tables.list(
                    catalog_name=catalog_name,
                    schema_name=schema_name,
                    include_browse=True,
                    max_results=1000
                ):
                    tables.append({
                        "name": table.name,
                        "full_name": table.full_name,
                        "catalog_name": table.catalog_name,
                        "schema_name": table.schema_name,
                        "table_type": table.table_type,
                        "data_source_format": table.data_source_format,
                        "owner": table.owner,
                        "comment": table.comment,
                    })
                return tables
            
            return await asyncio.to_thread(_list)
        except Exception as e:
            logger.error(f"Failed to list tables: {str(e)}")
            raise

    async def get_table_schema(
        self,
        server_id: str,
        server_config: DatabricksConfig,
        catalog_name: str,
        schema_name: str,
        table_name: str
    ) -> Dict[str, Any]:
        """Get detailed schema information for a table"""
        try:
            client = await self.get_workspace_client(server_id, server_config)
            full_name = f"{catalog_name}.{schema_name}.{table_name}"
            
            def _get():
                table = client.tables.get(
                    full_name=full_name,
                    include_browse=True,
                    include_delta_metadata=True
                )
                
                columns = []
                if table.columns:
                    for col in table.columns:
                        columns.append({
                            "name": col.name,
                            "type_name": col.type_name,
                            "type_text": col.type_text,
                            "type_json": col.type_json,
                            "position": col.position,
                            "nullable": col.nullable,
                            "comment": col.comment,
                        })
                
                return {
                    "name": table.name,
                    "full_name": table.full_name,
                    "catalog_name": table.catalog_name,
                    "schema_name": table.schema_name,
                    "table_type": table.table_type,
                    "data_source_format": table.data_source_format,
                    "columns": columns,
                    "owner": table.owner,
                    "comment": table.comment,
                    "storage_location": table.storage_location,
                    "view_definition": table.view_definition,
                }
            
            return await asyncio.to_thread(_get)
        except Exception as e:
            logger.error(f"Failed to get table schema: {str(e)}")
            raise

    async def list_volumes(
        self,
        server_id: str,
        server_config: DatabricksConfig,
        catalog_name: str,
        schema_name: str
    ) -> List[Dict[str, Any]]:
        """List volumes in a catalog.schema"""
        try:
            client = await self.get_workspace_client(server_id, server_config)
            
            def _list():
                volumes = []
                for volume in client.volumes.list(
                    catalog_name=catalog_name,
                    schema_name=schema_name,
                    include_browse=True,
                    max_results=1000
                ):
                    volumes.append({
                        "name": volume.name,
                        "full_name": volume.full_name,
                        "catalog_name": volume.catalog_name,
                        "schema_name": volume.schema_name,
                        "volume_type": volume.volume_type,
                        "owner": volume.owner,
                        "comment": volume.comment,
                        "storage_location": volume.storage_location,
                    })
                return volumes
            
            return await asyncio.to_thread(_list)
        except Exception as e:
            logger.error(f"Failed to list volumes: {str(e)}")
            raise

    async def get_volume_info(
        self,
        server_id: str,
        server_config: DatabricksConfig,
        catalog_name: str,
        schema_name: str,
        volume_name: str
    ) -> Dict[str, Any]:
        """Get detailed information about a volume"""
        try:
            client = await self.get_workspace_client(server_id, server_config)
            full_name = f"{catalog_name}.{schema_name}.{volume_name}"
            
            def _get():
                volume = client.volumes.read(name=full_name, include_browse=True)
                return {
                    "name": volume.name,
                    "full_name": volume.full_name,
                    "catalog_name": volume.catalog_name,
                    "schema_name": volume.schema_name,
                    "volume_type": volume.volume_type,
                    "owner": volume.owner,
                    "comment": volume.comment,
                    "storage_location": volume.storage_location,
                }
            
            return await asyncio.to_thread(_get)
        except Exception as e:
            logger.error(f"Failed to get volume info: {str(e)}")
            raise

    async def list_table_data(
        self,
        server_id: str,
        server_config: DatabricksConfig,
        catalog_name: str,
        schema_name: str,
        table_name: str,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """List data from a table with pagination"""
        try:
            full_name = f"{catalog_name}.{schema_name}.{table_name}"
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

    async def list_volume_data(
        self,
        server_id: str,
        server_config: DatabricksConfig,
        catalog_name: str,
        schema_name: str,
        volume_name: str,
        path: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List files/data in a volume"""
        try:
            volume_path = f"/Volumes/{catalog_name}/{schema_name}/{volume_name}"
            if path:
                volume_path = f"{volume_path}/{path.lstrip('/')}"
            
            query = f"LIST '{volume_path}'"
            rows = await self.execute_query(server_id, server_config, query)
            
            return rows
        except Exception as e:
            logger.error(f"Failed to list volume data: {str(e)}")
            raise

    async def test_connection(
        self,
        server_id: str,
        server_config: DatabricksConfig
    ) -> Dict[str, Any]:
        """Test connection to Databricks"""
        try:
            sql_ok = False
            workspace_ok = False
            
            try:
                connection = await self.get_sql_connection(server_id, server_config)
                def _test_sql():
                    with connection.cursor() as cursor:
                        cursor.execute("SELECT 1")
                        result = cursor.fetchone()
                        return result[0] == 1
                
                sql_ok = await asyncio.to_thread(_test_sql)
            except Exception as e:
                logger.error(f"SQL connection test failed: {str(e)}")
            
            try:
                client = await self.get_workspace_client(server_id, server_config)
                def _test_workspace():
                    list(client.catalogs.list(max_results=1))
                    return True
                
                workspace_ok = await asyncio.to_thread(_test_workspace)
            except Exception as e:
                logger.error(f"WorkspaceClient test failed: {str(e)}")
            
            return {
                "status": "connected" if (sql_ok and workspace_ok) else "partial" if (sql_ok or workspace_ok) else "error",
                "connected": sql_ok and workspace_ok,
                "sql_connection": sql_ok,
                "workspace_client": workspace_ok,
                "server_hostname": server_config.server_hostname,
                "http_path": server_config.http_path,
                "catalog": server_config.catalog,
                "schema": server_config.default_schema,
            }
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return {
                "status": "error",
                "connected": False,
                "error": str(e)
            }
