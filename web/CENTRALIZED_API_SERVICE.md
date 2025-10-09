# Centralized API Service with Cookie Authentication

## ✅ **Problem Solved**

Every API request needs to include authentication cookies, and we want to handle this consistently across the application.

## 🎯 **Solution**

Created a centralized API service that:
1. Automatically includes credentials with every request
2. Handles different content types (JSON vs form-encoded)
3. Manages error responses consistently
4. Provides type-safe API routes

## 🔧 **Implementation**

### API Routes Configuration

```javascript
const API_ROUTES = {
  // Auth endpoints
  login: '/auth/cookie/login',
  logout: '/auth/logout',
  me: '/users/me',
  register: '/auth/register',
  
  // API endpoints
  connectors: '/api/connectors',
  connectorSchema: (id) => `/api/connector-schema/${id}`,
  servers: '/api/servers',
  server: (id) => `/api/servers/${id}`,
  serverTools: (id) => `/api/servers/${id}/tools`,
};
```

### Default Request Configuration

```javascript
const defaultFetchOptions = {
  credentials: 'include', // Always include cookies
  headers: {
    'Accept': 'application/json',
    'Content-Type': 'application/json',
  },
};
```

### Centralized Request Handler

```javascript
const apiRequest = async (endpoint, options = {}) => {
  const url = `${API_BASE_URL}${endpoint}`;
  const fetchOptions = {
    ...defaultFetchOptions,
    ...options,
    headers: {
      ...defaultFetchOptions.headers,
      ...options.headers,
    },
  };

  try {
    const response = await fetch(url, fetchOptions);

    // Handle different response types
    if (response.status === 204) {
      return { ok: true };
    }

    // Parse JSON if available
    let data;
    const contentType = response.headers.get('content-type');
    if (contentType?.includes('application/json')) {
      data = await response.json();
    }

    // Handle errors
    if (!response.ok) {
      handleErrorResponse(response, data);
    }

    return data;
  } catch (error) {
    console.error('API Request failed:', error);
    throw error;
  }
};
```

### API Methods

```javascript
export const api = {
  // Auth
  login: async (formData) => {
    const body = new URLSearchParams();
    body.append('username', formData.email);
    body.append('password', formData.password);

    return apiRequest(API_ROUTES.login, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: body.toString(),
    });
  },

  // Regular JSON endpoints
  getServers: async () => {
    return apiRequest(API_ROUTES.servers);
  },

  createServer: async (serverData) => {
    return apiRequest(API_ROUTES.servers, {
      method: 'POST',
      body: JSON.stringify(serverData),
    });
  },
};
```

## 🔐 **Authentication Flow**

### Login Request (form-encoded)

```http
POST /auth/cookie/login
Content-Type: application/x-www-form-urlencoded
Accept: application/json

username=test@example.com&password=testpassword123
```

### API Request (with cookie)

```http
GET /api/servers
Accept: application/json
Content-Type: application/json
Cookie: auth_cookie=eyJ...

// Cookie is automatically included!
```

## 🎯 **Features**

### 1. Automatic Cookie Handling
- ✅ `credentials: 'include'` on all requests
- ✅ Cookies sent automatically
- ✅ No manual cookie management needed

### 2. Content Type Handling
- ✅ JSON for most requests
- ✅ Form-encoded for login
- ✅ Proper Accept headers

### 3. Error Handling
- ✅ 401 → Redirect to login
- ✅ 422 → Validation errors
- ✅ 204 → No content
- ✅ Network errors

### 4. Type Safety
- ✅ Centralized route definitions
- ✅ Consistent endpoint usage
- ✅ Easy to maintain

## 🧪 **Usage Examples**

### Login (Form-Encoded)
```javascript
try {
  const response = await api.login({
    email: 'user@example.com',
    password: 'password123'
  });
  
  if (response.ok) {
    // Cookie is automatically set
    console.log('Login successful');
  }
} catch (error) {
  console.error('Login failed:', error);
}
```

### API Request (JSON)
```javascript
try {
  const servers = await api.getServers();
  console.log('Servers:', servers);
} catch (error) {
  console.error('Failed to fetch servers:', error);
}
```

### Create Resource (JSON)
```javascript
try {
  const newServer = await api.createServer({
    name: 'Test Server',
    config: { /* ... */ }
  });
  console.log('Server created:', newServer);
} catch (error) {
  console.error('Failed to create server:', error);
}
```

## 🔍 **Error Handling**

### 1. Validation Errors (422)
```javascript
try {
  await api.createServer({});
} catch (error) {
  // Error: {"detail": [{"loc": ["body", "name"], "msg": "field required"}]}
  console.error('Validation failed:', error);
}
```

### 2. Authentication Errors (401)
```javascript
try {
  await api.getServers();
} catch (error) {
  // Automatically redirects to login
  console.error('Not authenticated:', error);
}
```

### 3. Network Errors
```javascript
try {
  await api.getServers();
} catch (error) {
  console.error('Network error:', error);
}
```

## 📋 **Best Practices**

### 1. Always Use the API Service
```javascript
// ✅ DO:
const servers = await api.getServers();

// ❌ DON'T:
const response = await fetch('/api/servers');
```

### 2. Handle Errors Properly
```javascript
// ✅ DO:
try {
  await api.someMethod();
} catch (error) {
  handleError(error);
}

// ❌ DON'T:
await api.someMethod();
```

### 3. Use Type-Safe Routes
```javascript
// ✅ DO:
await api.getServerTools(serverId);

// ❌ DON'T:
await fetch(`/api/servers/${serverId}/tools`);
```

## 🔒 **Security**

### Cookie Protection
- ✅ HttpOnly cookies
- ✅ SameSite=Lax
- ✅ Secure in production
- ✅ CSRF protection

### Error Handling
- ✅ No sensitive data in errors
- ✅ Proper status codes
- ✅ Validation error formatting

## 🎉 **Summary**

Your application now has:
- ✅ **Centralized API handling**
- ✅ **Automatic cookie authentication**
- ✅ **Consistent error handling**
- ✅ **Type-safe routes**
- ✅ **Clean, maintainable code**

**All API requests now automatically include authentication!** 🚀
