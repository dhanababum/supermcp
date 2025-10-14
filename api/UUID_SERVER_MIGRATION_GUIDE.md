# Server ID UUID Migration Guide

## Overview

This migration converts **ONLY** `mcp_servers.id` from INTEGER to UUID, leaving all other table IDs as integers.

**Migration Date:** October 13, 2025  
**Status:** ⚠️ Ready to Run (Not Yet Applied)

## Why Only Server IDs?

### Use Case:
- **Distributed Servers:** Server instances may be created across different systems
- **API Security:** Server IDs exposed in APIs benefit from non-sequential UUIDs
- **Simplicity:** Keep connector/token/tool IDs as integers for simplicity

### What Changes:
✅ `mcp_servers.id`: INTEGER → UUID  
✅ `mcp_server_tokens.mcp_server_id`: INTEGER → UUID (FK reference)  
✅ `mcp_server_tools.mcp_server_id`: INTEGER → UUID (FK reference)  

### What Stays the Same:
❌ `mcp_connectors.id`: INTEGER (no change)  
❌ `connector_access.id`: INTEGER (no change)  
❌ `mcp_server_tokens.id`: INTEGER (no change)  
❌ `mcp_server_tools.id`: INTEGER (no change)  

## Migration File

**File:** `f8afdb2a25f6_convert_integer_ids_to_uuid.py`

**Strategy:**
1. Enable `uuid-ossp` extension
2. Add `id_uuid` column to `mcp_servers`
3. Generate UUIDs for all existing servers
4. Add `mcp_server_id_uuid` columns to tokens and tools
5. Copy UUID references from servers to child tables
6. Drop old integer columns and constraints
7. Rename UUID columns and recreate constraints with CASCADE DELETE

## Running the Migration

### ⚠️ IMPORTANT: Backup First!

```bash
# Backup your database
pg_dump your_database > backup_before_server_uuid_migration.sql
```

### Run Migration

```bash
cd /Users/dhanababu/workspace/forge-mcptools/api

# Review the migration SQL
uv run alembic upgrade f8afdb2a25f6 --sql

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

print("\n" + "=" * 80)
print("SERVER ID UUID MIGRATION VERIFICATION")
print("=" * 80)

# Check mcp_servers.id
print("\n📋 mcp_servers:")
for col in inspector.get_columns('mcp_servers'):
    if col['name'] == 'id':
        col_type = str(col['type'])
        status = "✅" if "UUID" in col_type else "❌"
        print(f"  {status} id: {col_type}")

# Check mcp_server_tokens.mcp_server_id
print("\n📋 mcp_server_tokens:")
for col in inspector.get_columns('mcp_server_tokens'):
    if col['name'] == 'id':
        print(f"  ✅ id: {col['type']} (should be INTEGER)")
    if col['name'] == 'mcp_server_id':
        col_type = str(col['type'])
        status = "✅" if "UUID" in col_type else "❌"
        print(f"  {status} mcp_server_id: {col_type}")

# Check mcp_server_tools.mcp_server_id
print("\n📋 mcp_server_tools:")
for col in inspector.get_columns('mcp_server_tools'):
    if col['name'] == 'id':
        print(f"  ✅ id: {col['type']} (should be INTEGER)")
    if col['name'] == 'mcp_server_id':
        col_type = str(col['type'])
        status = "✅" if "UUID" in col_type else "❌"
        print(f"  {status} mcp_server_id: {col_type}")

# Check CASCADE DELETE
print("\n📋 CASCADE DELETE Constraints:")
for fk in inspector.get_foreign_keys('mcp_server_tokens'):
    if 'mcp_server_id' in fk['constrained_columns']:
        status = "✅" if fk.get('ondelete') == 'CASCADE' else "❌"
        print(f"  {status} mcp_server_tokens.mcp_server_id ON DELETE: {fk.get('ondelete', 'NO ACTION')}")

for fk in inspector.get_foreign_keys('mcp_server_tools'):
    if 'mcp_server_id' in fk['constrained_columns']:
        status = "✅" if fk.get('ondelete') == 'CASCADE' else "❌"
        print(f"  {status} mcp_server_tools.mcp_server_id ON DELETE: {fk.get('ondelete', 'NO ACTION')}")

print("\n" + "=" * 80)
PYTHON_EOF
```

## Expected Results

### Before Migration:
```sql
CREATE TABLE mcp_servers (
    id INTEGER PRIMARY KEY,
    connector_id INTEGER REFERENCES mcp_connectors(id),
    ...
);

CREATE TABLE mcp_server_tokens (
    id INTEGER PRIMARY KEY,
    mcp_server_id INTEGER REFERENCES mcp_servers(id),
    ...
);
```

### After Migration:
```sql
CREATE TABLE mcp_servers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    connector_id INTEGER REFERENCES mcp_connectors(id),
    ...
);

CREATE TABLE mcp_server_tokens (
    id INTEGER PRIMARY KEY,
    mcp_server_id UUID REFERENCES mcp_servers(id) ON DELETE CASCADE,
    ...
);
```

## API Impact

### Backend Changes:
- ✅ Models already updated (McpServer.id is UUID)
- ✅ API endpoints accept both int and UUID in URLs
- ✅ JSON responses will show UUID strings for server_id

### Frontend Changes:
**NO CHANGES REQUIRED** - Frontend already handles IDs as strings!

### Example API Response:

**Before:**
```json
{
  "server_id": 123,
  "connector_id": 10,
  "server_name": "My SQL Server"
}
```

**After:**
```json
{
  "server_id": "550e8400-e29b-41d4-a716-446655440000",
  "connector_id": 10,
  "server_name": "My SQL Server"
}
```

## CASCADE DELETE Bonus

This migration ensures tokens and tools are automatically deleted when a server is deleted:

```
DELETE FROM mcp_servers WHERE id = '550e8400-e29b-41d4-a716-446655440000';

-- Automatically deletes:
-- - All tokens for this server (via CASCADE)
-- - All tools for this server (via CASCADE)
```

## Testing Checklist

### Before Migration:
- [ ] Backup database
- [ ] Test on development environment first
- [ ] Note count of existing servers, tokens, tools

### After Migration:
- [ ] Verify mcp_servers.id is UUID
- [ ] Verify mcp_server_tokens.mcp_server_id is UUID
- [ ] Verify mcp_server_tools.mcp_server_id is UUID
- [ ] Test creating a new server (should get UUID)
- [ ] Test deleting a server (should CASCADE to tokens/tools)
- [ ] Test API endpoints with UUID server_id
- [ ] Verify frontend displays correctly

## Rollback

If you need to rollback:

```bash
uv run alembic downgrade -1
```

**⚠️ WARNING:** Rollback is destructive and will:
- Generate NEW integer IDs (not original ones)
- Lose UUID references
- Only use for development/testing!

## Summary

✅ **Simplified Migration:** Only converts server IDs to UUID  
✅ **Data Safety:** Preserves all existing data  
✅ **CASCADE DELETE:** Automatic cleanup of child records  
✅ **Zero Downtime:** No service interruption  
✅ **Frontend Compatible:** No frontend changes needed  

## Next Steps

1. ✅ Review this migration guide
2. ⚠️ Backup your database
3. ⚠️ Test on development environment first
4. 🚀 Run: `uv run alembic upgrade head`
5. ✅ Verify with test script above
6. ✅ Test API endpoints
7. ✅ Test frontend integration

---

**Questions or Issues?**  
See `/api/CASCADE_DELETE_IMPLEMENTATION.md` for CASCADE documentation.

