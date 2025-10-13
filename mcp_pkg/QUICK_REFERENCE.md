# Template Registration - Quick Reference

## 🚀 Quick Start

```python
from mcp_pkg.dynamic_mcp import create_dynamic_mcp
from pydantic import BaseModel, Field

# Setup
mcp, _, _ = create_dynamic_mcp(name="my_app", config=MyConfig, version="1.0.0", logo_file_path="logo.png")

# Register template
@mcp.template
def my_template(params):
    return {"result": "success"}

# Use template
result = mcp.render_template("my_template", {})
```

## 📋 All Decorator Patterns

```python
# 1. Simple
@mcp.template
def template1(params): ...

# 2. With name
@mcp.template("custom_name")
def template2(params): ...

# 3. With typed params
class MyParams(BaseModel):
    value: str

@mcp.template(params_model=MyParams)
def template3(params: MyParams): ...

# 4. With all options
@mcp.template(
    name="full",
    title="Full Template",
    description="Complete example",
    params_model=MyParams
)
def template4(params): ...

# 5. Async
@mcp.template
async def template5(params): ...

# 6. Direct
mcp.template(my_func, name="direct")
```

## 🔧 Core APIs

```python
# Register
@mcp.template
def my_template(params): return {}

# List
templates = mcp.list_templates()

# Count
count = mcp.get_template_count()

# Render (sync)
result = mcp.render_template("name", {"param": "value"})

# Render (async)
result = await mcp.render_template_async("name", {"param": "value"})

# Get
template = mcp.get_template("name")

# Unregister
mcp.unregister_template("name")

# Clear all
mcp.clear_templates()
```

## ✅ Do's

✅ Use type annotations  
✅ Provide docstrings  
✅ Validate with Pydantic  
✅ Handle async properly  
✅ Give meaningful names  

## ❌ Don'ts

❌ Don't instantiate BaseModel directly  
❌ Don't skip parameter validation  
❌ Don't use sync render for async templates  
❌ Don't use generic names like "template1"  
❌ Don't ignore error handling  

## 🎯 Common Patterns

### SQL Query Template
```python
class QueryParams(BaseModel):
    table: str
    columns: list[str] = ["*"]

@mcp.template(params_model=QueryParams)
def query_template(params: QueryParams):
    return {
        "name": f"query_{params.table}",
        "sql": f"SELECT {','.join(params.columns)} FROM {params.table}"
    }
```

### API Endpoint Template
```python
class APIParams(BaseModel):
    endpoint: str
    method: str = "GET"

@mcp.template(params_model=APIParams)
def api_template(params: APIParams):
    return {
        "name": f"call_{params.endpoint}",
        "method": params.method,
        "url": f"/api/{params.endpoint}"
    }
```

## 🐛 Error Handling

```python
from mcp_pkg.template_registery import TemplateRegistrationError
from pydantic import ValidationError

try:
    result = mcp.render_template("name", params)
except KeyError:
    print("Template not found")
except ValidationError as e:
    print(f"Invalid params: {e}")
except RuntimeError:
    print("Use render_template_async for async templates")
```

## 📊 Tool vs Template

| Use @mcp.tool | Use @mcp.template |
|---------------|-------------------|
| Query users table | Generate query for ANY table |
| Call specific API | Generate API caller for ANY endpoint |
| Process one file | Generate processor for ANY file type |
| Fixed operation | Parameterized operation factory |

## 🔒 Thread Safety

All operations are thread-safe:
- ✅ Registration
- ✅ Rendering  
- ✅ Listing
- ✅ Deletion

## 💡 Pro Tips

1. **Infer types from annotations**
   ```python
   @mcp.template  # Params model auto-inferred
   def my_template(params: MyParams): ...
   ```

2. **Batch registrations**
   ```python
   for name in table_names:
       mcp.template(
           lambda p, n=name: {...},
           name=f"query_{n}"
       )
   ```

3. **Template chaining**
   ```python
   @mcp.template
   def base(params):
       return mcp.render_template("parent", params)
   ```

## 📚 Full Documentation

- See `TEMPLATE_REGISTRATION_GUIDE.md` for complete guide
- See `example_templates.py` for full examples
- See `IMPLEMENTATION_SUMMARY.md` for technical details

---

**Quick Help**: `mcp.list_templates()` to see all registered templates

