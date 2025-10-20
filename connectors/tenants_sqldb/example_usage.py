"""
Example usage of Tenants SQL Database Connector

This file demonstrates how to:
1. Configure different database types
2. Create servers with the connector
3. Use tools and templates
"""

# Example 1: SQLite Configuration
sqlite_config = {
    "db_type": "sqlite",
    "database": "test.db"
}

# Example 2: PostgreSQL Configuration
postgresql_config = {
    "db_type": "postgresql",
    "host": "localhost",
    "port": 5432,
    "database": "myapp_db",
    "username": "postgres",
    "password": "secret123",
    "pool_size": 5,
    "max_overflow": 10
}

# Example 3: MySQL Configuration
mysql_config = {
    "db_type": "mysql",
    "host": "localhost",
    "port": 3306,
    "database": "myapp_db",
    "username": "root",
    "password": "secret123",
    "additional_params": {
        "driver": "pymysql"
    }
}

# Example 4: Snowflake Configuration
snowflake_config = {
    "db_type": "snowflake",
    "database": "PRODUCTION_DB",
    "username": "analytics_user",
    "password": "secret123",
    "additional_params": {
        "account": "mycompany.us-east-1",
        "warehouse": "ANALYTICS_WH",
        "schema": "PUBLIC"
    }
}

# Example Tool Usage (after server is created)
"""
# 1. Test Connection
test_connection()
# Returns: "Connection active: postgresql database is connected..."

# 2. List All Tables
list_tables()
# Returns: "Tables: ['users', 'orders', 'products']"

# 3. Get Table Schema
get_table_schema(table_name="users")
# Returns: Schema information with columns, indexes, etc.

# 4. Execute Simple Query
execute_query(query="SELECT * FROM users LIMIT 10")
# Returns: Query results as JSON

# 5. Execute Parameterized Query
execute_query(
    query="SELECT * FROM users WHERE age > :min_age AND status = :status",
    params={"min_age": 18, "status": "active"}
)
# Returns: Filtered query results
"""

# Example Template Usage
"""
# 1. Generate SELECT Query
select_query_template(
    table_name="users",
    columns="id, name, email",
    where_clause="created_at > '2024-01-01'",
    limit=100
)
# Output: "SELECT id, name, email FROM users
#          WHERE created_at > '2024-01-01' LIMIT 100"

# 2. Generate INSERT Query
insert_query_template(
    table_name="users",
    columns="name, email, age",
    values=":name, :email, :age"
)
# Output: "INSERT INTO users (name, email, age)
#          VALUES (:name, :email, :age)"

# 3. Custom Query Template
execute_query_template(
    query="UPDATE {table} SET status = :status WHERE id = :id",
    table="users"
)
# Output: "UPDATE users SET status = :status WHERE id = :id"
"""

