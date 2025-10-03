const API_BASE_URL = 'http://localhost:9000/api';

export const api = {
  // Connectors
  getConnectors: async () => {
    const response = await fetch(`${API_BASE_URL}/connectors`);
    if (!response.ok) throw new Error('Failed to fetch connectors');
    return response.json();
  },

  getConnectorSchema: async (connectorId) => {
    const response = await fetch(`${API_BASE_URL}/connector-schema/${connectorId}`);
    if (!response.ok) throw new Error('Failed to fetch connector schema');
    return response.json();
  },

  // Servers
  getServers: async () => {
    const response = await fetch(`${API_BASE_URL}/servers`);
    if (!response.ok) throw new Error('Failed to fetch servers');
    return response.json();
  },

  createServer: async (serverData) => {
    const response = await fetch(`${API_BASE_URL}/servers`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(serverData)
    });
    if (!response.ok) throw new Error('Failed to create server');
    return response.json();
  },

  deleteServer: async (serverId) => {
    const response = await fetch(`${API_BASE_URL}/servers/${serverId}`, {
      method: 'DELETE',
    });
    if (!response.ok) throw new Error('Failed to delete server');
    return response.json();
  },

  // Server Tools
  getServerTools: async (serverId) => {
    const response = await fetch(`${API_BASE_URL}/servers/${serverId}/tools`);
    if (!response.ok) throw new Error('Failed to fetch tools');
    return response.json();
  },
};

