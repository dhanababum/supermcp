# Infinite /users/me Calls - FIXED

## ✅ **Problem Solved**

The `/users/me` endpoint was being called infinitely after login.

## 🐛 **Root Cause**

### The Infinite Loop:

```mermaid
sequenceDiagram
    participant Auth
    participant Storage Event
    participant useAuth
    participant Backend

    Auth->>Storage Event: dispatchEvent('storage')
    Storage Event->>useAuth: handleStorageChange()
    useAuth->>Backend: GET /users/me
    Backend->>useAuth: Response
    useAuth->>useAuth: setState()
    Note over useAuth: State change triggers re-render
    useAuth->>Storage Event: Triggers storage event ❌
    Storage Event->>useAuth: handleStorageChange()
    useAuth->>Backend: GET /users/me again ❌
    Note over useAuth,Backend: Loop continues... 🔄
```

### Why It Happened:

1. **Storage Event Loop**:
   ```javascript
   // In Auth.jsx
   window.dispatchEvent(new Event('storage'));
   
   // In useAuth.js
   window.addEventListener('storage', () => {
     checkAuthStatus();  // Calls /users/me
   });
   ```

2. **Periodic Check**:
   ```javascript
   // Also checking every 5 minutes
   setInterval(checkAuthStatus, 5 * 60 * 1000);
   ```

3. **State Updates**:
   - Each check updates state
   - State updates trigger re-renders
   - Re-renders might trigger more checks

## ✅ **Solution**

### 1. Custom Event Instead of Storage

**Before:**
```javascript
// In Auth.jsx
window.dispatchEvent(new Event('storage'));

// In useAuth.js
window.addEventListener('storage', handleStorageChange);
```

**After:**
```javascript
// In Auth.jsx
window.dispatchEvent(new Event('auth:refresh'));

// In useAuth.js
window.addEventListener('auth:refresh', handleAuthRefresh);
```

### 2. Removed Periodic Check

**Before:**
```javascript
// Check every 5 minutes
const interval = setInterval(checkAuthStatus, 5 * 60 * 1000);
```

**After:**
```javascript
// Removed interval - not needed with proper event handling
```

### 3. Added Request Deduplication

```javascript
const isCheckingRef = useRef(false);

const checkAuthStatus = useCallback(async () => {
  if (isCheckingRef.current) {
    console.log('Auth check already in progress, skipping...');
    return;
  }

  try {
    isCheckingRef.current = true;
    // ... make API call
  } finally {
    isCheckingRef.current = false;
  }
}, []);
```

## 🔄 **How It Works Now**

### Login Flow:

```mermaid
sequenceDiagram
    participant Auth
    participant Custom Event
    participant useAuth
    participant Backend

    Auth->>Custom Event: dispatchEvent('auth:refresh')
    Custom Event->>useAuth: handleAuthRefresh()
    Note over useAuth: Check if already checking
    useAuth->>Backend: GET /users/me (if not checking)
    Backend->>useAuth: Response
    useAuth->>useAuth: setState()
    Note over useAuth: No more loops! ✅
```

### Key Improvements:

1. **Custom Event**: `auth:refresh` instead of `storage`
   - More specific purpose
   - No interference with storage events
   - No unintended triggers

2. **Request Deduplication**:
   - Tracks in-progress requests
   - Skips duplicate calls
   - Prevents race conditions

3. **Removed Interval**:
   - No more periodic checks
   - Relies on explicit triggers
   - Reduces unnecessary calls

## 🧪 **Testing**

### Watch Network Tab:

1. **Clear Network Tab**
2. **Login to your app**
3. **Filter by "users"**
4. **Should see:**
   - One call on initial load
   - One call after login
   - No more calls until user action

### Console Output:

```
Login successful - cookie set
Auth refresh event received
Checking auth status with /users/me...
Auth check successful, user: test@example.com
```

### What to Watch For:

#### Good (Fixed):
```
/users/me called once or twice ✅
```

#### Bad (Broken):
```
/users/me called repeatedly ❌
```

## 🔍 **Debugging**

### Monitor API Calls:

```javascript
// Add to console
let callCount = 0;
const originalFetch = window.fetch;
window.fetch = function(...args) {
  if (args[0].includes('/users/me')) {
    console.log(`/users/me call #${++callCount}`);
  }
  return originalFetch.apply(this, args);
};
```

### Check Event Listeners:

```javascript
// List all event listeners
getEventListeners(window);

// Should show:
// - auth:refresh: 1 listener
// - NO storage listeners
```

## 📊 **Before vs After**

### Before Fix:
```
Login → /users/me
State change → /users/me
Re-render → /users/me
Storage event → /users/me
Interval → /users/me
🔄 Infinite loop...
```

### After Fix:
```
Login → /users/me
Auth refresh → /users/me (if not already checking)
✅ Done!
```

## 🔧 **Files Modified**

1. **`web/src/hooks/useAuth.js`**
   - Added request deduplication
   - Switched to custom event
   - Removed interval check

2. **`web/src/pages/Auth/Auth.jsx`**
   - Updated to use custom event
   - Reduced timeout to 100ms

## 🚀 **Performance Impact**

### Network Requests:
- **Before:** Infinite `/users/me` calls
- **After:** 1-2 calls per login

### Server Load:
- **Before:** Constant API hits
- **After:** Minimal, only when needed

### Browser Performance:
- **Before:** Constant re-renders
- **After:** Smooth, predictable behavior

## 🎯 **Best Practices**

1. **Use Custom Events**:
   - More specific purpose
   - Better control
   - No side effects

2. **Deduplicate Requests**:
   - Prevent race conditions
   - Reduce server load
   - Better UX

3. **Minimal State Updates**:
   - Only when needed
   - Prevent re-render loops
   - Better performance

## 🎉 **Summary**

**Problem:** Infinite `/users/me` calls  
**Root Cause:** Storage event loop + periodic check  
**Solution:** Custom event + request deduplication  
**Result:** Minimal, controlled API calls  

### Key Changes:
✅ **Custom `auth:refresh` event**  
✅ **Request deduplication**  
✅ **Removed interval check**  
✅ **Better state management**  

**Your authentication is now efficient and controlled!** 🚀

---

## 🔍 **Quick Debug**

Add this to console to monitor auth checks:
```javascript
let authChecks = 0;
const debugFetch = window.fetch;
window.fetch = (...args) => {
  if (args[0].includes('/users/me')) {
    console.log(`Auth Check #${++authChecks} at ${new Date().toISOString()}`);
  }
  return debugFetch.apply(window, args);
};
```

Then login and watch the console! 🔍
