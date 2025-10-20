# Tenants SQL Database Connector - Architecture & Design

## Overview

The Tenants SQL Database Connector is a robust, production-ready MCP connector that enables multi-tenant database access across multiple database platforms. It follows enterprise-grade design patterns and leverages SQLAlchemy 2.0 for modern database interactions.

## Architecture Components

### 1. Database Connection Manager (`db_manager.py`)

**Purpose**: Centralized database connection management with support for multiple database types.

**Key Features**:
- **Factory Pattern**: Dynamic connection URL building based on database type
- **Connection Pooling**: Configurable pool sizes with QueuePool for production databases
- **Lifecycle Management**: Proper connection initialization and cleanup
- **Type Safety**: Enum-based database type validation

**Supported Databases**:
```python
class DatabaseType(str, Enum):
    SQLITE = "sqlite"
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    MSSQL = "mssql"
    ORACLE = "oracle"
    SNOWFLAKE = "snowflake"
```

**Design Patterns Used**:

1. **Builder Pattern** (`_build_connection_url`):
   - Constructs database-specific connection URLs
   - Handles default ports and driver specifications
   - Supports additional parameters for advanced configurations

2. **Strategy Pattern** (Connection Pooling):
   - NullPool for SQLite (doesn't support pooling well)
   - QueuePool for other databases (production-grade pooling)

3. **Resource Management**:
   - Automatic connection testing with `pool_pre_ping=True`
   - Graceful disconnect with engine disposal
   - Connection state tracking with `is_connected` property

### 2. MCP Server Implementation (`main.py`)

**Purpose**: MCP server entry point with tool and template definitions.

**Key Components**:

#### Configuration Model
```python
class TenantSqlDbConfig(BaseModel):
    db_type: DatabaseType
    host: Optional[str]
    port: Optional[int]
    database: str
    username: Optional[str]
    password: Optional[str]
    pool_size: int = 5
    max_overflow: int = 10
    additional_params: Optional[Dict[str, Any]]
```

#### Lifecycle Hooks

**Server Start** (`@mcp.on_server_start()`):
```python
async def on_server_start(config: TenantSqlDbConfig):
    # 1. Initialize DatabaseConnectionManager
    # 2. Establish connection with provided config
    # 3. Verify connection is active
```

**Server Stop** (`@mcp.on_server_stop()`):
```python
async def on_server_stop():
    # 1. Close active connections
    # 2. Dispose of SQLAlchemy engine
    # 3. Clean up resources
```

**Benefits**:
- Automatic connection setup when server is created
- Automatic cleanup when server is deleted
- No manual connection management required

#### MCP Tools

**1. `execute_query`**
- Purpose: Execute any SQL query with optional parameters
- Use Case: Custom queries, data retrieval, DML operations
- Safety: Supports parameterized queries to prevent SQL injection

**2. `list_tables`**
- Purpose: Schema discovery
- Use Case: Explore database structure
- Implementation: Uses SQLAlchemy's `inspect()` API

**3. `get_table_schema`**
- Purpose: Detailed table metadata
- Use Case: Understanding table structure before querying
- Returns: Columns, primary keys, foreign keys, indexes

**4. `test_connection`**
- Purpose: Connection health check
- Use Case: Verify connectivity before operations
- Returns: Status and database type information

#### MCP Templates

**1. `select_query`**
```python
@mcp.template(name="select_query", params_model=SelectQueryTemplate)
```
- Generates SELECT statements
- Supports column selection, WHERE clauses, LIMIT
- Dynamic parameter substitution

**2. `insert_query`**
```python
@mcp.template(name="insert_query", params_model=InsertQueryTemplate)
```
- Generates INSERT statements
- Supports parameterized values
- Safe for prepared statements

**3. `execute_query`**
```python
@mcp.template(name="execute_query", params_model=ExecuteQueryParams)
```
- Custom query template with parameter substitution
- Flexible for complex operations

## Design Patterns Summary

### 1. **Singleton Pattern**
The global `db_manager` instance ensures one connection per server:
```python
db_manager: Optional[DatabaseConnectionManager] = None
```

**Benefits**:
- Single connection pool per server instance
- Resource efficiency
- Thread-safe operations with SQLAlchemy

### 2. **Dependency Injection**
Configuration is injected through Pydantic models:
```python
@mcp.on_server_start()
async def on_server_start(config: TenantSqlDbConfig):
    # Configuration automatically validated and injected
```

**Benefits**:
- Type safety with Pydantic validation
- Clear configuration contracts
- Easy testing with mock configs

### 3. **Factory Pattern**
Database-specific connection logic is centralized:
```python
def _build_connection_url(self) -> str:
    if self.db_type == DatabaseType.SQLITE:
        return f"sqlite:///{self.database}"
    elif self.db_type == DatabaseType.POSTGRESQL:
        # ... PostgreSQL-specific logic
```

**Benefits**:
- Easy to add new database types
- Consistent interface across databases
- Encapsulated database-specific details

### 4. **Template Method Pattern**
Query templates provide reusable query structures:
```python
@mcp.template(name="select_query", params_model=SelectQueryTemplate)
def select_query_template(params: SelectQueryTemplate, **kwargs) -> str:
    # Build query from template
```

**Benefits**:
- Reusable query patterns
- Reduced code duplication
- Consistent query structure

### 5. **Strategy Pattern**
Different pooling strategies based on database type:
```python
if self.db_type == DatabaseType.SQLITE:
    poolclass=NullPool  # No pooling for SQLite
else:
    # QueuePool for production databases
```

**Benefits**:
- Optimized for each database type
- Configurable pool parameters
- Production-grade connection management

## Connection Lifecycle

```
1. User Creates Server via Platform
   ↓
2. Platform sends TenantSqlDbConfig
   ↓
3. on_server_start() hook triggered
   ↓
4. DatabaseConnectionManager initialized
   ↓
5. Connection established with SQLAlchemy
   ↓
6. Tools available for use
   ↓
7. User deletes server
   ↓
8. on_server_stop() hook triggered
   ↓
9. Connection closed, resources cleaned up
```

## Security Considerations

### 1. **Parameterized Queries**
All query execution supports parameters:
```python
execute_query(
    query="SELECT * FROM users WHERE id = :user_id",
    params={"user_id": 123}
)
```

### 2. **Credential Management**
- Credentials stored in connector configuration
- Not exposed in tool responses
- Secured by platform's encryption

### 3. **Connection Pooling**
- Limits concurrent connections
- Prevents resource exhaustion
- Configurable based on database capacity

### 4. **Error Handling**
- Detailed error messages for debugging
- No sensitive data in error responses
- Proper exception catching and logging

## Performance Optimizations

### 1. **Connection Pooling**
```python
create_engine(
    url,
    pool_size=5,           # Number of persistent connections
    max_overflow=10,       # Additional connections when needed
    pool_timeout=30,       # Wait time for available connection
    pool_pre_ping=True     # Verify connection before use
)
```

### 2. **Connection Reuse**
- Single engine per server instance
- Pooled connections for multiple requests
- Automatic connection health checking

### 3. **Lazy Initialization**
- Connection only established when server starts
- No overhead for inactive servers
- Clean resource disposal on shutdown

## Extension Points

### Adding New Database Types

1. Add to `DatabaseType` enum:
```python
class DatabaseType(str, Enum):
    # ... existing types
    NEWDB = "newdb"
```

2. Add URL builder logic:
```python
def _build_connection_url(self) -> str:
    # ... existing logic
    elif self.db_type == DatabaseType.NEWDB:
        return f"newdb://{self.username}:{self.password}@{self.host}"
```

3. Update dependencies in `pyproject.toml`:
```toml
[project.optional-dependencies]
newdb = ["newdb-driver>=1.0.0"]
```

### Adding New Tools

```python
@mcp.tool()
def new_tool(param: str) -> str:
    """Tool description"""
    if not db_manager or not db_manager.is_connected:
        return "Error: Database not connected"
    # Tool implementation
```

### Adding New Templates

```python
class NewTemplateParams(BaseModel):
    field: str = Field(description="Field description")

@mcp.template(name="new_template", params_model=NewTemplateParams)
def new_template(params: NewTemplateParams, **kwargs) -> str:
    # Template implementation
```

## Testing Strategy

### Unit Tests
- Test DatabaseConnectionManager with mock engines
- Test URL building for each database type
- Test connection lifecycle

### Integration Tests
- Test actual database connections (SQLite for CI)
- Test query execution
- Test schema inspection

### End-to-End Tests
- Test server creation through platform
- Test tool invocation
- Test template rendering

## Monitoring & Logging

All operations are logged:
```python
logger.info(f"Successfully connected to {self.db_type} database")
logger.error(f"Query execution failed: {str(e)}")
```

**Log Levels**:
- INFO: Connection events, successful operations
- ERROR: Connection failures, query errors
- DEBUG: Detailed execution information (when enabled)

## Best Practices Implemented

1. ✅ **Type Safety**: Pydantic models for all configurations
2. ✅ **Error Handling**: Comprehensive try-catch blocks
3. ✅ **Resource Management**: Proper cleanup with lifecycle hooks
4. ✅ **Security**: Parameterized queries, credential protection
5. ✅ **Performance**: Connection pooling, reuse
6. ✅ **Maintainability**: Clear separation of concerns
7. ✅ **Extensibility**: Easy to add new databases and tools
8. ✅ **Documentation**: Comprehensive README and examples

## Comparison with cc.py Example

| Feature | cc.py | tenants_sqldb |
|---------|-------|---------------|
| Database Support | Single config example | 6 database types |
| Connection Management | Not implemented | Full lifecycle |
| Connection Pooling | N/A | Configurable pools |
| Schema Inspection | No | Yes (tables, columns, keys) |
| Query Templates | Basic | 3 templates |
| Error Handling | Basic | Comprehensive |
| Type Safety | Basic | Full Pydantic |
| Documentation | Minimal | Complete |

## Conclusion

The Tenants SQL Database Connector demonstrates enterprise-grade design:
- **Scalable**: Supports multiple database types and tenants
- **Maintainable**: Clear architecture with separation of concerns
- **Secure**: Parameterized queries and credential protection
- **Performant**: Connection pooling and resource optimization
- **Extensible**: Easy to add new databases and features

This implementation can serve as a reference for building other connectors in the platform.

