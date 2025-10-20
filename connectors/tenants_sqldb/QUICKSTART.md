# Quick Start Guide - Tenants SQL Database Connector

This guide will help you get started with the Tenants SQL Database Connector in under 5 minutes.

## Step 1: Installation

### Install Base Connector
```bash
cd /Users/dhanababu/workspace/forge-mcptools/connectors/tenants_sqldb
pip install -e .
```

### Install Database Drivers

Choose the database(s) you need:

```bash
# For PostgreSQL
pip install -e ".[postgresql]"

# For MySQL
pip install -e ".[mysql]"

# For all databases
pip install -e ".[all]"
```

## Step 2: Run the Connector Locally (Optional)

```bash
# Set environment variables
export API_BASE_URL="http://localhost:9001"
export API_WEB_URL="http://localhost:3000"
export CONNECTOR_SECRET="your-connector-secret"
export CONNECTOR_ID="your-connector-id"

# Run the server
python main.py
```

The connector will start on `http://localhost:8026`

## Step 3: Register Connector in Platform

1. Navigate to the MCP platform web interface
2. Go to **Connectors** section
3. Click **Add Connector**
4. Upload or link to this connector
5. Save the connector

## Step 4: Create a Server

### Example: SQLite Server

1. Navigate to **Servers** → **Create New Server**
2. Select **tenants_sqldb** connector
3. Configure:
```json
{
  "db_type": "sqlite",
  "database": "/path/to/your/database.db"
}
```
4. Click **Create Server**

### Example: PostgreSQL Server

1. Navigate to **Servers** → **Create New Server**
2. Select **tenants_sqldb** connector
3. Configure:
```json
{
  "db_type": "postgresql",
  "host": "localhost",
  "port": 5432,
  "database": "mydb",
  "username": "postgres",
  "password": "your-password",
  "pool_size": 5,
  "max_overflow": 10
}
```
4. Click **Create Server**

## Step 5: Use the Tools

Once your server is created, you can use the available tools:

### Test Connection
```python
# Call: test_connection()
# Returns: "Connection active: postgresql database is connected..."
```

### List Tables
```python
# Call: list_tables()
# Returns: "Tables: ['users', 'orders', 'products']"
```

### Execute Query
```python
# Call: execute_query(
#   query="SELECT * FROM users WHERE age > :age",
#   params={"age": 18}
# )
# Returns: Query results as JSON
```

### Get Table Schema
```python
# Call: get_table_schema(table_name="users")
# Returns: Complete schema with columns, keys, indexes
```

## Step 6: Use Templates

Templates help you build queries quickly:

### Generate SELECT Query
```python
# Template: select_query
# Input:
{
  "table_name": "users",
  "columns": "id, name, email",
  "where_clause": "age > 18",
  "limit": 100
}
# Output: "SELECT id, name, email FROM users WHERE age > 18 LIMIT 100"
```

### Generate INSERT Query
```python
# Template: insert_query
# Input:
{
  "table_name": "users",
  "columns": "name, email, age",
  "values": ":name, :email, :age"
}
# Output: "INSERT INTO users (name, email, age) VALUES (:name, :email, :age)"
```

## Common Use Cases

### Use Case 1: Data Analytics
```python
# 1. Connect to your analytics database
# 2. List available tables
list_tables()

# 3. Inspect table schema
get_table_schema(table_name="sales")

# 4. Run analytical queries
execute_query(
    query="""
        SELECT product_id, SUM(amount) as total_sales
        FROM sales
        WHERE date >= :start_date
        GROUP BY product_id
        ORDER BY total_sales DESC
        LIMIT 10
    """,
    params={"start_date": "2024-01-01"}
)
```

### Use Case 2: Multi-Tenant Application
```python
# Create separate servers for each tenant
# Tenant 1: tenant1_db
# Tenant 2: tenant2_db

# Each server maintains isolated connections
# No cross-tenant data access
```

### Use Case 3: Database Migration
```python
# 1. Connect to source database (Server 1)
# 2. Get table schemas
get_table_schema(table_name="users")

# 3. Connect to target database (Server 2)
# 4. Execute CREATE TABLE statements
# 5. Copy data with SELECT/INSERT
```

## Troubleshooting

### Connection Failed
```
Error: Failed to connect to database
```

**Solutions**:
1. Verify database credentials
2. Check database host is accessible
3. Ensure database service is running
4. Install required driver package

### Driver Not Found
```
Error: No module named 'psycopg2'
```

**Solution**:
```bash
pip install -e ".[postgresql]"
```

### Query Execution Failed
```
Error: relation "users" does not exist
```

**Solutions**:
1. Verify table name spelling
2. Check database/schema selection
3. Use `list_tables()` to see available tables

## Next Steps

1. **Read the full documentation**: See [README.md](README.md)
2. **Understand the architecture**: See [ARCHITECTURE.md](ARCHITECTURE.md)
3. **Explore examples**: See [example_usage.py](example_usage.py)
4. **Create custom tools**: Extend the connector with your own tools
5. **Add templates**: Create templates for common queries in your domain

## Support

For issues or questions:
1. Check the [README.md](README.md) for detailed documentation
2. Review [ARCHITECTURE.md](ARCHITECTURE.md) for design details
3. Look at [example_usage.py](example_usage.py) for usage patterns

## Security Reminders

- ✅ Never commit database credentials to version control
- ✅ Use environment variables for sensitive data
- ✅ Always use parameterized queries
- ✅ Configure appropriate connection pool sizes
- ✅ Regularly rotate database passwords
- ✅ Use read-only credentials when possible

---

**You're all set!** Start creating servers and querying your databases through the MCP platform.

