# API Endpoint Migration: connector-config → server-config

## ✅ Update Completed

All references to `/api/connector-config` have been updated to `/api/server-config` throughout the codebase.

## 📋 Changes Summary

### Backend API Endpoints (api/main.py)

| Old Endpoint | New Endpoint | Status |
|-------------|--------------|--------|
| `POST /api/connector-config/{connector_id}` | `POST /api/server-config/{server_id}` | ✅ Updated |
| `GET /api/connector-config/{connector_id}` | `GET /api/server-config/{server_id}` | ✅ Updated |
| `GET /api/connector-configs` | `GET /api/server-configs` | ✅ Updated |
| `DELETE /api/connector-config/{connector_id}` | `DELETE /api/server-config/{server_id}` | ✅ Updated |

### Frontend Updates (web/src/App.js)

**Before:**
```javascript
fetch(`http://localhost:9000/api/connector-config/${selectedConnector.id}`, {
  method: 'POST',
  // ...
})
```

**After:**
```javascript
fetch(`http://localhost:9000/api/server-config/${selectedConnector.id}`, {
  method: 'POST',
  // ...
})
```

### Other Code Updates

**File:** `mcp_tools/connectors/sql_db/main.py`

**Before:**
```python
response = requests.get(f"{config.API_URL}/connector-config/{token.credentials}")
```

**After:**
```python
response = requests.get(f"{config.API_URL}/server-config/{token.credentials}")
```

## 🔍 Files Updated

1. ✅ **web/src/App.js** - Frontend API call
2. ✅ **web/CONNECTOR_CONFIGURATION.md** - Documentation
3. ✅ **mcp_tools/connectors/sql_db/main.py** - Backend connector code
4. ✅ **api/main.py** - Already updated in previous migration

## 🧪 Testing

### Test the New Endpoints

**1. Save Server Config:**
```bash
curl -X POST http://localhost:9000/api/server-config/sql_db \
  -H "Content-Type: application/json" \
  -d '{
    "connection_type": "postgres",
    "username": "admin",
    "password": "secret",
    "host": "localhost",
    "port": 5432,
    "database": "mydb"
  }'
```

**Expected Response:**
```json
{
  "status": "created",
  "message": "Configuration for sql_db created successfully",
  "config_id": 1,
  "server_id": "sql_db"
}
```

**2. Get Server Config:**
```bash
curl http://localhost:9000/api/server-config/sql_db
```

**3. List All Configs:**
```bash
curl http://localhost:9000/api/server-configs
```

**4. Delete Config:**
```bash
curl -X DELETE http://localhost:9000/api/server-config/sql_db
```

### Test from Frontend

1. Navigate to http://localhost:3000
2. Click "Connectors" in sidebar
3. Click "Configure" on SQL databases
4. Fill out the form
5. Click "Save Configuration"
6. Should see success message with the new endpoint! ✅

## 🔄 Migration Path

### From Old to New

**Parameter Name Changes:**
- `connector_id` → `server_id`
- `connector_name` → `server_name`

**Table Changes:**
- `connector_configurations` → `mcp_servers` (with added `configuration` JSONB column)

**Endpoint Path Changes:**
- `/api/connector-config/*` → `/api/server-config/*`
- `/api/connector-configs` → `/api/server-configs`

## 📊 Complete API Reference

### POST /api/server-config/{server_id}

Create or update server configuration.

**Request:**
```http
POST /api/server-config/sql_db
Content-Type: application/json

{
  "connection_type": "postgres",
  "username": "admin",
  "password": "secret",
  "host": "localhost",
  "port": 5432,
  "database": "mydb"
}
```

**Response:**
```json
{
  "status": "created",
  "message": "Configuration for sql_db created successfully",
  "config_id": 1,
  "server_id": "sql_db"
}
```

### GET /api/server-config/{server_id}

Retrieve server configuration.

**Request:**
```http
GET /api/server-config/sql_db
```

**Response:**
```json
{
  "id": 1,
  "server_id": "sql_db",
  "server_name": "SQL databases",
  "configuration": {
    "connection_type": "postgres",
    "username": "admin",
    "host": "localhost",
    "port": 5432,
    "database": "mydb"
  },
  "created_at": "2025-10-01T10:00:00",
  "updated_at": "2025-10-01T10:00:00",
  "is_active": true
}
```

### GET /api/server-configs

List all server configurations.

**Request:**
```http
GET /api/server-configs
```

**Response:**
```json
[
  {
    "id": 1,
    "server_id": "sql_db",
    "server_name": "SQL databases",
    "configuration": { ... },
    "created_at": "2025-10-01T10:00:00",
    "updated_at": "2025-10-01T10:00:00",
    "is_active": true
  }
]
```

### DELETE /api/server-config/{server_id}

Delete (soft delete) server configuration.

**Request:**
```http
DELETE /api/server-config/sql_db
```

**Response:**
```json
{
  "status": "deleted",
  "message": "Configuration for sql_db deleted successfully",
  "server_id": "sql_db"
}
```

## ✅ Verification Checklist

- [x] Backend endpoints updated in `api/main.py`
- [x] Frontend API calls updated in `web/src/App.js`
- [x] Connector code updated in `mcp_tools/connectors/sql_db/main.py`
- [x] Documentation updated
- [x] No remaining references to old endpoints in active code
- [ ] Test all endpoints manually
- [ ] Test frontend configuration flow
- [ ] Verify existing data still works

## 🚀 Deployment Notes

**Breaking Change Alert:** This is a breaking change if you have external clients using the old endpoints.

### Migration Checklist for Deployment:

1. **Database Migration:**
   - ✅ Already completed via Alembic migration `1a19129680dc`
   - Table renamed: `connector_configurations` → `mcp_servers`

2. **Backend Deployment:**
   - Deploy updated `api/main.py`
   - Restart API server

3. **Frontend Deployment:**
   - Deploy updated `web/src/App.js`
   - Clear browser cache for users

4. **External Clients:**
   - Notify external API consumers about endpoint changes
   - Provide migration timeline
   - Consider temporary redirect support if needed

## 📝 Backward Compatibility

**Note:** The old endpoints (`/api/connector-config/*`) are no longer available. All clients must update to use the new endpoints.

If you need backward compatibility, you can add redirects or aliases in `api/main.py`:

```python
# Backward compatibility aliases (optional)
@router.post("/connector-config/{server_id}")
async def save_connector_config_legacy(
    server_id: str,
    config_data: dict,
    session: Session = Depends(get_session)
):
    """Legacy endpoint - redirects to new endpoint"""
    return await save_server_config(server_id, config_data, session)
```

## 🎯 Benefits of This Change

1. **Consistency:** Endpoint names now match the database table name (`mcp_servers`)
2. **Clarity:** "server-config" better represents the consolidated functionality
3. **Simplification:** Single table for server information and configuration
4. **Scalability:** JSONB column allows flexible schema evolution

---

**Status:** ✅ All endpoints updated and ready to use!

**Last Updated:** 2025-10-01

Use the new `/api/server-config/*` endpoints for all server configuration operations. 🚀

