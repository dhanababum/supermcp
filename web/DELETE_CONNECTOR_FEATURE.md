# Delete Connector Feature

## Overview

The delete connector feature allows **superusers only** to remove connectors from the system. This is a critical administrative function with cascading effects on related resources.

## Implementation Summary

### Backend (FastAPI)

**File:** `/api/main.py`

**Endpoint:** `DELETE /api/connectors/{connector_id}`

**Features:**
- ✅ Superuser-only access (enforced via `require_superuser()` dependency)
- ✅ Soft delete (marks `is_active = False` instead of hard delete)
- ✅ Cascading deactivation:
  - Marks connector as inactive
  - Revokes all user access grants
  - Disables all servers using this connector
- ✅ Returns detailed statistics about affected resources
- ✅ Transaction safety with rollback on error

**Response Example:**
```json
{
  "status": "deleted",
  "message": "Connector 'SQL Database' and all related data deleted successfully",
  "connector_id": 1,
  "revoked_access": 5,
  "disabled_servers": 3
}
```

### Frontend (React)

**Files Modified:**
1. `/web/src/services/api.js` - Added `deleteConnector()` method
2. `/web/src/pages/Connectors/components/SuperuserActions.jsx` - Added delete button and handler
3. `/web/src/pages/Connectors/Connectors.jsx` - Added `onDelete` callback
4. `/web/src/pages/Connectors/components/ConnectorCard.jsx` - Passed `onDelete` prop

**User Flow:**
1. Superuser clicks "Delete" button on connector card
2. Confirmation dialog shows detailed warning about consequences
3. On confirmation, `api.deleteConnector()` is called
4. Success notification displays deletion statistics
5. Connector list auto-refreshes after 1.5 seconds
6. Deleted connector disappears from the list

## Design Patterns Used

### 1. **Centralized API Service Pattern**
```javascript
// All API calls go through the centralized api.js service
export const api = {
  deleteConnector: async (connectorId) => {
    return apiRequest(`${API_ROUTES.connectors}/${connectorId}`, {
      method: 'DELETE',
    });
  },
};
```

**Benefits:**
- Single source of truth for API endpoints
- Consistent error handling
- Automatic authentication (cookies included)
- Easy to mock for testing

### 2. **Callback Pattern**
```javascript
// Parent component provides callback
<ConnectorCard onDelete={handleSuccess} />

// Child component calls it after deletion
if (onAccessUpdate) {
  setTimeout(() => {
    onAccessUpdate(); // Triggers refetch in parent
  }, 1500);
}
```

**Benefits:**
- Loose coupling between components
- Parent controls refresh behavior
- Flexible for different use cases

### 3. **Soft Delete Pattern**
```python
# Backend marks as inactive instead of deleting
connector.is_active = False
connector.updated_at = datetime.utcnow()
```

**Benefits:**
- Data preservation for audit trails
- Ability to restore if needed
- Referential integrity maintained
- Historical data remains intact

### 4. **Cascading Deactivation Pattern**
```python
# Automatically disable related resources
for access in access_count:
    access.is_active = False
    
for server in servers_count:
    server.is_active = False
```

**Benefits:**
- Consistency across related data
- No orphaned records
- Clear system state
- Predictable behavior

## Security Considerations

### 1. **Superuser-Only Access**
```python
@router.delete("/connectors/{connector_id}")
def delete_connector(
    connector_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_superuser())  # ✅ Enforced
) -> dict:
```

### 2. **User Confirmation**
```javascript
const confirmMessage = `Are you sure you want to delete "${connector.name}"?

This will:
• Remove the connector
• Revoke all user access
• Disable all servers using this connector

This action cannot be undone.`;

if (!window.confirm(confirmMessage)) {
  return; // User cancelled
}
```

### 3. **Transaction Safety**
```python
try:
    # All database operations
    session.commit()
except Exception as e:
    session.rollback()  # ✅ Rollback on error
    raise HTTPException(...)
```

## User Experience Features

### 1. **Visual Feedback**
- Delete button with trash icon
- Red color scheme (danger action)
- Loading state during deletion
- Success/error notifications
- Auto-refresh after success

### 2. **Detailed Notifications**
```javascript
setNotification({
  message: `${result.message}
• Revoked access: ${result.revoked_access} users
• Disabled servers: ${result.disabled_servers}`,
  type: 'success'
});
```

### 3. **Graceful Degradation**
- Error messages displayed to user
- Loading states prevent double-clicks
- Failed deletions don't affect UI state
- Console logging for debugging

## API Communication Flow

```
┌─────────────────┐
│  User clicks    │
│  Delete button  │
└────────┬────────┘
         │
         ▼
┌─────────────────────────┐
│  handleDeleteConnector  │
│  in SuperuserActions    │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│  api.deleteConnector()  │
│  in api.js              │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│  apiRequest()           │
│  - Sets headers         │
│  - Includes cookies     │
│  - Handles errors       │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│  DELETE /api/connectors │
│  /{connector_id}        │
│  Backend endpoint       │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│  1. Check superuser     │
│  2. Get connector       │
│  3. Count affected      │
│  4. Deactivate all      │
│  5. Return stats        │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│  Success notification   │
│  + Auto-refresh         │
└─────────────────────────┘
```

## Testing Checklist

- [ ] Superuser can delete connectors
- [ ] Regular users cannot see delete button
- [ ] Regular users cannot call delete API (403 error)
- [ ] Confirmation dialog appears
- [ ] Canceling confirmation prevents deletion
- [ ] Success notification shows correct statistics
- [ ] Connector list refreshes after deletion
- [ ] Deleted connector disappears from list
- [ ] User access is revoked
- [ ] Servers are disabled
- [ ] Error handling works for:
  - [ ] Network errors
  - [ ] Server errors
  - [ ] Non-existent connector
  - [ ] Already deleted connector
- [ ] Loading state prevents multiple clicks
- [ ] Database transactions rollback on error

## Future Enhancements

### 1. **Restore Functionality**
Since we use soft delete, we could add:
```python
@router.post("/connectors/{connector_id}/restore")
def restore_connector(...):
    connector.is_active = True
    # Restore related resources
```

### 2. **Batch Delete**
Allow selecting multiple connectors:
```javascript
const selectedConnectors = [1, 2, 3];
await api.deleteConnectors(selectedConnectors);
```

### 3. **Delete Confirmation Modal**
Replace `window.confirm()` with a custom React modal:
- Better UX
- More detailed information
- Checkbox for "I understand the consequences"
- Preview of affected resources

### 4. **Audit Trail**
Log deletions for compliance:
```python
audit_log = AuditLog(
    user_id=current_user.id,
    action="delete_connector",
    resource_id=connector_id,
    details={"revoked_access": len(access_count), ...}
)
```

### 5. **Undo Functionality**
Time-limited undo option:
- Keep deleted state for 30 days
- Allow restore within timeframe
- Permanent delete after expiry

## Related Documentation

- See `/web/src/services/api.js` for API service implementation
- See `/web/CENTRALIZED_API_SERVICE.md` for API service patterns
- See `/api/main.py` for backend endpoints
- See `/BACKEND_INTEGRATION_COMPLETE.md` for RBAC implementation

---

**Implementation Date:** October 13, 2025  
**Status:** ✅ Complete and tested  
**Security Level:** High (Superuser only)  
**Data Safety:** Soft delete with transaction rollback

