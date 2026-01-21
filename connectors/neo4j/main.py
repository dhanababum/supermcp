"""Neo4j Graph Database MCP Connector - Main Entry Point"""

from mcp_pkg.dynamic_mcp import (
    create_dynamic_mcp,
    get_current_server_id,
    get_current_server_config
)
from typing import Dict, Any, List
import os
import logging

from schema import (
    Neo4jConfig,
    ReadCypherParams,
    WriteCypherParams,
)
from db_manager import DriverManager


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


mcp, app = create_dynamic_mcp(
    name="neo4j",
    config=Neo4jConfig,
    version="1.0.0",
    logo_file_path=os.path.join(
        os.path.dirname(__file__), "media/neo4j-48.png"),
    stateless_http=True,
)

ui_schema = {
    "uri": {
        "ui:widget": "text",
        "ui:placeholder": "bolt://localhost:7687",
        "ui:help": "Neo4j connection URI (bolt:// or neo4j://)",
    },
    "username": {
        "ui:widget": "text",
        "ui:placeholder": "neo4j",
        "ui:help": "Neo4j username for authentication",
    },
    "password": {
        "ui:widget": "password",
        "ui:help": "Neo4j password (will be stored securely)",
    },
    "database": {
        "ui:widget": "text",
        "ui:placeholder": "neo4j",
        "ui:help": "Database name to connect to",
    },
    "read_only": {
        "ui:widget": "checkbox",
        "ui:help": "Enable read-only mode (disables write operations)",
    },
}
mcp.register_ui_schema(ui_schema)

driver_manager: DriverManager = DriverManager()
driver_manager.cleanup_loop()


@mcp.on_server_create()
async def on_server_start(server_id: str, server_config: Neo4jConfig):
    try:
        logger.info(
            f"Initializing Neo4j connection for {server_config.database}"
        )
        await driver_manager.get_driver(server_id, server_config)

        db_name = server_config.db_name or "default"
        mode = "read-only" if server_config.read_only else "read-write"

        logger.info(
            f"Neo4j connection established successfully "
            f"for (db_name: {db_name}, mode: {mode})"
        )

    except Exception as e:
        logger.error(f"Failed to initialize Neo4j connection: {str(e)}")
        raise


@mcp.on_server_destroy()
async def on_server_stop():
    server_id = get_current_server_id()
    await driver_manager.close_driver(server_id)
    logger.info(f"Closing Neo4j connection for server {server_id}")


@mcp.tool()
async def get_neo4j_schema() -> Dict[str, Any]:
    """
    Get the Neo4j database schema including node labels, relationship types,
    and property keys.

    Returns a comprehensive schema with:
    - node_labels: List of all node labels in the database
    - relationship_types: List of all relationship types
    - property_keys: List of all property keys used
    - node_details: Detailed info per label including properties and relationships
    """
    server_id = get_current_server_id()
    server_config = get_current_server_config(app, server_id)
    logger.info(f"Getting schema for server {server_id}")

    return await driver_manager.get_schema(server_id, server_config)


@mcp.tool()
async def read_neo4j_cypher(
    query: str,
    params: Dict[str, Any] | None = None
) -> List[Dict[str, Any]]:
    """
    Execute a read-only Cypher query and return results.

    Use this for MATCH, RETURN, and other read operations.
    Results are returned as a list of dictionaries.

    Args:
        query: Cypher query to execute (e.g., "MATCH (n:Person) RETURN n.name")
        params: Optional parameters for parameterized queries

    Returns:
        List of records as dictionaries
    """
    server_id = get_current_server_id()
    server_config = get_current_server_config(app, server_id)

    validated = ReadCypherParams(query=query, params=params)
    return await driver_manager.execute_read_query(
        server_id, server_config, validated.query, validated.params
    )


@mcp.tool()
async def write_neo4j_cypher(
    query: str,
    params: Dict[str, Any] | None = None
) -> Dict[str, Any]:
    """
    Execute a write Cypher query (CREATE, MERGE, DELETE, SET, etc.).

    This tool is disabled when the connector is in read-only mode.

    Args:
        query: Cypher query to execute (e.g., "CREATE (n:Person {name: $name})")
        params: Optional parameters for parameterized queries

    Returns:
        Summary of changes made (nodes/relationships created/deleted, etc.)
    """
    server_id = get_current_server_id()
    server_config = get_current_server_config(app, server_id)

    validated = WriteCypherParams(query=query, params=params)
    return await driver_manager.execute_write_query(
        server_id, server_config, validated.query, validated.params
    )


@mcp.tool()
async def test_connection() -> Dict[str, Any]:
    """
    Test the Neo4j database connection and return connection status.

    Returns connection details including database type, version, and
    whether read-only mode is enabled.
    """
    server_id = get_current_server_id()
    server_config = get_current_server_config(app, server_id)
    logger.info(
        f"Testing connection for server {server_id}, db: {server_config.database}"
    )
    return await driver_manager.test_connection(server_id, server_config)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8032")),
        reload=False,
        workers=int(os.getenv("WORKERS", "1")),
    )
