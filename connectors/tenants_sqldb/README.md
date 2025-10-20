# Tenants SQL Database MCP Connector

A multi-tenant SQL database connector for the MCP (Model Context Protocol) platform. This connector supports multiple database types and provides a unified interface for database operations.

## Features

- **Multi-Database Support**: Connect to SQLite, PostgreSQL, MySQL, MSSQL, Oracle, and Snowflake
- **SQLAlchemy 2.0**: Built on the latest SQLAlchemy with modern async patterns
- **Connection Pooling**: Efficient connection management with configurable pool sizes
- **Server Lifecycle Management**: Automatic connection initialization and cleanup
- **Schema Inspection**: Query table schemas, columns, indexes, and relationships
- **Template System**: Pre-built query templates for common operations
- **Type Safety**: Full Pydantic validation for all configurations

## Supported Databases

| Database | Type Value | Default Port | Required Packages |
|----------|-----------|--------------|-------------------|
| SQLite | `sqlite` | N/A | Built-in |
| PostgreSQL | `postgresql` | 5432 | `psycopg2-binary` |
| MySQL | `mysql` | 3306 | `pymysql` |
| MSSQL | `mssql` | 1433 | `pyodbc` |
| Oracle | `oracle` | 1521 | `cx_oracle` |
| Snowflake | `snowflake` | N/A | `snowflake-sqlalchemy` |

## Installation

### Base Installation
```bash
cd connectors/tenants_sqldb
pip install -e .
```

### Database-Specific Drivers

Install drivers for the databases you plan to use:

```bash
# PostgreSQL
pip install -e ".[postgresql]"

# MySQL
pip install -e ".[mysql]"

# All databases
pip install -e ".[all]"
```

## Configuration

When creating a server through the MCP platform, provide the following configuration:

### SQLite Example
```json
{
  "db_type": "sqlite",
  "database": "/path/to/database.db"
}
```

### PostgreSQL Example
```json
{
  "db_type": "postgresql",
  "host": "localhost",
  "port": 5432,
  "database": "mydb",
  "username": "user",
  "password": "password",
  "pool_size": 5,
  "max_overflow": 10
}
```

### MySQL Example
```json
{
  "db_type": "mysql",
  "host": "localhost",
  "port": 3306,
  "database": "mydb",
  "username": "user",
  "password": "password",
  "additional_params": {
    "driver": "pymysql"
  }
}
```

### Snowflake Example
```json
{
  "db_type": "snowflake",
  "host": "account.snowflakecomputing.com",
  "database": "mydb",
  "username": "user",
  "password": "password",
  "additional_params": {
    "account": "account",
    "warehouse": "my_warehouse",
    "schema": "public"
  }
}
```

## Available Tools

### `execute_query`
Execute any SQL query with optional parameterized queries.

**Parameters:**
- `query` (str): SQL query to execute
- `params` (dict, optional): Parameters for parameterized queries

**Example:**
```python
execute_query(
    query="SELECT * FROM users WHERE age > :age",
    params={"age": 18}
)
```

### `list_tables`
List all tables in the connected database.

**Returns:** List of table names

### `get_table_schema`
Get detailed schema information for a specific table.

**Parameters:**
- `table_name` (str): Name of the table to inspect

**Returns:** Schema information including columns, primary keys, foreign keys, and indexes

### `test_connection`
Test if the database connection is active and responsive.

**Returns:** Connection status message

## Available Templates

### `select_query`
Generate SELECT queries with filtering and limiting.

**Parameters:**
- `table_name` (str): Table to query
- `columns` (str): Columns to select (default: "*")
- `where_clause` (str, optional): WHERE clause without the WHERE keyword
- `limit` (int, optional): Limit number of results

**Example:**
```python
select_query_template(
    table_name="users",
    columns="id, name, email",
    where_clause="age > 18",
    limit=100
)
# Output: SELECT id, name, email FROM users WHERE age > 18 LIMIT 100
```

### `insert_query`
Generate INSERT queries.

**Parameters:**
- `table_name` (str): Table to insert into
- `columns` (str): Column names (comma-separated)
- `values` (str): Values to insert

**Example:**
```python
insert_query_template(
    table_name="users",
    columns="name, email, age",
    values=":name, :email, :age"
)
# Output: INSERT INTO users (name, email, age) VALUES (:name, :email, :age)
```

### `execute_query`
Template for executing custom queries with parameter substitution.

**Parameters:**
- `query` (str): SQL query with placeholders
- `params` (dict, optional): Parameters for query

## Architecture & Design Patterns

### 1. **Connection Manager Pattern**
The `DatabaseConnectionManager` class encapsulates all database-specific logic:
- Connection URL building for different database types
- Connection pooling configuration
- Lifecycle management (connect/disconnect)
- Query execution with error handling

### 2. **Factory Pattern**
Connection URLs are built using a factory method pattern, supporting multiple database types through a unified interface.

### 3. **Dependency Injection**
The MCP server receives configuration through Pydantic models, ensuring type safety and validation.

### 4. **Lifecycle Hooks**
- `@mcp.on_server_start()`: Initialize database connection when server starts
- `@mcp.on_server_stop()`: Clean up connections when server stops

### 5. **Singleton Pattern**
The global `db_manager` instance ensures a single connection per server instance.

## Development

### Running Locally
```bash
cd connectors/tenants_sqldb
python main.py
```

The server will start on `http://localhost:8026`

### Environment Variables
```bash
export API_BASE_URL="http://localhost:9001"
export API_WEB_URL="http://localhost:3000"
export CONNECTOR_SECRET="your-secret"
export CONNECTOR_ID="your-connector-id"
```

## Best Practices

1. **Connection Pooling**: Configure `pool_size` and `max_overflow` based on your workload
2. **Parameterized Queries**: Always use parameterized queries to prevent SQL injection
3. **Connection Testing**: Use `test_connection` tool to verify connectivity before operations
4. **Schema Inspection**: Use `get_table_schema` to understand table structure before querying
5. **Error Handling**: All tools return descriptive error messages for debugging

## Security Considerations

- Credentials are stored securely in the connector configuration
- Use environment variables for sensitive data in development
- Parameterized queries prevent SQL injection attacks
- Connection pooling limits resource consumption

## Troubleshooting

### Connection Issues
1. Verify database credentials
2. Check network connectivity to database host
3. Ensure required driver packages are installed
4. Use `test_connection` tool to diagnose issues

### Query Failures
1. Check SQL syntax for your specific database type
2. Verify table and column names exist
3. Review parameter types and values
4. Check database permissions for the user

## License

See main project LICENSE file.

