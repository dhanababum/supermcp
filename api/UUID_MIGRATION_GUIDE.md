# UUID Migration Guide

## Overview

This document describes the migration from INTEGER primary keys to UUID primary keys across all MCP tables.

**Migration Date:** October 13, 2025  
**Status:** ⚠️ Ready to Run (Not Yet Applied)

## Why UUIDs?

### Benefits:
1. **Distributed Systems:** UUIDs can be generated independently across multiple servers
2. **Security:** No sequential ID leakage
3. **Merging Data:** Easy to merge databases from different sources
4. **Scalability:** No single point of contention for ID generation
5. **API Design:** IDs don't reveal business metrics

### Trade-offs:
- Slightly larger storage (16 bytes vs 4 bytes)
- Less human-readable than integers
- Index performance (minimal impact with modern databases)

## Tables Affected

| Table | Old ID Type | New ID Type | Foreign Keys Affected |
|-------|------------|-------------|----------------------|
| `mcp_connectors` | INTEGER | UUID | connector_access, mcp_servers |
| `connector_access` | INTEGER | UUID | None |
| `mcp_servers` | INTEGER | UUID | mcp_server_tokens, mcp_server_tools |
| `mcp_server_tokens` | INTEGER | UUID | None |
| `mcp_server_tools` | INTEGER | UUID | None |

## Migration Strategy

### 1. **Zero Downtime Approach**

The migration uses a multi-step strategy to avoid data loss:

```
Step 1: Add new UUID columns alongside existing INTEGER columns
Step 2: Generate UUIDs for all existing rows
Step 3: Copy UUID references for foreign keys
Step 4: Drop old constraints
Step 5: Drop old INTEGER columns
Step 6: Rename UUID columns to original names
Step 7: Recreate constraints with CASCADE DELETE
```

### 2. **Data Preservation**

- ✅ All existing data is preserved
- ✅ UUIDs are generated using PostgreSQL's `uuid_generate_v4()`
- ✅ Foreign key relationships are maintained
- ✅ CASCADE DELETE is preserved (and extended to all FK relationships)

### 3. **Migration Order (Dependency Tree)**

```
1. mcp_connectors (root - no dependencies)
   ↓
2. connector_access (depends on mcp_connectors)
   ↓
3. mcp_servers (depends on mcp_connectors)
   ↓
4. mcp_server_tokens (depends on mcp_servers)
5. mcp_server_tools (depends on mcp_servers)
```

## Migration File

**File:** `f8afdb2a25f6_convert_integer_ids_to_uuid.py`

**Key Operations:**
1. Enables `uuid-ossp` extension
2. Processes tables in dependency order
3. Generates UUIDs for existing data
4. Updates foreign key references
5. Recreates all constraints with CASCADE DELETE

## Model Changes

### Before (INTEGER):
```python
class McpConnector(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
```

### After (UUID):
```python
class McpConnector(SQLModel, table=True):
    id: Optional[uuid.UUID] = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        sa_column=Column(UUID(as_uuid=True))
    )
```

## Running the Migration

### ⚠️ IMPORTANT: Backup First!

```bash
# Backup your database
pg_dump your_database > backup_before_uuid_migration.sql
```

### Run Migration

```bash
cd /Users/dhanababu/workspace/forge-mcptools/api

# Check current migration status
uv run alembic current

# Review the migration
uv run alembic upgrade f8afdb2a25f6 --sql  # See SQL without applying

# Run the migration
uv run alembic upgrade head
```

### Verify Migration

```bash
cd /Users/dhanababu/workspace/forge-mcptools/api
uv run python << 'PYTHON_EOF'
from database import get_session
from sqlalchemy import inspect

session = next(get_session())
inspector = inspect(session.bind)

tables = ['mcp_connectors', 'connector_access', 'mcp_servers', 
          'mcp_server_tokens', 'mcp_server_tools']

print("\n" + "=" * 80)
print("UUID MIGRATION VERIFICATION")
print("=" * 80)

for table in tables:
    print(f"\n📋 {table.upper()}:")
    columns = inspector.get_columns(table)
    id_col = next((c for c in columns if c['name'] == 'id'), None)
    if id_col:
        col_type = str(id_col['type'])
        status = "✅" if "UUID" in col_type else "❌"
        print(f"  {status} id column type: {col_type}")

print("\n" + "=" * 80)
PYTHON_EOF
```

## API Impact

### Frontend Changes Required

The frontend needs to handle UUIDs instead of integers:

#### Before:
```javascript
// Old - integers
connectorId: 123
serverId: 456
```

#### After:
```javascript
// New - UUIDs
connectorId: "550e8400-e29b-41d4-a716-446655440000"
serverId: "6ba7b810-9dad-11d1-80b4-00c04fd430c8"
```

#### URL Routes

Frontend routes should remain the same since they accept both integers and UUIDs:
```javascript
`/api/connectors/${connectorId}`  // Works with both int and UUID
```

### JavaScript UUID Validation

Add UUID validation in frontend:
```javascript
const isValidUUID = (str) => {
  const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
  return uuidRegex.test(str);
};
```

## Rollback Strategy

### If Migration Fails Mid-Way

```bash
# Alembic tracks migration state
# If migration fails, it will NOT mark as complete

# Check status
uv run alembic current

# If needed, manually rollback
uv run alembic downgrade -1
```

### ⚠️ WARNING: Downgrade is Destructive

The downgrade operation will:
- Convert UUIDs back to INTEGERs
- Generate NEW integer IDs (not original ones!)
- **Lose UUID references**

Only use downgrade for testing/development, NOT production!

## Testing Checklist

### Before Migration
- [ ] Backup database
- [ ] Test migration on development database first
- [ ] Verify all foreign key relationships are correct
- [ ] Document any custom queries that use integer IDs

### After Migration
- [ ] Verify all tables have UUID IDs
- [ ] Check foreign key constraints are intact
- [ ] Test CRUD operations (Create, Read, Update, Delete)
- [ ] Test CASCADE DELETE functionality
- [ ] Verify frontend can handle UUID IDs
- [ ] Test API endpoints with UUID parameters
- [ ] Check application logs for errors

## Expected SQL Changes

### Example: mcp_connectors Table

**Before Migration:**
```sql
CREATE TABLE mcp_connectors (
    id INTEGER PRIMARY KEY,
    ...
);
```

**After Migration:**
```sql
CREATE TABLE mcp_connectors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ...
);
```

### Example: Foreign Key

**Before Migration:**
```sql
ALTER TABLE mcp_servers
ADD CONSTRAINT fk_mcp_servers_connector_id
FOREIGN KEY (connector_id) REFERENCES mcp_connectors(id)
ON DELETE CASCADE;
```

**After Migration:**
```sql
ALTER TABLE mcp_servers
ADD CONSTRAINT fk_mcp_servers_connector_id
FOREIGN KEY (connector_id) REFERENCES mcp_connectors(id)
ON DELETE CASCADE;

-- Same constraint name and behavior, just UUID types
```

## CASCADE DELETE Bonus

This migration also ensures ALL foreign key relationships have CASCADE DELETE:

```sql
✅ mcp_servers.connector_id → mcp_connectors.id (CASCADE)
✅ connector_access.connector_id → mcp_connectors.id (CASCADE)
✅ mcp_server_tokens.mcp_server_id → mcp_servers.id (CASCADE) [NEW]
✅ mcp_server_tools.mcp_server_id → mcp_servers.id (CASCADE) [NEW]
```

Now deleting a connector will automatically delete:
1. All servers using that connector
2. All access grants for that connector
3. All tokens for those servers [NEW]
4. All tools for those servers [NEW]

## Performance Considerations

### Storage Impact
```
INTEGER: 4 bytes
UUID: 16 bytes
Overhead: +12 bytes per ID field

Example: 1 million connectors
- Old: 4 MB
- New: 16 MB
- Difference: 12 MB (negligible)
```

### Index Impact
- UUIDs use slightly more index space
- Modern PostgreSQL handles UUID indexes efficiently
- Use `uuid_generate_v4()` for better randomness and distribution

### Query Performance
- PRIMARY KEY lookups: No noticeable difference
- JOIN operations: Negligible impact (<5%)
- INSERT operations: May be slightly faster (no sequence locking)

## Troubleshooting

### Issue: Extension not found
```
ERROR: extension "uuid-ossp" is not available
```

**Solution:**
```sql
-- Connect as superuser
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
```

### Issue: Foreign key constraint violation
```
ERROR: update or delete on table "mcp_connectors" violates foreign key constraint
```

**Solution:**
This shouldn't happen if migration runs correctly. If it does:
```bash
# Check for orphaned records
SELECT * FROM mcp_servers WHERE connector_id NOT IN (SELECT id FROM mcp_connectors);
```

### Issue: Column already exists
```
ERROR: column "id_uuid" of relation "mcp_connectors" already exists
```

**Solution:**
```bash
# Migration was partially run - check state
uv run alembic current

# Downgrade and re-run
uv run alembic downgrade -1
uv run alembic upgrade head
```

## Summary

✅ **Migration File Created:** `f8afdb2a25f6_convert_integer_ids_to_uuid.py`  
✅ **Models Updated:** All 5 tables now use UUID  
✅ **CASCADE DELETE:** Extended to all FK relationships  
✅ **Zero Downtime:** Migration preserves all data  
✅ **Rollback Supported:** (Destructive - testing only)

## Next Steps

1. ✅ Review this migration guide
2. ⚠️ Backup your database
3. ⚠️ Test on development environment first
4. 🚀 Run: `uv run alembic upgrade head`
5. ✅ Verify with test script above
6. ✅ Test frontend integration

---

**Questions or Issues?**  
See `/api/CASCADE_DELETE_IMPLEMENTATION.md` for related CASCADE documentation.

