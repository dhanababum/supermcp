import asyncio
from collections import OrderedDict
import logging
from typing import Any, Dict, Optional, List
from neo4j import AsyncGraphDatabase, AsyncDriver
from schema import Neo4jConfig


logger = logging.getLogger(__name__)


class DriverManager:
    def __init__(
        self,
        global_max_connections=500,
        per_target_max=20,
        idle_ttl=300
    ):
        self.global_max = global_max_connections
        self.per_target_max = per_target_max
        self.idle_ttl = idle_ttl
        self.drivers: OrderedDict[str, tuple] = OrderedDict()
        self.total_connections = 0
        self.lock = asyncio.Lock()

    async def _create_driver(self, server_config: Neo4jConfig) -> AsyncDriver:
        auth = None
        if server_config.username and server_config.password:
            auth = (server_config.username, server_config.password)

        driver = AsyncGraphDatabase.driver(
            server_config.uri,
            auth=auth,
            max_connection_pool_size=self.per_target_max
        )
        return driver

    async def get_driver(
        self, server_id: str, server_config: Neo4jConfig
    ) -> AsyncDriver:
        key = server_id
        async with self.lock:
            if key in self.drivers:
                driver, _, _, _ = self.drivers.pop(key)
                self.drivers[key] = (
                    driver,
                    asyncio.get_event_loop().time(),
                    self.per_target_max,
                    server_config
                )
                return driver

            if self.total_connections + self.per_target_max > self.global_max:
                await self.evict_one()

            driver = await self._create_driver(server_config)
            self.drivers[key] = (
                driver,
                asyncio.get_event_loop().time(),
                self.per_target_max,
                server_config
            )
            self.total_connections += self.per_target_max
            return driver

    async def evict_one(self):
        for key, (driver, last_used, maxsize, _) in list(self.drivers.items()):
            await driver.close()
            self.total_connections -= maxsize
            del self.drivers[key]
            return

    async def cleanup_loop(self):
        while True:
            await asyncio.sleep(self.idle_ttl / 2)
            now = asyncio.get_event_loop().time()
            async with self.lock:
                items = list(self.drivers.items())
                for key, (driver, last_used, maxsize, _) in items:
                    if now - last_used > self.idle_ttl:
                        await driver.close()
                        self.total_connections -= maxsize
                        del self.drivers[key]

    async def close_driver(self, server_id: str):
        async with self.lock:
            if server_id in self.drivers:
                driver, _, maxsize, _ = self.drivers.pop(server_id)
                await driver.close()
                self.total_connections -= maxsize
                return True
            return False

    async def execute_read_query(
        self,
        server_id: str,
        server_config: Neo4jConfig,
        query: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        try:
            driver = await self.get_driver(server_id, server_config)
            async with driver.session(database=server_config.database) as session:
                result = await session.run(query, params or {})
                records = await result.data()
                return records
        except Exception as e:
            logger.error(f"Read query execution failed: {str(e)}")
            raise

    async def execute_write_query(
        self,
        server_id: str,
        server_config: Neo4jConfig,
        query: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if server_config.read_only:
            raise ValueError(
                "Write operations are disabled in read-only mode. "
                "Set read_only=False in configuration to enable writes."
            )

        try:
            driver = await self.get_driver(server_id, server_config)
            async with driver.session(database=server_config.database) as session:
                result = await session.run(query, params or {})
                summary = await result.consume()
                counters = summary.counters

                return {
                    "nodes_created": counters.nodes_created,
                    "nodes_deleted": counters.nodes_deleted,
                    "relationships_created": counters.relationships_created,
                    "relationships_deleted": counters.relationships_deleted,
                    "properties_set": counters.properties_set,
                    "labels_added": counters.labels_added,
                    "labels_removed": counters.labels_removed,
                    "indexes_added": counters.indexes_added,
                    "indexes_removed": counters.indexes_removed,
                    "constraints_added": counters.constraints_added,
                    "constraints_removed": counters.constraints_removed,
                }
        except Exception as e:
            logger.error(f"Write query execution failed: {str(e)}")
            raise

    async def get_schema(
        self,
        server_id: str,
        server_config: Neo4jConfig
    ) -> Dict[str, Any]:
        driver = await self.get_driver(server_id, server_config)
        async with driver.session(database=server_config.database) as session:
            labels_result = await session.run("CALL db.labels() YIELD label RETURN label")
            labels = [record["label"] async for record in labels_result]

            rel_types_result = await session.run(
                "CALL db.relationshipTypes() YIELD relationshipType RETURN relationshipType"
            )
            relationship_types = [
                record["relationshipType"] async for record in rel_types_result
            ]

            props_result = await session.run(
                "CALL db.propertyKeys() YIELD propertyKey RETURN propertyKey"
            )
            property_keys = [record["propertyKey"] async for record in props_result]

            node_details = []
            for label in labels:
                props_query = f"""
                MATCH (n:`{label}`)
                WITH n LIMIT 100
                UNWIND keys(n) AS key
                RETURN DISTINCT key AS property
                """
                props_result = await session.run(props_query)
                properties = [record["property"] async for record in props_result]
                
                rels_query = f"""
                MATCH (n:`{label}`)-[r]->(m)
                RETURN DISTINCT type(r) AS rel_type, labels(m)[0] AS target_label
                LIMIT 50
                """
                rels_result = await session.run(rels_query)
                relationships = [
                    {"type": record["rel_type"], "target": record["target_label"]}
                    async for record in rels_result
                ]

                node_details.append({
                    "label": label,
                    "properties": properties,
                    "outgoing_relationships": relationships
                })

            return {
                "node_labels": labels,
                "relationship_types": relationship_types,
                "property_keys": property_keys,
                "node_details": node_details
            }

    async def test_connection(
        self,
        server_id: str,
        server_config: Neo4jConfig
    ) -> Dict[str, Any]:
        try:
            driver = await self.get_driver(server_id, server_config)
            async with driver.session(database=server_config.database) as session:
                result = await session.run("RETURN 1 AS test")
                record = await result.single()
                assert record["test"] == 1

                version_result = await session.run(
                    "CALL dbms.components() YIELD name, versions "
                    "WHERE name = 'Neo4j Kernel' RETURN versions[0] AS version"
                )
                version_record = await version_result.single()
                version = version_record["version"] if version_record else "Unknown"

            return {
                "status": "connected",
                "connected": True,
                "db_type": "neo4j",
                "database": server_config.database,
                "uri": server_config.uri,
                "version": version,
                "read_only": server_config.read_only
            }
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return {
                "status": "error",
                "connected": False,
                "db_type": "neo4j",
                "database": server_config.database,
                "error": str(e)
            }
