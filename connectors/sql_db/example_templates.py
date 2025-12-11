"""
Example: Dynamic Template Registration for SQL Database Connector

This file demonstrates how to register templates similar to tool registration.
Templates allow you to create reusable, parameterized tool definitions that can
be instantiated with different configurations.

Design Patterns Used:
- Factory Pattern: Templates create tools from parameters
- Registry Pattern: Templates are registered and looked up by name
- Decorator Pattern: @mcp.template wraps functions
- Strategy Pattern: Different templates for different SQL operations
"""

from pydantic import BaseModel, Field
from mcp_pkg.dynamic_mcp import create_dynamic_mcp


# Define parameter models for templates
class QueryTemplateParams(BaseModel):
    """Parameters for creating a query tool from template"""
    table_name: str = Field(description="Name of the database table")
    columns: list[str] = Field(default=["*"], description="Columns to select")
    description: str = Field(default="", description="Custom description for the tool")


class InsertTemplateParams(BaseModel):
    """Parameters for creating an insert tool from template"""
    table_name: str = Field(description="Name of the database table")
    columns: list[str] = Field(description="Columns to insert into")
    description: str = Field(default="", description="Custom description for the tool")


class UpdateTemplateParams(BaseModel):
    """Parameters for creating an update tool from template"""
    table_name: str = Field(description="Name of the database table")
    set_columns: list[str] = Field(description="Columns to update")
    where_column: str = Field(description="Column for WHERE clause")
    description: str = Field(default="", description="Custom description for the tool")


# Configuration for the SQL connector
class SqlConfig(BaseModel):
    database_url: str = Field(description="Database connection URL")
    max_connections: int = Field(default=10, description="Maximum number of connections")
    timeout: int = Field(default=30, description="Query timeout in seconds")


# Create the MCP server
mcp, mcp_app, app = create_dynamic_mcp(
    name="sql_db_with_templates",
    config=SqlConfig,
    version="1.0.0",
    logo_file_path="media/sqldb.png",
)


# ============================================================================
# TEMPLATE REGISTRATION EXAMPLES (Similar to @server.tool)
# ============================================================================

# Example 1: Simple template registration without parentheses
@mcp.template
def query_table(params: QueryTemplateParams):
    """
    Template for creating a SELECT query tool.
    
    This template generates a tool that queries a specific table.
    """
    columns_str = ", ".join(params.columns)
    query = f"SELECT {columns_str} FROM {params.table_name}"
    
    return {
        "name": f"query_{params.table_name}",
        "description": params.description or f"Query data from {params.table_name} table",
        "sql": query,
        "parameters": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of rows to return",
                    "default": 100
                }
            }
        }
    }


# Example 2: Template with custom name
@mcp.template("insert_into_table")
def create_insert_tool(params: InsertTemplateParams):
    """
    Template for creating an INSERT tool.
    
    Generates a tool that inserts data into a specific table.
    """
    columns_str = ", ".join(params.columns)
    placeholders = ", ".join([f"${i+1}" for i in range(len(params.columns))])
    query = f"INSERT INTO {params.table_name} ({columns_str}) VALUES ({placeholders})"
    
    return {
        "name": f"insert_{params.table_name}",
        "description": params.description or f"Insert data into {params.table_name} table",
        "sql": query,
        "parameters": {
            "type": "object",
            "properties": {
                col: {
                    "type": "string",
                    "description": f"Value for {col} column"
                }
                for col in params.columns
            },
            "required": params.columns
        }
    }


# Example 3: Template with explicit params_model keyword
@mcp.template(params_model=UpdateTemplateParams)
def update_table(params):
    """
    Template for creating an UPDATE tool.
    
    Generates a tool that updates records in a specific table.
    """
    set_clause = ", ".join([f"{col} = ${i+1}" for i, col in enumerate(params.set_columns)])
    query = f"UPDATE {params.table_name} SET {set_clause} WHERE {params.where_column} = ${len(params.set_columns) + 1}"
    
    return {
        "name": f"update_{params.table_name}",
        "description": params.description or f"Update records in {params.table_name} table",
        "sql": query,
        "parameters": {
            "type": "object",
            "properties": {
                **{
                    col: {
                        "type": "string",
                        "description": f"New value for {col}"
                    }
                    for col in params.set_columns
                },
                params.where_column: {
                    "type": "string",
                    "description": f"Value to match for {params.where_column}"
                }
            },
            "required": params.set_columns + [params.where_column]
        }
    }


# Example 4: Template with custom name and title
@mcp.template(
    name="delete_from_table",
    title="Delete Records Template",
    description="Creates a tool for deleting records from a table"
)
def delete_template(params: BaseModel):
    """Template for creating a DELETE tool"""
    table_name = params.table_name  # type: ignore
    id_column = params.id_column  # type: ignore
    
    return {
        "name": f"delete_{table_name}",
        "description": f"Delete records from {table_name} table",
        "sql": f"DELETE FROM {table_name} WHERE {id_column} = $1",
        "parameters": {
            "type": "object",
            "properties": {
                id_column: {
                    "type": "string",
                    "description": f"ID of the record to delete"
                }
            },
            "required": [id_column]
        }
    }


# Example 5: Async template
@mcp.template
async def async_query_template(params: QueryTemplateParams):
    """
    Async template for complex queries.
    
    Can perform async operations before returning the tool definition.
    """
    # Simulate async operation (e.g., validate table exists, fetch schema)
    import asyncio
    await asyncio.sleep(0.1)
    
    return {
        "name": f"async_query_{params.table_name}",
        "description": f"Async query for {params.table_name}",
        "sql": f"SELECT * FROM {params.table_name}",
        "is_async": True
    }


# Example 6: Direct template registration (without decorator)
def join_query_template(params: BaseModel):
    """Template for creating JOIN query tools"""
    left_table = params.left_table  # type: ignore
    right_table = params.right_table  # type: ignore
    join_column = params.join_column  # type: ignore
    
    return {
        "name": f"join_{left_table}_{right_table}",
        "description": f"Join {left_table} and {right_table} tables",
        "sql": f"SELECT * FROM {left_table} JOIN {right_table} ON {left_table}.{join_column} = {right_table}.{join_column}"
    }

# Register the template directly
mcp.template(join_query_template, name="join_tables")


# ============================================================================
# USAGE EXAMPLES
# ============================================================================

def demonstrate_template_usage():
    """Demonstrate how to use registered templates"""
    
    # List all available templates
    print("Available Templates:")
    print("-" * 50)
    templates = mcp.list_templates()
    for template in templates:
        print(f"  - {template['name']}: {template['description']}")
    print()
    
    # Render a template to create a tool
    print("Rendering 'query_table' template:")
    print("-" * 50)
    try:
        tool_def = mcp.render_template(
            "query_table",
            {
                "table_name": "users",
                "columns": ["id", "name", "email"],
                "description": "Query users table with selected columns"
            }
        )
        print(f"Generated tool: {tool_def['name']}")
        print(f"Description: {tool_def['description']}")
        print(f"SQL: {tool_def['sql']}")
        print()
    except Exception as e:
        print(f"Error: {e}")
    
    # Render an insert template
    print("Rendering 'insert_into_table' template:")
    print("-" * 50)
    try:
        tool_def = mcp.render_template(
            "insert_into_table",
            {
                "table_name": "products",
                "columns": ["name", "price", "category"],
                "description": "Insert new products"
            }
        )
        print(f"Generated tool: {tool_def['name']}")
        print(f"SQL: {tool_def['sql']}")
        print()
    except Exception as e:
        print(f"Error: {e}")
    
    # Get template count
    print(f"Total templates registered: {mcp.get_template_count()}")


# ============================================================================
# COMPARISON: Tool vs Template Registration
# ============================================================================

"""
TOOL REGISTRATION (@mcp.tool):
- Creates a callable function that can be invoked by clients
- Each tool is a concrete implementation
- Tools execute logic and return results
- Example: @mcp.tool
          def query_users(limit: int = 100):
              return execute_query(f"SELECT * FROM users LIMIT {limit}")

TEMPLATE REGISTRATION (@mcp.template):
- Creates a factory for generating tool definitions
- Templates are reusable patterns
- Templates generate tool schemas/configurations
- Example: @mcp.template
          def query_table(params: QueryTemplateParams):
              return {
                  "name": f"query_{params.table_name}",
                  "sql": f"SELECT * FROM {params.table_name}"
              }

KEY DIFFERENCES:
1. Tools are concrete, templates are abstract
2. Tools are invoked by users, templates are invoked by admins/developers
3. Tools return data, templates return tool definitions
4. One template can generate many tools

WHEN TO USE:
- Use @mcp.tool for specific, implemented functionality
- Use @mcp.template for repeatable patterns across similar operations
"""


if __name__ == "__main__":
    import uvicorn
    
    # Demonstrate template usage
    demonstrate_template_usage()
    
    # Run the server
    print("\nStarting MCP server with templates...")
    print("Visit http://localhost:8025/connector.json to see tools and templates")
    uvicorn.run("example_templates:app", host="0.0.0.0", port=8025, reload=True)

