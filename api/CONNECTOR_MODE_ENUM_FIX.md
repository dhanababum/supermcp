# ConnectorMode Enum Adaptation Fix

## Issue

**Error**: `(psycopg2.ProgrammingError) can't adapt type 'ConnectorMode'`

**Date**: 2025-10-13  
**Status**: ✅ Fixed

## Problem Description

When creating or updating connectors, the `ConnectorMode` enum was being passed directly to PostgreSQL via psycopg2, which doesn't know how to adapt Python Enum objects to SQL types.

### Error Stack Trace

```
psycopg2.ProgrammingError: can't adapt type 'ConnectorMode'
[SQL: INSERT INTO mcp_connectors (..., mode, ...) VALUES (..., %(mode)s, ...)]
[parameters: {..., 'mode': <ConnectorMode.deactive: 'deactive'>, ...}]
```

## Root Cause

The database column is defined as `VARCHAR(20)`, and SQLAlchemy expects string values, but the code was passing enum objects directly:

```python
# Wrong - Enum object
connector.mode = ConnectorMode.deactive
# Results in: <ConnectorMode.deactive: 'deactive'>

# Correct - String value
connector.mode = ConnectorMode.deactive.value
# Results in: "deactive"
```

## Solution

Convert all `ConnectorMode` enum assignments to use `.value` to extract the string value.

### Fixed Locations

#### 1. Register Connector Endpoint (Line 337)

**File**: `api/main.py`  
**Endpoint**: `POST /api/connectors/register`

```python
# Before
connector_data = {
    # ...
    "mode": ConnectorMode.deactive,  # ❌ Wrong
    # ...
}

# After
connector_data = {
    # ...
    "mode": ConnectorMode.deactive.value,  # ✅ Correct
    # ...
}
```

#### 2. Activate Connector Endpoint (Line 425)

**File**: `api/main.py`  
**Endpoint**: `POST /api/connectors/activate`

```python
# Before
connector.mode = ConnectorMode.active  # ❌ Wrong

# After
connector.mode = ConnectorMode.active.value  # ✅ Correct
```

#### 3. Legacy Register Endpoint (Line 256)

**File**: `api/main.py`  
**Endpoint**: `POST /register-connector`

```python
# Before
connector = McpConnector(
    name=req.name,
    secret=secret_hash,
    mode=ConnectorMode.sync,  # ❌ Wrong
    # ...
)

# After
connector = McpConnector(
    name=req.name,
    secret=secret_hash,
    mode=ConnectorMode.sync.value,  # ✅ Correct
    # ...
)
```

## ConnectorMode Enum

**File**: `api/datatypes.py`

```python
class ConnectorMode(Enum):
    sync = "sync"
    active = "active"
    deactive = "deactive"
```

### Enum Value Mapping

| Enum Member | `.value` (String) | Database Value |
|------------|-------------------|----------------|
| `ConnectorMode.sync` | `"sync"` | `sync` |
| `ConnectorMode.active` | `"active"` | `active` |
| `ConnectorMode.deactive` | `"deactive"` | `deactive` |

## Why This Fix Works

### 1. Database Schema

The `mcp_connectors` table defines `mode` as:

```sql
mode VARCHAR(20) NOT NULL DEFAULT 'sync'
```

PostgreSQL expects a string value, not a Python object.

### 2. SQLAlchemy Mapping

The model defines:

```python
mode: ConnectorMode = Field(
    default=ConnectorMode.sync,
    sa_column=Column(String(20), nullable=False, default='sync'),
    description="The connector mode"
)
```

The `String(20)` type requires string values.

### 3. Psycopg2 Adaptation

Psycopg2 (PostgreSQL adapter) knows how to convert Python types to SQL types:

| Python Type | Psycopg2 Handling |
|------------|-------------------|
| `str` | ✅ Direct conversion to VARCHAR |
| `int` | ✅ Direct conversion to INTEGER |
| `Enum` | ❌ No built-in adapter |

To use enums, we must:
- Either: Convert to string using `.value`
- Or: Register a custom adapter (more complex)

## Testing

### Test Registration

```bash
curl -X POST http://localhost:9000/api/connectors/register \
  -H "Content-Type: application/json" \
  -H "Cookie: auth_cookie=<your-cookie>" \
  -d '{
    "name": "Test Connector",
    "description": "Test description",
    "secret": "optional_secret"
  }'
```

**Expected Response**:
```json
{
  "status": "registered",
  "connector": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Test Connector",
    "mode": "deactive",
    "description": "Test description",
    ...
  }
}
```

### Test Activation

```bash
curl -X POST http://localhost:9000/api/connectors/activate \
  -H "Content-Type: application/json" \
  -H "Cookie: auth_cookie=<your-cookie>" \
  -d '{
    "connector_id": "550e8400-e29b-41d4-a716-446655440000",
    "connector_url": "http://localhost:8080"
  }'
```

**Expected Response**:
```json
{
  "status": "activated",
  "connector": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Test Connector",
    "mode": "active",
    ...
  }
}
```

## Verification

Check that all enum assignments now use `.value`:

```bash
grep -n "ConnectorMode\." api/main.py
```

**Expected**: All instances should show `.value` after the enum member.

## Related Files

- `api/main.py`: Fixed enum assignments
- `api/datatypes.py`: Enum definition
- `api/models.py`: Model with mode field

## Impact

### Affected Endpoints

- ✅ `POST /api/connectors/register` - Two-step registration (Step 1)
- ✅ `POST /api/connectors/activate` - Two-step registration (Step 2)
- ✅ `POST /register-connector` - Legacy endpoint

### Operations Fixed

- Creating new connectors in `deactive` mode
- Activating registered connectors to `active` mode
- Legacy connector registration in `sync` mode

## Best Practices

### When Using Enums with SQLAlchemy

1. **Always use `.value`** when assigning enum to database fields:
   ```python
   model.field = MyEnum.member.value
   ```

2. **Define the column as String** in the model:
   ```python
   field: MyEnum = Field(
       sa_column=Column(String(20)),
       default=MyEnum.default_value
   )
   ```

3. **Be consistent** - always extract the string value before database operations.

### Alternative Approach (Not Recommended Here)

Register a custom psycopg2 adapter:

```python
import psycopg2.extensions
from datatypes import ConnectorMode

def adapt_connector_mode(mode):
    return psycopg2.extensions.AsIs(f"'{mode.value}'")

psycopg2.extensions.register_adapter(ConnectorMode, adapt_connector_mode)
```

**Why we chose `.value` instead**:
- Simpler and more explicit
- No global state changes
- Easier to understand and debug
- Consistent with Pydantic/FastAPI patterns

## Prevention

To prevent this issue in the future:

1. **Code Review**: Check that all enum assignments to database fields use `.value`
2. **Testing**: Test create/update operations in development
3. **Linting**: Consider adding a custom linter rule
4. **Documentation**: Keep this document updated

## Conclusion

The fix was straightforward: convert enum objects to their string values using `.value` before passing them to the database. This ensures compatibility with psycopg2's type adaptation system and the database's VARCHAR type.

**Status**: ✅ Fully Fixed  
**Testing**: Required (manual testing with frontend)  
**Rollback**: Not needed (code-only fix)

