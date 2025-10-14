# CASCADE DELETE Implementation Guide

## Overview

This document explains the implementation of **database-level CASCADE DELETE** for the connector deletion feature. This approach is cleaner and more efficient than manually updating related records in application code.

## Problem Statement

### Original Issue
When attempting to delete a connector, the system encountered a type mismatch error:
```
operator does not exist: character varying = integer
```

**Root Cause:** 
- `mcp_connectors.id` was defined as `INTEGER`
- `mcp_servers.connector_id` was defined as `VARCHAR` (string)
- This prevented proper foreign key relationships and cascade operations

## Solution

### 1. Database Schema Changes

**Two migrations were created:**

#### Migration 1: Fix connector_id Type (`937bb56cd37e`)
- Converts `mcp_servers.connector_id` from VARCHAR to INTEGER
- Adds proper foreign key constraint with CASCADE DELETE
- Migrates existing data safely

#### Migration 2: Add CASCADE to ConnectorAccess (`a5d42366c591`)
- Adds CASCADE DELETE to `connector_access.connector_id` foreign key
- Ensures access grants are automatically deleted with connectors

### 2. Model Updates

**File:** `api/models.py`

#### McpServer Model
```python
connector_id: Optional[int] = Field(
    default=None,
    sa_column=Column(ForeignKey('mcp_connectors.id', ondelete='CASCADE')),
    description="Foreign key to the connector (CASCADE DELETE enabled)"
)
```

#### ConnectorAccess Model
```python
connector_id: Optional[int] = Field(
    default=None,
    sa_column=Column(ForeignKey('mcp_connectors.id', ondelete='CASCADE')),
    description="Foreign key to the connector (CASCADE DELETE enabled)"
)
```

### 3. Simplified Delete Endpoint

**Before (Manual Updates):**
```python
# Manual soft delete of all related records
for server in servers_count:
    server.is_active = False
    session.add(server)

for access in access_count:
    access.is_active = False
    session.add(access)

connector.is_active = False
session.add(connector)
session.commit()
```

**After (CASCADE DELETE):**
```python
# Database handles everything automatically
session.delete(connector)
session.commit()
```

## Benefits of CASCADE DELETE

### 1. **Simplicity**
- ✅ Single `session.delete()` call
- ✅ No manual iteration over related records
- ✅ Less application code to maintain

### 2. **Performance**
- ✅ Database handles deletions in a single transaction
- ✅ More efficient than multiple UPDATE/DELETE statements
- ✅ Reduced network roundtrips

### 3. **Data Integrity**
- ✅ Atomic operation (all or nothing)
- ✅ No risk of orphaned records
- ✅ Referential integrity enforced by database

### 4. **Reliability**
- ✅ Database ensures consistency
- ✅ Less chance of application bugs
- ✅ Works even if application code changes

## Migration Details

### Migration 1: `937bb56cd37e_fix_connector_id_type_to_integer.py`

**What it does:**
1. Renames `connector_id` to `connector_id_old` (VARCHAR)
2. Adds new `connector_id` column (INTEGER, nullable)
3. Migrates data: `CAST(connector_id_old AS INTEGER)`
4. Makes `connector_id` NOT NULL
5. Adds foreign key with `ondelete='CASCADE'`
6. Drops old `connector_id_old` column

**Data Safety:**
- Only migrates rows where `connector_id_old` is a valid integer
- Uses regex check: `WHERE connector_id_old ~ '^[0-9]+$'`
- Preserves data integrity during conversion

**Downgrade:**
- Reverses the process
- Converts INTEGER back to VARCHAR
- Removes CASCADE constraint

### Migration 2: `a5d42366c591_add_cascade_delete_to_connector_access.py`

**What it does:**
1. Drops existing `connector_access_connector_id_fkey` constraint
2. Recreates with `ondelete='CASCADE'`

**Downgrade:**
- Removes CASCADE option
- Recreates without CASCADE

## Running the Migrations

```bash
cd /Users/dhanababu/workspace/forge-mcptools/api

# Check current migration status
uv run alembic current

# Show pending migrations
uv run alembic heads

# Run migrations
uv run alembic upgrade head

# If you need to rollback
uv run alembic downgrade -1
```

## Testing the CASCADE DELETE

### Test Scenario 1: Delete Connector with Servers

```python
# Setup
connector = create_connector(name="Test DB")
server1 = create_server(connector_id=connector.id)
server2 = create_server(connector_id=connector.id)

# Delete connector
session.delete(connector)
session.commit()

# Verify cascade
assert session.get(McpServer, server1.id) is None  # ✅ Auto-deleted
assert session.get(McpServer, server2.id) is None  # ✅ Auto-deleted
```

### Test Scenario 2: Delete Connector with Access Grants

```python
# Setup
connector = create_connector(name="Test DB")
access1 = grant_access(connector_id=connector.id, user_id=user1.id)
access2 = grant_access(connector_id=connector.id, user_id=user2.id)

# Delete connector
session.delete(connector)
session.commit()

# Verify cascade
assert session.get(ConnectorAccess, access1.id) is None  # ✅ Auto-deleted
assert session.get(ConnectorAccess, access2.id) is None  # ✅ Auto-deleted
```

### Test Scenario 3: API Endpoint

```bash
# As superuser, delete a connector
curl -X DELETE http://localhost:9000/api/connectors/10 \
  -H "Cookie: auth_cookie=..." \
  -H "Content-Type: application/json"

# Expected response:
{
  "status": "deleted",
  "message": "Connector 'SQL Database' and all related data deleted successfully",
  "connector_id": 10,
  "revoked_access": 3,
  "deleted_servers": 5
}
```

## Database Constraints

### Before Migration
```sql
-- mcp_servers table
connector_id VARCHAR NOT NULL  -- ❌ Type mismatch

-- connector_access table
connector_id INTEGER REFERENCES mcp_connectors(id)  -- ⚠️ No CASCADE
```

### After Migration
```sql
-- mcp_servers table
connector_id INTEGER REFERENCES mcp_connectors(id) ON DELETE CASCADE  -- ✅

-- connector_access table
connector_id INTEGER REFERENCES mcp_connectors(id) ON DELETE CASCADE  -- ✅
```

## Rollback Strategy

If you need to revert to soft delete:

1. **Downgrade migrations:**
   ```bash
   uv run alembic downgrade 75ec8f84a2b1
   ```

2. **Revert model changes:**
   - Change `connector_id` back to `str` in `McpServer`
   - Remove `ondelete='CASCADE'` from both models

3. **Update delete endpoint:**
   - Add back manual loop to mark records as inactive
   - Use soft delete instead of hard delete

## Known Limitations

### 1. Soft Delete Pattern
- CASCADE DELETE performs **hard delete** (permanent removal)
- Cannot use with `is_active` soft delete pattern
- If soft delete is required, use application-level logic instead

### 2. Audit Trail
- Deleted records are gone forever
- Consider adding an audit log table before deletion if needed:
  ```python
  # Before deletion
  audit_log = AuditLog(
      action="delete_connector",
      connector_id=connector.id,
      connector_name=connector.name,
      user_id=current_user.id,
      affected_servers=servers_count,
      affected_access=access_count
  )
  session.add(audit_log)
  ```

### 3. Related Tokens and Tools
- `mcp_server_tokens` table has FK to `mcp_servers`
- `mcp_server_tools` table has FK to `mcp_servers`
- These should also have CASCADE DELETE to avoid orphans
- **TODO:** Add migrations for these tables if needed

## Recommendations

### 1. Add CASCADE to Server Tokens
```python
# In McpServerToken model
mcp_server_id: Optional[int] = Field(
    default=None,
    sa_column=Column(ForeignKey('mcp_servers.id', ondelete='CASCADE')),
    description="Foreign key to the MCP server (CASCADE DELETE enabled)"
)
```

### 2. Add CASCADE to Server Tools
```python
# In McpServerTool model
mcp_server_id: Optional[int] = Field(
    default=None,
    sa_column=Column(ForeignKey('mcp_servers.id', ondelete='CASCADE')),
    description="Foreign key to the MCP server (CASCADE DELETE enabled)"
)
```

### 3. Add Audit Logging
Create an `audit_log` table to track deletions:
```python
class AuditLog(SQLModel, table=True):
    id: int
    action: str  # "delete_connector"
    resource_type: str  # "connector"
    resource_id: int
    user_id: UUID
    details: dict  # JSONB with deletion stats
    created_at: datetime
```

## Summary

✅ **Implemented:**
- CASCADE DELETE for `mcp_servers.connector_id`
- CASCADE DELETE for `connector_access.connector_id`
- Fixed type mismatch (VARCHAR → INTEGER)
- Simplified delete endpoint
- Comprehensive migrations with rollback

✅ **Benefits:**
- Cleaner code (single delete call)
- Better performance (database-level operation)
- Guaranteed referential integrity
- Reduced application complexity

⚠️ **Considerations:**
- Hard delete (not soft delete)
- No audit trail by default
- Need to extend CASCADE to tokens and tools

---

**Implementation Date:** October 13, 2025  
**Status:** ✅ Ready for migration  
**Migration Files:**
- `937bb56cd37e_fix_connector_id_type_to_integer.py`
- `a5d42366c591_add_cascade_delete_to_connector_access.py`

