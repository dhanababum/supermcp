// Use environment variable for API URL, fallback to localhost for development
export const API_BASE_URL = window.APP_CONFIG?.API_BASE_URL || 
                     process.env.REACT_APP_API_BASE_URL || 
                     'http://localhost:9000';
const IGNORE_REDIRECT_ENDPOINTS = ['/auth/cookie/login', '/auth/logout', '/users/me'];
const API_ROUTES = {
  // Auth endpoints
  login: '/auth/cookie/login',
  logout: '/auth/logout',
  me: '/users/me',
  register: '/auth/register',
  
  // API endpoints
  connectors: '/api/connectors',
  registerConnector: '/api/connectors/register',
  activateConnector: '/api/connectors/activate',
  connectorSchema: (id) => `/api/connector-schema/${id}`,
  servers: '/api/servers',
  server: (id) => `/api/servers/${id}`,
  serverTools: (id) => `/api/servers/${id}/tools`,
};

// Default fetch options with credentials
const defaultFetchOptions = {
  credentials: 'include', // Always include cookies
  headers: {
    'Accept': 'application/json',
    'Content-Type': 'application/json',
  },
};

// Helper function to make API requests
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

    // Special case: form-encoded login request
    if (endpoint === API_ROUTES.login && options.isFormEncoded) {
      return response;
    }

    // Handle 204 No Content
    if (response.status === 204) {
      return { ok: true };
    }

    // Try to parse JSON response
    let data;
    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      data = await response.json();
    }

    if (!response.ok) {
      // Handle 401 Unauthorized
      if (response.status === 401) {
        if (!IGNORE_REDIRECT_ENDPOINTS.includes(endpoint)) {
          window.location.href = '/auth/login';
        }
        throw new Error('Unauthorized - redirecting to login');
      }
      
      // Handle validation errors
      if (response.status === 422 && data?.detail) {
        throw new Error(JSON.stringify(data.detail));
      }
      
      // Handle other errors
      throw new Error(data?.detail || `HTTP ${response.status}: ${response.statusText}`);
    }

    return data;
  } catch (error) {
    console.error('API Request failed:', error);
    throw error;
  }
};

export const api = {
  // Auth endpoints
  login: async (formData) => {
    // Special case: form-encoded login
    const body = new URLSearchParams();
    body.append('username', formData.email);
    body.append('password', formData.password);

    return apiRequest(API_ROUTES.login, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: body.toString(),
      isFormEncoded: true,
    });
  },

  logout: async () => {
    return apiRequest(API_ROUTES.logout, { method: 'POST' });
  },

  checkAuth: async () => {
    try {
      await apiRequest(API_ROUTES.me);
      return true;
    } catch (error) {
      return false;
    }
  },

  getMe: async () => {
    return apiRequest(API_ROUTES.me);
  },

  register: async (userData) => {
    return apiRequest(API_ROUTES.register, {
      method: 'POST',
      body: JSON.stringify(userData),
    });
  },

  // Connectors
  getConnectors: async () => {
    return apiRequest(API_ROUTES.connectors);
  },

  createConnector: async (connectorData) => {
    return apiRequest(API_ROUTES.connectors, {
      method: 'POST',
      body: JSON.stringify(connectorData),
    });
  },

  // Two-step connector registration
  registerConnector: async (connectorData) => {
    return apiRequest(API_ROUTES.registerConnector, {
      method: 'POST',
      body: JSON.stringify(connectorData),
    });
  },

  activateConnector: async (activationData) => {
    return apiRequest(API_ROUTES.activateConnector, {
      method: 'POST',
      body: JSON.stringify(activationData),
    });
  },

  deleteConnector: async (connectorId) => {
    return apiRequest(`${API_ROUTES.connectors}/${connectorId}`, {
      method: 'DELETE',
    });
  },

  updateConnectorMode: async (connectorId, mode) => {
    return apiRequest(`${API_ROUTES.connectors}/${connectorId}/mode`, {
      method: 'PATCH',
      body: JSON.stringify({ mode }),
    });
  },

  getConnectorSchema: async (connectorId) => {
    return apiRequest(API_ROUTES.connectorSchema(connectorId));
  },

  getConnectorTemplates: async (connectorId) => {
    return apiRequest(`/api/connectors/${connectorId}/templates`);
  },

  // Connector Access Management (Superuser only)
  grantConnectorAccess: async (userId, connectorId) => {
    return apiRequest('/api/connectors/grant-access', {
      method: 'POST',
      body: JSON.stringify({
        user_id: userId,
        connector_id: connectorId,
      }),
    });
  },

  revokeConnectorAccess: async (userId, connectorId) => {
    return apiRequest('/api/connectors/revoke-access', {
      method: 'POST',
      body: JSON.stringify({
        user_id: userId,
        connector_id: connectorId,
      }),
    });
  },

  getConnectorAccess: async (connectorId) => {
    return apiRequest(`/api/connectors/${connectorId}/access`);
  },

  // User Management (Superuser only)
  searchUsers: async (query) => {
    return apiRequest(`/api/users/search?q=${encodeURIComponent(query)}`);
  },

  getAllUsers: async () => {
    return apiRequest('/api/users');
  },

  // Servers
  getServers: async () => {
    return apiRequest(API_ROUTES.servers);
  },

  createServer: async (serverData) => {
    return apiRequest(API_ROUTES.servers, {
      method: 'POST',
      body: JSON.stringify(serverData),
    });
  },

  deleteServer: async (serverId) => {
    return apiRequest(API_ROUTES.server(serverId), {
      method: 'DELETE',
    });
  },

  getServer: async (serverId) => {
    return apiRequest(API_ROUTES.server(serverId));
  },

  updateServer: async (serverId, serverData) => {
    return apiRequest(API_ROUTES.server(serverId), {
      method: 'PUT',
      body: JSON.stringify(serverData),
    });
  },

  // Server Tools
  getServerTools: async (serverId) => {
    return apiRequest(API_ROUTES.serverTools(serverId));
  },

  createServerTool: async (serverId, toolData) => {
    return apiRequest(API_ROUTES.serverTools(serverId), {
      method: 'POST',
      body: JSON.stringify(toolData),
    });
  },

  // Server Tokens
  getServerTokens: async (serverId) => {
    return apiRequest(`/api/servers/${serverId}/tokens`);
  },

  createServerToken: async (serverId, tokenData) => {
    return apiRequest(`/api/servers/${serverId}/tokens`, {
      method: 'POST',
      body: JSON.stringify(tokenData || {}),
    });
  },

  deleteServerToken: async (serverId, tokenId) => {
    return apiRequest(`/api/servers/${serverId}/tokens/${tokenId}`, {
      method: 'DELETE',
    });
  },

  updateServerToken: async (serverId, tokenId, updateData) => {
    return apiRequest(`/api/servers/${serverId}/tokens/${tokenId}`, {
      method: 'PATCH',
      body: JSON.stringify(updateData),
    });
  },
};

