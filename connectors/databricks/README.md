# Databricks Connector

MCP connector for Databricks with Unity Catalog support, SQL query execution, and volume management.

## Features

- **Unity Catalog Operations**: List and explore catalogs, schemas, tables, and volumes
- **SQL Query Execution**: Execute SQL queries against Databricks SQL warehouses
- **Data Listing**: List table data and volume contents with pagination
- **Connection Management**: Efficient connection pooling for SQL and WorkspaceClient

## Configuration

| Field | Description | Required |
|-------|-------------|----------|
| `server_hostname` | Databricks workspace server hostname (e.g., `adb-1234567890123456.7.azuredatabricks.net`) | Yes |
| `http_path` | HTTP path for SQL warehouse or compute (e.g., `/sql/1.0/warehouses/abc123def456`) | Yes |
| `access_token` | Personal access token for authentication | Yes |
| `catalog` | Default catalog name (optional) | No |
| `default_schema` | Default schema name (optional) | No |
| `warehouse_id` | SQL warehouse ID (optional) | No |
| `pool_size` | Connection pool size for SQL connections (default: 5) | No |
| `verify_ssl` | Verify SSL certificates (default: True, set to False for self-signed certificates) | No |

## Getting Started

### Prerequisites

1. A Databricks workspace with Unity Catalog enabled
2. A SQL warehouse or compute cluster
3. A personal access token with appropriate permissions

### Finding Your Connection Details

1. **Server Hostname**: Found in your Databricks workspace URL
   - Example: `https://adb-1234567890123456.7.azuredatabricks.net`
   - Hostname: `adb-1234567890123456.7.azuredatabricks.net`

2. **HTTP Path**: Found in SQL warehouse connection details
   - Navigate to SQL Warehouses in your workspace
   - Click on your warehouse → Connection details
   - Copy the HTTP path (e.g., `/sql/1.0/warehouses/abc123def456`)

3. **Access Token**: Create a personal access token
   - Go to User Settings → Access Tokens
   - Generate a new token
   - Save it securely (it won't be shown again)

## Tools

### Unity Catalog Tools

#### `list_catalogs`
List all Unity Catalog catalogs visible to the user.

**Returns**: List of catalogs with name, owner, comment, storage_root, and other metadata

**Example**:
```python
catalogs = await list_catalogs()
# Returns: [{"name": "main", "owner": "user@example.com", ...}, ...]
```

#### `list_schemas`
List schemas in a specific catalog.

**Parameters**:
- `catalog_name` (str): Name of the catalog

**Returns**: List of schemas with name, full_name, owner, and other metadata

**Example**:
```python
schemas = await list_schemas(catalog_name="main")
# Returns: [{"name": "default", "full_name": "main.default", ...}, ...]
```

#### `list_tables`
List tables in a catalog.schema.

**Parameters**:
- `catalog_name` (str): Name of the catalog
- `schema_name` (str): Name of the schema

**Returns**: List of tables with name, full_name, table_type, data_source_format, and other metadata

**Example**:
```python
tables = await list_tables(catalog_name="main", schema_name="default")
# Returns: [{"name": "users", "table_type": "MANAGED", ...}, ...]
```

#### `get_table_schema`
Get detailed schema information for a specific table.

**Parameters**:
- `catalog_name` (str): Name of the catalog
- `schema_name` (str): Name of the schema
- `table_name` (str): Name of the table

**Returns**: Dictionary with table schema including columns, types, and metadata

**Example**:
```python
schema = await get_table_schema(
    catalog_name="main",
    schema_name="default",
    table_name="users"
)
# Returns: {
#   "name": "users",
#   "columns": [{"name": "id", "type_name": "INT", ...}, ...],
#   ...
# }
```

#### `list_volumes`
List volumes in a catalog.schema.

**Parameters**:
- `catalog_name` (str): Name of the catalog
- `schema_name` (str): Name of the schema

**Returns**: List of volumes with name, full_name, volume_type, storage_location, and other metadata

**Example**:
```python
volumes = await list_volumes(catalog_name="main", schema_name="default")
# Returns: [{"name": "data", "volume_type": "EXTERNAL", ...}, ...]
```

#### `get_volume_info`
Get detailed information about a specific volume.

**Parameters**:
- `catalog_name` (str): Name of the catalog
- `schema_name` (str): Name of the schema
- `volume_name` (str): Name of the volume

**Returns**: Dictionary with volume information including storage_location and metadata

**Example**:
```python
volume_info = await get_volume_info(
    catalog_name="main",
    schema_name="default",
    volume_name="data"
)
# Returns: {"name": "data", "storage_location": "s3://...", ...}
```

### Query & Data Tools

#### `execute_query`
Execute a SQL query against Databricks SQL warehouse.

**Parameters**:
- `query` (str): SQL query to execute
- `params` (List[Any], optional): Parameters for parameterized queries (use `?` placeholders)

**Returns**: 
- For SELECT queries: List of dictionaries representing rows
- For INSERT/UPDATE/DELETE: List with `affected_rows` count

**Example**:
```python
# Simple query
results = await execute_query("SELECT * FROM main.default.users LIMIT 10")

# Parameterized query
results = await execute_query(
    "SELECT * FROM main.default.users WHERE age > ?",
    params=[18]
)
```

#### `list_table_data`
List data from a table with pagination support.

**Parameters**:
- `catalog_name` (str): Name of the catalog
- `schema_name` (str): Name of the schema
- `table_name` (str): Name of the table
- `limit` (int, optional): Maximum number of rows to return (default: 100)
- `offset` (int, optional): Offset for pagination (default: 0)

**Returns**: Dictionary with rows, count, limit, and offset

**Example**:
```python
data = await list_table_data(
    catalog_name="main",
    schema_name="default",
    table_name="users",
    limit=50,
    offset=0
)
# Returns: {"rows": [...], "count": 50, "limit": 50, "offset": 0}
```

#### `list_volume_data`
List files/data in a volume (directory listing).

**Parameters**:
- `catalog_name` (str): Name of the catalog
- `schema_name` (str): Name of the schema
- `volume_name` (str): Name of the volume
- `path` (str, optional): Path within the volume (defaults to root)

**Returns**: List of files/directories in the volume

**Example**:
```python
files = await list_volume_data(
    catalog_name="main",
    schema_name="default",
    volume_name="data",
    path="raw/"
)
# Returns: [{"path": "raw/file1.csv", "size": 1024, ...}, ...]
```

#### `test_connection`
Test the Databricks connection and return connection status.

**Returns**: Dictionary with connection status, SQL connection status, and WorkspaceClient status

**Example**:
```python
status = await test_connection()
# Returns: {
#   "status": "connected",
#   "connected": True,
#   "sql_connection": True,
#   "workspace_client": True,
#   ...
# }
```

## Example Usage

### Exploring Unity Catalog

```python
# List all catalogs
catalogs = await list_catalogs()

# List schemas in a catalog
schemas = await list_schemas(catalog_name="main")

# List tables in a schema
tables = await list_tables(catalog_name="main", schema_name="default")

# Get table schema
schema = await get_table_schema(
    catalog_name="main",
    schema_name="default",
    table_name="users"
)

# List volumes
volumes = await list_volumes(catalog_name="main", schema_name="default")
```

### Querying Data

```python
# Execute a simple query
results = await execute_query(
    "SELECT COUNT(*) as total FROM main.default.users"
)

# List table data with pagination
page1 = await list_table_data(
    catalog_name="main",
    schema_name="default",
    table_name="users",
    limit=100,
    offset=0
)

page2 = await list_table_data(
    catalog_name="main",
    schema_name="default",
    table_name="users",
    limit=100,
    offset=100
)
```

### Working with Volumes

```python
# List volumes
volumes = await list_volumes(catalog_name="main", schema_name="default")

# Get volume info
volume_info = await get_volume_info(
    catalog_name="main",
    schema_name="default",
    volume_name="data"
)

# List files in a volume
files = await list_volume_data(
    catalog_name="main",
    schema_name="default",
    volume_name="data",
    path="raw/"
)
```

## Permissions

The connector requires appropriate permissions in Databricks:

- **Unity Catalog**: `USE_CATALOG`, `USE_SCHEMA`, `SELECT` (for tables), `READ_VOLUME` (for volumes)
- **SQL Warehouse**: Access to execute queries on the specified warehouse
- **Workspace API**: Access to Unity Catalog APIs

## Error Handling

The connector handles common errors:

- **Authentication failures**: Invalid tokens or expired credentials
- **Permission errors**: Insufficient privileges for operations
- **Connection errors**: Network issues or unavailable warehouses
- **Query errors**: SQL syntax errors or invalid table references

All errors are logged and returned with descriptive error messages.

## Troubleshooting

### SSL Certificate Verification Errors

If you encounter SSL certificate verification errors like:
```
[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: self-signed certificate in certificate chain
```

This typically occurs when:
- Your Databricks workspace uses self-signed certificates
- The certificate chain is incomplete
- Your system's CA trust store doesn't include the required certificates

**Solution**: Set `verify_ssl` to `False` in your connector configuration. This will disable SSL certificate verification.

**Security Warning**: Disabling SSL verification should only be used for development/testing environments. In production, you should:
- Use properly signed certificates
- Add the CA certificate to your system's trust store
- Use the `_tls_trusted_ca_file` parameter with a custom CA bundle

**Example configuration with SSL verification disabled**:
```python
{
    "server_hostname": "your-workspace.cloud.databricks.com",
    "http_path": "/sql/1.0/warehouses/your-warehouse-id",
    "access_token": "your-token",
    "verify_ssl": False  # Only for development/testing
}
```

## Development

### Running Locally

```bash
cd connectors/databricks
uv sync
uv run uvicorn main:app --host 0.0.0.0 --port 8027
```

### Docker Development

```bash
# Build from workspace root
docker build -f connectors/databricks/Dockerfile.dev -t databricks:dev .

# Run container
docker run -p 8027:8027 databricks:dev
```

## Dependencies

- `databricks-sql-connector`: For SQL query execution
- `databricks-sdk`: For Unity Catalog API operations
- `mcp-pkg`: Core MCP framework
- `pydantic`: Configuration models
- `uvicorn`: ASGI server
