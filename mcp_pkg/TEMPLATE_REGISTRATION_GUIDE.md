# Dynamic Template Registration System

## Overview

The **Dynamic Template Registration System** provides a flexible, decorator-based approach to creating reusable tool templates for MCP servers. This system mirrors the `@server.tool` registration pattern but is designed for creating **tool factories** rather than concrete tool implementations.

## Design Patterns

### 1. **Factory Pattern** 🏭
Templates act as factories that generate tool definitions based on parameters.

```python
@mcp.template
def query_template(params):
    return {
        "name": f"query_{params.table}",
        "sql": f"SELECT * FROM {params.table}"
    }
```

### 2. **Registry Pattern** 📚
All templates are stored in a centralized, thread-safe registry for lookup and management.

```python
# Register
@mcp.template
def my_template(params): ...

# Retrieve
template = mcp.get_template("my_template")

# List all
templates = mcp.list_templates()
```

### 3. **Decorator Pattern** ✨
Functions are wrapped to add template capabilities without modifying their core logic.

```python
@mcp.template
def original_function(params):
    return {"tool": "definition"}

# Function still callable as normal
result = original_function(params)
```

### 4. **Strategy Pattern** 🎯
Different strategies for sync vs async template rendering.

```python
# Sync template
result = mcp.render_template("name", params)

# Async template
result = await mcp.render_template_async("name", params)
```

## Registration Syntax

The `@mcp.template` decorator supports **multiple calling patterns** similar to `@server.tool`:

### Pattern 1: No Parentheses
```python
@mcp.template
def my_template(params):
    """Template description"""
    return {"name": "tool"}
```

### Pattern 2: With Empty Parentheses
```python
@mcp.template()
def my_template(params):
    return {"name": "tool"}
```

### Pattern 3: With String Name
```python
@mcp.template("custom_name")
def my_template(params):
    return {"name": "tool"}
```

### Pattern 4: With Keyword Arguments
```python
@mcp.template(name="custom_name", title="My Template")
def my_template(params):
    return {"name": "tool"}
```

### Pattern 5: With Parameter Model
```python
class MyParams(BaseModel):
    table: str
    columns: list[str]

@mcp.template(params_model=MyParams)
def my_template(params: MyParams):
    return {
        "name": f"query_{params.table}",
        "columns": params.columns
    }
```

### Pattern 6: Direct Registration
```python
def my_function(params):
    return {"name": "tool"}

# Register without decorator
mcp.template(my_function, name="my_template")
```

### Pattern 7: Async Templates
```python
@mcp.template
async def async_template(params):
    await some_async_operation()
    return {"name": "tool"}
```

## Complete Example

```python
from pydantic import BaseModel, Field
from mcp_pkg.dynamic_mcp import create_dynamic_mcp

# 1. Define parameter model
class QueryParams(BaseModel):
    table_name: str = Field(description="Table to query")
    columns: list[str] = Field(default=["*"])
    limit: int = Field(default=100)

# 2. Create MCP server
class DbConfig(BaseModel):
    db_url: str

mcp, mcp_app, app = create_dynamic_mcp(
    name="my_connector",
    config=DbConfig,
    version="1.0.0",
    logo_file_path="logo.png"
)

# 3. Register template
@mcp.template(params_model=QueryParams)
def query_template(params: QueryParams):
    """Generate a SELECT query tool"""
    cols = ", ".join(params.columns)
    return {
        "name": f"query_{params.table_name}",
        "description": f"Query {params.table_name} table",
        "sql": f"SELECT {cols} FROM {params.table_name} LIMIT {params.limit}",
        "parameters": {
            "type": "object",
            "properties": {
                "where": {
                    "type": "string",
                    "description": "WHERE clause filter"
                }
            }
        }
    }

# 4. Use the template
tool_def = mcp.render_template(
    "query_template",
    {
        "table_name": "users",
        "columns": ["id", "name", "email"],
        "limit": 50
    }
)

print(tool_def)
# Output:
# {
#     "name": "query_users",
#     "description": "Query users table",
#     "sql": "SELECT id, name, email FROM users LIMIT 50",
#     ...
# }
```

## API Reference

### `@mcp.template(...)`

Register a function as a template.

**Parameters:**
- `name_or_fn` (str | Callable | None): Function or template name
- `name` (str | None): Template name (keyword-only)
- `title` (str | None): Human-readable title
- `description` (str | None): Template description
- `params_model` (Type[BaseModel] | None): Pydantic model for parameter validation

**Returns:** Wrapped function or decorator

**Raises:**
- `TemplateRegistrationError`: If registration fails
- `TypeError`: If arguments are invalid

### `mcp.render_template(name, params, **kwargs)`

Render a synchronous template.

**Parameters:**
- `name` (str): Template name
- `params` (dict): Parameter dictionary
- `**kwargs`: Additional arguments for template function

**Returns:** Template function result

**Raises:**
- `KeyError`: If template not found
- `ValidationError`: If parameters are invalid
- `RuntimeError`: If template is async

### `mcp.render_template_async(name, params, **kwargs)`

Render an asynchronous template.

**Parameters:**
- `name` (str): Template name
- `params` (dict): Parameter dictionary
- `**kwargs`: Additional arguments for template function

**Returns:** Template function result (awaitable)

**Raises:**
- `KeyError`: If template not found
- `ValidationError`: If parameters are invalid

### `mcp.get_template(name)`

Retrieve a registered template.

**Parameters:**
- `name` (str): Template name

**Returns:** `ToolTemplate` instance

**Raises:**
- `KeyError`: If template not found

### `mcp.list_templates()`

List all registered templates.

**Returns:** List of template metadata dictionaries

### `mcp.get_template_count()`

Get the number of registered templates.

**Returns:** int

### `mcp.unregister_template(name)`

Remove a template from the registry.

**Parameters:**
- `name` (str): Template name

**Returns:** bool (True if removed, False if not found)

### `mcp.clear_templates()`

Remove all registered templates.

## Tool vs Template Comparison

| Feature | Tools (`@mcp.tool`) | Templates (`@mcp.template`) |
|---------|---------------------|----------------------------|
| **Purpose** | Execute logic | Generate tool definitions |
| **Returns** | Data/results | Tool configurations |
| **Invoked by** | End users | Admins/developers |
| **Reusability** | Single implementation | Multiple instantiations |
| **Example** | Query specific table | Generate query tool for any table |

### When to Use Tools

Use `@mcp.tool` when:
- You have a specific, concrete operation
- Users will invoke it directly
- The implementation is unique and not reusable

```python
@mcp.tool
def get_user_by_id(user_id: int):
    return database.query(f"SELECT * FROM users WHERE id = {user_id}")
```

### When to Use Templates

Use `@mcp.template` when:
- You have a repeatable pattern across similar operations
- You want to generate multiple similar tools
- The structure is the same, but parameters differ

```python
@mcp.template
def query_table_template(params):
    return {
        "name": f"query_{params.table}",
        "sql": f"SELECT * FROM {params.table}"
    }

# Can generate tools for multiple tables:
# query_users, query_products, query_orders, etc.
```

## Thread Safety

All template operations are **thread-safe** thanks to internal locking:

```python
# Safe to call from multiple threads
@mcp.template
def my_template(params): ...

# Safe to render from multiple threads
result = mcp.render_template("name", params)
```

## Best Practices

### 1. Use Type Annotations
```python
@mcp.template
def good_template(params: MyParams):  # ✅ Clear type
    ...

@mcp.template
def bad_template(params):  # ❌ Unclear type
    ...
```

### 2. Provide Descriptive Docstrings
```python
@mcp.template
def query_template(params):
    """
    Generate a SELECT query tool for any table.
    
    Creates a parameterized query with configurable columns and filters.
    """
    ...
```

### 3. Validate Parameters with Pydantic
```python
class QueryParams(BaseModel):
    table: str = Field(min_length=1, max_length=63)
    columns: list[str] = Field(min_items=1)
    
    @validator('table')
    def validate_table_name(cls, v):
        if not v.isidentifier():
            raise ValueError("Invalid table name")
        return v
```

### 4. Handle Async Properly
```python
# Async template
@mcp.template
async def async_template(params):
    result = await some_async_op()
    return result

# Must use async render
result = await mcp.render_template_async("async_template", params)
```

### 5. Provide Meaningful Names
```python
# Good names
@mcp.template("query_with_pagination")
@mcp.template("insert_with_validation")
@mcp.template("update_with_audit")

# Bad names
@mcp.template("template1")
@mcp.template("temp")
@mcp.template("fn")
```

## Error Handling

```python
from mcp_pkg.template_registery import TemplateRegistrationError
from pydantic import ValidationError

# Handle registration errors
try:
    @mcp.template
    def invalid_template():  # ❌ No params
        pass
except TemplateRegistrationError as e:
    print(f"Registration failed: {e}")

# Handle rendering errors
try:
    result = mcp.render_template("my_template", invalid_params)
except ValidationError as e:
    print(f"Invalid parameters: {e}")
except KeyError as e:
    print(f"Template not found: {e}")
```

## Advanced Usage

### Dynamic Template Registration
```python
def create_templates_from_schema(schema):
    for table in schema.tables:
        def template_fn(params, table_name=table.name):
            return {"name": f"query_{table_name}"}
        
        mcp.template(template_fn, name=f"{table.name}_template")
```

### Template Chaining
```python
@mcp.template
def base_query(params):
    return {"sql": f"SELECT * FROM {params.table}"}

@mcp.template
def filtered_query(params):
    base = mcp.render_template("base_query", params)
    base["sql"] += f" WHERE {params.filter}"
    return base
```

### Template Metadata
```python
@mcp.template
def my_template(params):
    return {"tool": "def"}

# Access metadata
fn = my_template
print(fn._template_name)  # "my_template"
print(fn._template)       # ToolTemplate instance
```

## Conclusion

The Dynamic Template Registration System provides a powerful, flexible way to create reusable tool factories that follow the same intuitive patterns as tool registration. By combining multiple design patterns (Factory, Registry, Decorator, Strategy), it enables scalable, maintainable MCP server development.

**Key Takeaways:**
- Templates are tool factories, not tools themselves
- Multiple registration syntaxes support different use cases
- Thread-safe operation ensures reliability
- Pydantic validation provides type safety
- Async support enables complex operations

For more examples, see `connectors/sql_db/example_templates.py`.

