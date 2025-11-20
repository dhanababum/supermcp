# MSSQL/Azure SQL Database MCP Connector

An efficient Model Context Protocol (MCP) connector for Microsoft SQL Server and Azure SQL Database with connection pooling, async operations, and comprehensive database management features.

## Features

- **Multi-Database Support**: Works with both standard SQL Server and Azure SQL Database
- **Async Operations**: Built on `aioodbc` for efficient async database operations
- **Connection Pooling**: Intelligent connection pool management with configurable limits
- **Azure SQL Support**: Built-in support for Azure SQL authentication and SSL/TLS
- **Schema Introspection**: Query table schemas, columns, indexes, and relationships
- **Parameterized Queries**: Safe query execution with parameter binding
- **Query Templates**: Pre-built templates for common SELECT and INSERT operations

## Requirements

- Python >= 3.12.2
- Microsoft ODBC Driver 18 for SQL Server
- UV package manager
- Access to MSSQL or Azure SQL Database

### ODBC Driver Installation

The connector requires Microsoft ODBC Driver 18 for SQL Server. 

**Docker**: The driver is automatically installed in the Docker image.

**Local Development** (Linux/Debian):
```bash
# Add Microsoft repository
curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | \
    gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg

curl -fsSL https://packages.microsoft.com/config/debian/12/prod.list | \
    sudo tee /etc/apt/sources.list.d/mssql-release.list

# Install ODBC Driver
sudo apt-get update
sudo ACCEPT_EULA=Y apt-get install -y msodbcsql18

# Verify installation
odbcinst -q -d -n "ODBC Driver 18 for SQL Server"
```

**macOS**:
```bash
brew tap microsoft/mssql-release
brew install msodbcsql18 mssql-tools18
```

**Verify Installation**:
```bash
# Run verification script
./verify_driver.sh

# Or check manually
odbcinst -q -d
```

## Installation

### Development Setup

1. Install UV package manager:
```bash
pip install uv
```

2. Install dependencies:
```bash
cd connectors/mssql
uv sync
```

### Docker Setup

Build and run using Docker:

```bash
# From workspace root
docker build -f connectors/mssql/Dockerfile.dev -t mssql-connector:dev .

docker run -p 8028:8028 \
  -e PORT=8028 \
  -e WORKERS=1 \
  -e APP_BASE_URL=http://localhost:8000 \
  mssql-connector:dev
```

## Configuration

The connector accepts the following configuration parameters:

**Note**: The connector uses a fixed ODBC driver: **ODBC Driver 18 for SQL Server** (installed in the Docker image).

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `host` | string | - | Database server hostname or Azure SQL endpoint |
| `port` | integer | 1433 | Database port |
| `database` | string | - | Database name |
| `username` | string | - | Database username |
| `password` | string | - | Database password |
| `azure_auth` | boolean | false | Enable Azure SQL authentication |
| `encrypt` | boolean | true | Use encrypted connection |
| `trust_server_certificate` | boolean | false | Trust server certificate |
| `pool_size` | integer | 5 | Number of connections in pool |
| `max_overflow` | integer | 10 | Max additional connections |
| `additional_params` | object | - | Additional ODBC parameters |

### Example Configuration

#### Standard SQL Server

```json
{
  "host": "localhost",
  "port": 1433,
  "database": "my_database",
  "username": "sa",
  "password": "your_password",
  "encrypt": true,
  "trust_server_certificate": true,
  "pool_size": 5,
  "max_overflow": 10
}
```

#### Azure SQL Database

```json
{
  "host": "myserver.database.windows.net",
  "port": 1433,
  "database": "my_azure_db",
  "username": "admin@myserver",
  "password": "your_password",
  "azure_auth": false,
  "encrypt": true,
  "trust_server_certificate": false,
  "pool_size": 10,
  "max_overflow": 20
}
```

## Available Tools

### `list_tables()`
List all tables in the database.

**Returns**: List of table names

### `get_table_schema(table_name: str)`
Get detailed schema information for a specific table.

**Parameters**:
- `table_name`: Name of the table to inspect

**Returns**: Schema object with columns, primary keys, foreign keys, and indexes

### `execute_query(query: str, params: dict = None)`
Execute any SQL query with optional parameters.

**Parameters**:
- `query`: SQL query to execute
- `params`: Optional dictionary of query parameters

**Returns**: 
- For SELECT: List of row dictionaries
- For INSERT/UPDATE/DELETE: Affected rows count

### `test_connection()`
Test database connectivity and return connection information.

**Returns**: Connection status and server details

## Available Templates

### `select_query`
Execute SELECT queries with automatic row limiting.

**Parameters**:
- `sql_query`: SQL SELECT statement
- `limit`: Maximum rows to return (default: 2)

### `insert_query`
Generate and execute INSERT statements.

**Parameters**:
- `table_name`: Target table name
- `columns`: Comma-separated column names
- `values`: Comma-separated values

## Usage Examples

### Query Execution

```python
# Execute a SELECT query
results = await execute_query(
    "SELECT TOP 10 * FROM users WHERE status = ?",
    params={"status": "active"}
)

# Execute an INSERT
result = await execute_query(
    "INSERT INTO users (name, email) VALUES (?, ?)",
    params={"name": "John Doe", "email": "john@example.com"}
)
```

### Schema Inspection

```python
# Get table schema
schema = await get_table_schema("users")
print(f"Columns: {schema['columns']}")
print(f"Primary Keys: {schema['primary_keys']}")
print(f"Foreign Keys: {schema['foreign_keys']}")
```

## Architecture

### Connection Pool Management

The connector uses an efficient connection pool with the following features:

- **Global Connection Limit**: Prevents overwhelming the database server
- **Per-Target Limits**: Manages connections per database instance
- **Idle Connection Cleanup**: Automatically closes unused connections
- **LRU Eviction**: Least recently used pools are evicted when limits are reached

### Async Operations

All database operations are fully async using `aioodbc`, providing:
- Non-blocking I/O
- High concurrency
- Efficient resource utilization

## Performance Considerations

1. **Connection Pooling**: Reuses connections to avoid overhead
2. **Parameterized Queries**: Prevents SQL injection and improves query planning
3. **Efficient Schema Queries**: Uses SQL Server system catalog views
4. **Configurable Pool Sizes**: Tune based on workload requirements

## Security

- **Encrypted Connections**: SSL/TLS support for secure communication
- **Parameterized Queries**: Protection against SQL injection
- **Azure SQL Support**: Compatible with Azure SQL security features
- **Certificate Validation**: Configurable server certificate validation

## Troubleshooting

### Connection Issues

1. Verify ODBC driver is installed: `odbcinst -q -d`
2. Check network connectivity to SQL Server
3. Verify firewall rules allow connections on port 1433
4. For Azure SQL, ensure client IP is whitelisted

### Performance Issues

1. Increase `pool_size` for high-concurrency workloads
2. Use query templates for frequently executed queries
3. Monitor connection pool usage via `test_connection()`

## Development

### Running Tests

```bash
# Run all tests
./run_tests.sh

# Or using pytest directly
uv run pytest -v
```

### Code Style

The project follows PEP 8 with:
- Maximum line length: 79 characters
- Type hints for all public functions
- Comprehensive docstrings

## License

See workspace LICENSE file for details.

## Support

For issues and questions, please refer to the main project repository.

