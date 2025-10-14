# Two-Step Connector Registration System

**Date:** October 13, 2025  
**Feature:** Register and Activate Connectors Separately  
**Access:** Superuser Only

## Overview

Implemented a two-step process for connector management:
1. **Register:** Create connector metadata (deactive mode)
2. **Activate:** Fetch schema from running connector and activate it

## API Endpoints

### Step 1: Register Connector

**Endpoint:** `POST /api/connectors/register`  
**Access:** Superuser only  
**Purpose:** Register a new connector with basic metadata

#### Request Body
```json
{
  "name": "my_connector",
  "description": "My custom connector for XYZ",
  "secret": "optional_connector_secret"
}
```

#### Response (201 Created)
```json
{
  "status": "registered",
  "message": "Connector 'my_connector' registered successfully",
  "connector_id": 15,
  "name": "my_connector",
  "mode": "deactive",
  "description": "My custom connector for XYZ",
  "created_at": "2025-10-13T20:00:00.000000",
  "next_step": "Activate the connector by providing the connector URL via POST /api/connectors/activate"
}
```

#### What Happens
- Creates connector record in database
- Sets mode to `deactive`
- Stores optional secret (encrypted)
- Returns connector ID for activation step
- Record is visible in connector list but not usable

### Step 2: Activate Connector

**Endpoint:** `POST /api/connectors/activate`  
**Access:** Superuser only  
**Purpose:** Fetch schema from connector URL and activate it

#### Request Body
```json
{
  "connector_id": 15,
  "connector_url": "http://localhost:8025/connector.json"
}
```

#### Response (200 OK)
```json
{
  "status": "activated",
  "message": "Connector 'my_connector' activated successfully",
  "connector_id": 15,
  "name": "my_connector",
  "url": "http://localhost:8025/connector.json",
  "mode": "active",
  "version": "1.0.0",
  "tools_count": 5,
  "templates_count": 3,
  "created_at": "2025-10-13T20:00:00.000000",
  "updated_at": "2025-10-13T20:05:00.000000"
}
```

#### What Happens
- Fetches connector schema from provided URL
- Updates connector with:
  - URL
  - Version
  - Description (if different)
  - Tools configuration
  - Templates configuration
  - Server configuration
  - Logo URL
- Changes mode from `deactive` to `active`
- Downloads and stores logo
- Connector is now ready for use

## Connector Modes

### Mode States
```python
class ConnectorMode(Enum):
    sync = "sync"      # Synchronous operations
    active = "active"  # Fully active and operational
    deactive = "deactive"  # Registered but not activated
```

### Mode Transitions
```
Registration → deactive
Activation   → active
Manual       → sync/deactive (via admin)
```

## UI Flow

### Superuser Dashboard - Connectors Page

#### 1. Register Connector Form
```jsx
<RegisterConnectorForm>
  <Input name="name" label="Connector Name" required />
  <Textarea name="description" label="Description" required />
  <Input name="secret" label="Secret (Optional)" type="password" />
  <Button type="submit">Register Connector</Button>
</RegisterConnectorForm>
```

#### 2. Connector List with Status
```jsx
{connectors.map(connector => (
  <ConnectorCard key={connector.id}>
    <Badge mode={connector.mode}>
      {connector.mode === 'deactive' && 'Not Activated'}
      {connector.mode === 'active' && 'Active'}
      {connector.mode === 'sync' && 'Sync Mode'}
    </Badge>
    
    {connector.mode === 'deactive' && (
      <ActivateButton connector={connector} />
    )}
    
    {connector.mode === 'active' && (
      <CreateServerButton connector={connector} />
    )}
  </ConnectorCard>
))}
```

#### 3. Activate Connector Modal
```jsx
<ActivateConnectorModal connector={connector}>
  <Info>
    Connector: {connector.name}
    Status: {connector.mode}
  </Info>
  
  <Input 
    name="connector_url" 
    label="Connector URL" 
    placeholder="http://localhost:8025/connector.json"
    required 
  />
  
  <Button onClick={handleActivate}>
    Activate Connector
  </Button>
</ActivateConnectorModal>
```

## Usage Examples

### Example 1: Complete Registration Flow

```bash
# Step 1: Register the connector
curl -X POST http://localhost:9000/api/connectors/register \
  -H "Content-Type: application/json" \
  -H "Cookie: auth_cookie=<your_cookie>" \
  -d '{
    "name": "postgres_connector",
    "description": "PostgreSQL database connector",
    "secret": "my_secure_secret_123"
  }'

# Response:
# {
#   "status": "registered",
#   "connector_id": 20,
#   "mode": "deactive",
#   ...
# }

# Step 2: Start your connector server
# (Run your connector application on port 8025)

# Step 3: Activate the connector
curl -X POST http://localhost:9000/api/connectors/activate \
  -H "Content-Type: application/json" \
  -H "Cookie: auth_cookie=<your_cookie>" \
  -d '{
    "connector_id": 20,
    "connector_url": "http://localhost:8025/connector.json"
  }'

# Response:
# {
#   "status": "activated",
#   "mode": "active",
#   "tools_count": 5,
#   ...
# }
```

### Example 2: Frontend React Implementation

```jsx
// RegisterConnectorPage.jsx
import React, { useState } from 'react';
import { api } from '../services/api';

function RegisterConnectorPage() {
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    secret: ''
  });
  const [registeredConnector, setRegisteredConnector] = useState(null);

  const handleRegister = async (e) => {
    e.preventDefault();
    try {
      const result = await api.registerConnector(formData);
      setRegisteredConnector(result);
      alert(`Connector registered! ID: ${result.connector_id}`);
    } catch (error) {
      alert(`Error: ${error.message}`);
    }
  };

  const handleActivate = async (connectorUrl) => {
    try {
      const result = await api.activateConnector({
        connector_id: registeredConnector.connector_id,
        connector_url: connectorUrl
      });
      alert(`Connector activated! Mode: ${result.mode}`);
      // Refresh connector list
      window.location.reload();
    } catch (error) {
      alert(`Activation failed: ${error.message}`);
    }
  };

  return (
    <div>
      <h1>Register New Connector</h1>
      
      {/* Step 1: Registration Form */}
      <form onSubmit={handleRegister}>
        <input
          name="name"
          placeholder="Connector Name"
          value={formData.name}
          onChange={(e) => setFormData({...formData, name: e.target.value})}
          required
        />
        <textarea
          name="description"
          placeholder="Description"
          value={formData.description}
          onChange={(e) => setFormData({...formData, description: e.target.value})}
          required
        />
        <input
          name="secret"
          type="password"
          placeholder="Secret (Optional)"
          value={formData.secret}
          onChange={(e) => setFormData({...formData, secret: e.target.value})}
        />
        <button type="submit">Register Connector</button>
      </form>

      {/* Step 2: Activation Form (shown after registration) */}
      {registeredConnector && registeredConnector.mode === 'deactive' && (
        <div className="activation-section">
          <h2>Activate Connector: {registeredConnector.name}</h2>
          <p>Start your connector server, then provide the URL:</p>
          <form onSubmit={(e) => {
            e.preventDefault();
            const url = e.target.connector_url.value;
            handleActivate(url);
          }}>
            <input
              name="connector_url"
              placeholder="http://localhost:8025/connector.json"
              required
            />
            <button type="submit">Activate</button>
          </form>
        </div>
      )}
    </div>
  );
}
```

### Example 3: API Service Methods

```javascript
// services/api.js
export const api = {
  // ... existing methods

  registerConnector: async (data) => {
    return apiRequest('/api/connectors/register', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  activateConnector: async (data) => {
    return apiRequest('/api/connectors/activate', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  // ... rest of methods
};
```

## Error Handling

### Common Errors

#### 1. Duplicate Connector Name
```json
{
  "status": 409,
  "detail": "Connector with name 'my_connector' already exists"
}
```

#### 2. Connector URL Not Reachable
```json
{
  "status": 400,
  "detail": "Failed to connect to connector URL: Connection refused"
}
```

#### 3. Invalid Connector Schema
```json
{
  "status": 400,
  "detail": "Failed to fetch connector schema from http://localhost:8025/connector.json. Status: 404"
}
```

#### 4. Connector Not Found
```json
{
  "status": 404,
  "detail": "Connector with ID 99 not found"
}
```

#### 5. Not a Superuser
```json
{
  "status": 403,
  "detail": "Access denied. Superuser role required."
}
```

### Frontend Error Handling Example

```jsx
const handleRegister = async (formData) => {
  try {
    const result = await api.registerConnector(formData);
    setNotification({
      type: 'success',
      message: `Connector '${result.name}' registered successfully!`
    });
    return result;
  } catch (error) {
    if (error.status === 409) {
      setNotification({
        type: 'error',
        message: 'A connector with this name already exists. Please choose a different name.'
      });
    } else if (error.status === 403) {
      setNotification({
        type: 'error',
        message: 'You need superuser permissions to register connectors.'
      });
    } else {
      setNotification({
        type: 'error',
        message: `Failed to register connector: ${error.message}`
      });
    }
    throw error;
  }
};

const handleActivate = async (connectorId, connectorUrl) => {
  try {
    const result = await api.activateConnector({
      connector_id: connectorId,
      connector_url: connectorUrl
    });
    setNotification({
      type: 'success',
      message: `Connector activated! Found ${result.tools_count} tools and ${result.templates_count} templates.`
    });
    return result;
  } catch (error) {
    if (error.status === 400) {
      setNotification({
        type: 'error',
        message: 'Cannot reach connector server. Make sure it\'s running and the URL is correct.'
      });
    } else if (error.status === 404) {
      setNotification({
        type: 'error',
        message: 'Connector not found. It may have been deleted.'
      });
    } else {
      setNotification({
        type: 'error',
        message: `Failed to activate connector: ${error.message}`
      });
    }
    throw error;
  }
};
```

## Database Schema

### Connector Record States

#### After Registration (Deactive)
```sql
SELECT id, name, url, mode, version FROM mcp_connectors WHERE id = 20;
```
```
| id | name              | url | mode      | version |
|----|-------------------|-----|-----------|---------|
| 20 | postgres_connector| ""  | deactive  | 0.0.0   |
```

#### After Activation (Active)
```sql
SELECT id, name, url, mode, version FROM mcp_connectors WHERE id = 20;
```
```
| id | name              | url                                    | mode   | version |
|----|-------------------|----------------------------------------|--------|---------|
| 20 | postgres_connector| http://localhost:8025/connector.json  | active | 1.0.0   |
```

## Benefits

### 1. Flexibility
- Register connectors before deployment
- Activate when ready
- No need for connector to be running during registration

### 2. Security
- Secrets can be registered beforehand
- URL validation happens at activation
- Superuser-only operations

### 3. Workflow Management
- Clear separation of concerns
- Better error handling
- Progressive deployment

### 4. User Experience
- Clear status indicators (deactive/active)
- Two-step process is intuitive
- Immediate feedback at each step

## Migration Path

### From Old Single-Step Process
The old `/api/connectors` endpoint is still available for backward compatibility but marked as deprecated.

**Old Way (still works):**
```bash
curl -X POST http://localhost:9000/api/connectors \
  -d '{"connector_url": "http://localhost:8025/connector.json"}'
```

**New Way (recommended):**
```bash
# Step 1
curl -X POST http://localhost:9000/api/connectors/register \
  -d '{"name": "my_connector", "description": "..."}'

# Step 2
curl -X POST http://localhost:9000/api/connectors/activate \
  -d '{"connector_id": 20, "connector_url": "http://localhost:8025/connector.json"}'
```

## Testing

### Manual Test Script

```bash
#!/bin/bash

# Test the two-step connector registration

API_URL="http://localhost:9000/api"
AUTH_COOKIE="your_auth_cookie_here"

echo "Step 1: Registering connector..."
REGISTER_RESPONSE=$(curl -s -X POST "$API_URL/connectors/register" \
  -H "Content-Type: application/json" \
  -H "Cookie: auth_cookie=$AUTH_COOKIE" \
  -d '{
    "name": "test_connector_'$(date +%s)'",
    "description": "Test connector for two-step registration",
    "secret": "test_secret_123"
  }')

echo "Register Response:"
echo "$REGISTER_RESPONSE" | jq .

CONNECTOR_ID=$(echo "$REGISTER_RESPONSE" | jq -r '.connector_id')
echo "Connector ID: $CONNECTOR_ID"

read -p "Start your connector server and press Enter to continue..."

echo ""
echo "Step 2: Activating connector..."
ACTIVATE_RESPONSE=$(curl -s -X POST "$API_URL/connectors/activate" \
  -H "Content-Type: application/json" \
  -H "Cookie: auth_cookie=$AUTH_COOKIE" \
  -d '{
    "connector_id": '$CONNECTOR_ID',
    "connector_url": "http://localhost:8025/connector.json"
  }')

echo "Activate Response:"
echo "$ACTIVATE_RESPONSE" | jq .

MODE=$(echo "$ACTIVATE_RESPONSE" | jq -r '.mode')
echo ""
echo "Final Mode: $MODE"

if [ "$MODE" == "active" ]; then
  echo "✅ Test PASSED: Connector successfully activated!"
else
  echo "❌ Test FAILED: Connector not activated"
fi
```

## Next Steps

1. ✅ Backend endpoints implemented
2. 🔄 Frontend UI components needed:
   - Register connector form
   - Connector list with status badges
   - Activate connector modal
   - Status indicators
3. 🔄 API service methods
4. 🔄 Error handling and user feedback
5. 🔄 Testing with real connectors

## Conclusion

The two-step connector registration system provides a flexible, secure, and user-friendly way to manage connectors. Superusers can register connectors ahead of time and activate them when ready, with clear status indicators and comprehensive error handling throughout the process.

**Ready for frontend integration!** 🚀

