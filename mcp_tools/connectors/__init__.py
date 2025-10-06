from mcp_tools.connectors.sql_db.schema import SqlDbSchema


def get_all_connectors():
    return [{
        "sql_db": {
            "name": "SQL databases",
            "description": "Connect to SQL databases",
            "version": "0.1.0",
            "author": "MCP Tools",
        }
    }]


def get_connector_schema(connector_name: str) -> dict:
    connector_schemas = {
        "sql_db": SqlDbSchema.model_json_schema(),
        "sql_db_mcp": SqlDbSchema.model_json_schema(),
    }
    return connector_schemas.get(connector_name)
