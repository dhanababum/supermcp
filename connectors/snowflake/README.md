# Snowflake Connector

MCP connector for Snowflake with database exploration, SQL query execution, and stage management.

## Features

- **Database Operations**: List and explore databases, schemas, tables, and stages
- **SQL Query Execution**: Execute SQL queries against Snowflake warehouses
- **Data Listing**: List table data with pagination
- **Connection Management**: Efficient connection pooling

## Configuration

| Field | Description | Required |
|-------|-------------|----------|
| `account` | Snowflake account identifier (e.g., `xy12345.us-east-1` or `myorg-myaccount`) | Yes |
| `user` | Snowflake username for authentication | Yes |
| `password` | Snowflake password for authentication | Yes |
| `warehouse` | Snowflake compute warehouse name (e.g., `COMPUTE_WH`) | No |
| `database` | Default database name (optional) | No |
| `schema_name` | Default schema name (optional) | No |
| `role` | Snowflake role for access control (optional) | No |
| `pool_size` | Connection pool size (default: 5) | No |

## Getting Started

### Prerequisites

1. A Snowflake account
2. A compute warehouse
3. User credentials with appropriate permissions

### Finding Your Connection Details

1. **Account Identifier**: Found in your Snowflake URL
   - Example: `https://xy12345.us-east-1.snowflakecomputing.com`
   - Account: `xy12345.us-east-1`
   - For organizations: `myorg-myaccount`

2. **Warehouse**: Navigate to Admin > Warehouses in Snowflake
   - Copy the warehouse name (e.g., `COMPUTE_WH`)

3. **User/Password**: Your Snowflake login credentials

## Tools

### Database Exploration Tools

#### `list_databases`
List all accessible databases in the Snowflake account.

**Returns**: List of databases with name, owner, comment, and metadata

**Example**:
```python
databases = await list_databases()
# Returns: [{"name": "MY_DATABASE", "owner": "ACCOUNTADMIN", ...}, ...]
```

#### `list_schemas`
List schemas in a specific database.

**Parameters**:
- `database_name` (str): Name of the database

**Returns**: List of schemas with name, owner, and metadata

**Example**:
```python
schemas = await list_schemas(database_name="MY_DATABASE")
# Returns: [{"name": "PUBLIC", "database_name": "MY_DATABASE", ...}, ...]
```

#### `list_tables`
List tables in a database.schema.

**Parameters**:
- `database_name` (str): Name of the database
- `schema_name` (str): Name of the schema

**Returns**: List of tables with name, kind, owner, rows count, and metadata

**Example**:
```python
tables = await list_tables(database_name="MY_DATABASE", schema_name="PUBLIC")
# Returns: [{"name": "USERS", "kind": "TABLE", "rows": 1000, ...}, ...]
```

#### `get_table_schema`
Get detailed schema information for a specific table.

**Parameters**:
- `database_name` (str): Name of the database
- `schema_name` (str): Name of the schema
- `table_name` (str): Name of the table

**Returns**: Dictionary with table schema including columns, types, and metadata

**Example**:
```python
schema = await get_table_schema(
    database_name="MY_DATABASE",
    schema_name="PUBLIC",
    table_name="USERS"
)
# Returns: {
#   "name": "USERS",
#   "columns": [{"name": "ID", "type": "NUMBER", ...}, ...],
#   ...
# }
```

#### `list_warehouses`
List all accessible warehouses in the Snowflake account.

**Returns**: List of warehouses with name, state, size, type, and metadata

**Example**:
```python
warehouses = await list_warehouses()
# Returns: [{"name": "COMPUTE_WH", "state": "STARTED", "size": "X-Small", ...}, ...]
```

#### `list_stages`
List stages in a database.schema.

**Parameters**:
- `database_name` (str): Name of the database
- `schema_name` (str): Name of the schema

**Returns**: List of stages with name, url, type, and metadata

**Example**:
```python
stages = await list_stages(database_name="MY_DATABASE", schema_name="PUBLIC")
# Returns: [{"name": "MY_STAGE", "type": "INTERNAL", ...}, ...]
```

### Query & Data Tools

#### `execute_query`
Execute a SQL query against Snowflake.

**Parameters**:
- `query` (str): SQL query to execute
- `params` (List[Any], optional): Parameters for parameterized queries (use `%s` placeholders)

**Returns**: 
- For SELECT queries: List of dictionaries representing rows
- For INSERT/UPDATE/DELETE: List with `affected_rows` count

**Example**:
```python
# Simple query
results = await execute_query("SELECT * FROM MY_DATABASE.PUBLIC.USERS LIMIT 10")

# Parameterized query
results = await execute_query(
    "SELECT * FROM MY_DATABASE.PUBLIC.USERS WHERE AGE > %s",
    params=[18]
)
```

#### `list_table_data`
List data from a table with pagination support.

**Parameters**:
- `database_name` (str): Name of the database
- `schema_name` (str): Name of the schema
- `table_name` (str): Name of the table
- `limit` (int, optional): Maximum number of rows to return (default: 100)
- `offset` (int, optional): Offset for pagination (default: 0)

**Returns**: Dictionary with rows, count, limit, and offset

**Example**:
```python
data = await list_table_data(
    database_name="MY_DATABASE",
    schema_name="PUBLIC",
    table_name="USERS",
    limit=50,
    offset=0
)
# Returns: {"rows": [...], "count": 50, "limit": 50, "offset": 0}
```

#### `test_connection`
Test the Snowflake connection and return connection status.

**Returns**: Dictionary with connection status and session information

**Example**:
```python
status = await test_connection()
# Returns: {
#   "status": "connected",
#   "connected": True,
#   "version": "8.10.0",
#   "account": "xy12345",
#   "user": "MY_USER",
#   "warehouse": "COMPUTE_WH",
#   ...
# }
```

## Example Usage

### Exploring Databases

```python
# List all databases
databases = await list_databases()

# List schemas in a database
schemas = await list_schemas(database_name="MY_DATABASE")

# List tables in a schema
tables = await list_tables(database_name="MY_DATABASE", schema_name="PUBLIC")

# Get table schema
schema = await get_table_schema(
    database_name="MY_DATABASE",
    schema_name="PUBLIC",
    table_name="USERS"
)

# List warehouses
warehouses = await list_warehouses()
```

### Querying Data

```python
# Execute a simple query
results = await execute_query(
    "SELECT COUNT(*) as total FROM MY_DATABASE.PUBLIC.USERS"
)

# List table data with pagination
page1 = await list_table_data(
    database_name="MY_DATABASE",
    schema_name="PUBLIC",
    table_name="USERS",
    limit=100,
    offset=0
)

page2 = await list_table_data(
    database_name="MY_DATABASE",
    schema_name="PUBLIC",
    table_name="USERS",
    limit=100,
    offset=100
)
```

### Working with Stages

```python
# List stages
stages = await list_stages(database_name="MY_DATABASE", schema_name="PUBLIC")

# List files in a stage
files = await execute_query("LIST @MY_DATABASE.PUBLIC.MY_STAGE")
```

## Permissions

The connector requires appropriate permissions in Snowflake:

- **Database**: `USAGE` on databases
- **Schema**: `USAGE` on schemas
- **Table**: `SELECT` on tables
- **Warehouse**: `USAGE` on warehouses
- **Stage**: `READ` on stages

## Error Handling

The connector handles common errors:

- **Authentication failures**: Invalid credentials
- **Permission errors**: Insufficient privileges for operations
- **Connection errors**: Network issues or unavailable warehouses
- **Query errors**: SQL syntax errors or invalid object references

All errors are logged and returned with descriptive error messages.

## Development

### Running Locally

```bash
cd connectors/snowflake
uv sync
uv run uvicorn main:app --host 0.0.0.0 --port 8034
```

### Docker Development

```bash
# Build from workspace root
docker build -f connectors/snowflake/Dockerfile.dev -t snowflake:dev .

# Run container
docker run -p 8034:8034 -e PORT=8034 -e WORKERS=1 -e APP_BASE_URL=http://localhost:8000 snowflake:dev
```

## Dependencies

- `snowflake-connector-python`: For Snowflake connectivity
- `mcp-pkg`: Core MCP framework
- `pydantic`: Configuration models
- `uvicorn`: ASGI server
