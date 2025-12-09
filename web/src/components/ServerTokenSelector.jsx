import React, { useState, useEffect } from 'react';
import { api } from '../services/api';

const ServerTokenSelector = ({ onServerTokenSelect, selectedServer, selectedToken }) => {
  const [servers, setServers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchServers = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await api.getServersWithTokens();
      
      setServers(response || []);
    } catch (error) {
      console.error('Error fetching servers:', error);
      setError(`Failed to load servers: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchServers();
  }, []);

  const handleServerSelect = (event) => {
    const serverId = event.target.value;
    if (serverId === '0' || serverId === '') {
      // "Select a server" option selected
      return;
    }
    
    const server = servers.find(s => s.id === serverId);
    if (!server) return;
    
    // If server has tokens, select the first active token
    if (server.tokens && server.tokens.length > 0) {
      const activeToken = server.tokens.find(token => token.is_active);
      if (activeToken) {
        onServerTokenSelect(server, activeToken);
      } else {
        setError('No active tokens available for this server');
      }
    } else {
      setError('No tokens available for this server');
    }
  };

  const handleTokenSelect = (event) => {
    const tokenId = parseInt(event.target.value, 10);
    if (tokenId === 0 || !selectedServer) return;
    
    const token = selectedServer.tokens.find(t => t.id === tokenId);
    if (token) {
      onServerTokenSelect(selectedServer, token);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-4">
        <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-brand-600"></div>
        <span className="ml-2 text-surface-600">Loading servers...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-error-50 border border-error-200 rounded-lg">
        <div className="flex items-center">
          <svg className="w-5 h-5 text-error-400 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span className="text-error-700">{error}</span>
        </div>
        <button
          onClick={fetchServers}
          className="mt-2 px-3 py-1 bg-error-600 text-white text-sm rounded hover:bg-error-700 transition-colors"
        >
          Retry
        </button>
      </div>
    );
  }

  if (servers.length === 0) {
    return (
      <div className="p-4 bg-surface-50 border border-surface-200 rounded-lg text-center">
        <svg className="w-8 h-8 text-surface-400 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
        </svg>
        <p className="text-surface-600">No servers available</p>
        <p className="text-sm text-surface-500 mt-1">Create a server first to use MCP client</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-lg font-semibold text-surface-900 mb-3">Select Server & Token</h3>
        <p className="text-sm text-surface-600 mb-4">Choose a server and its authentication token for MCP connection</p>
      </div>

      {/* Server and Token Selection Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Server Selection */}
        <div className="space-y-4">
          <div>
            <label htmlFor="server-select" className="block text-sm font-medium text-surface-700 mb-2">
              Select Server
            </label>
            <select
              id="server-select"
              value={selectedServer?.id || '0'}
              onChange={handleServerSelect}
              className="w-full px-3 py-2 border border-surface-300 rounded-md shadow-sm focus:outline-none focus:ring-brand-500 focus:border-brand-500 bg-white text-surface-900"
            >
              <option value="0">Select a server...</option>
              {servers.map((server) => (
                <option key={server.id} value={server.id}>
                  {server.server_name} (ID: {server.id})
                </option>
              ))}
            </select>
          </div>

          {/* Server Details */}
          {selectedServer && (
            <div className="p-4 bg-brand-50 border border-brand-200 rounded-lg">
              <h4 className="font-semibold text-brand-900 mb-2">{selectedServer.server_name}</h4>
              <div className="text-sm text-surface-600 space-y-1">
                <div><span className="font-medium">ID:</span> {selectedServer.id}</div>
                <div><span className="font-medium">Connector:</span> {selectedServer.connector_id}</div>
                <div><span className="font-medium">Server URL:</span> 
                  <span className="ml-1 font-mono text-xs bg-white px-2 py-1 rounded border border-surface-200">
                    {selectedServer.server_url || 'Not set'}
                  </span>
                </div>
                <div><span className="font-medium">Status:</span> <span className="text-success-600 font-medium">Active</span></div>
                <div><span className="font-medium">Available Tokens:</span> {selectedServer.tokens?.length || 0}</div>
              </div>
            </div>
          )}
        </div>

        {/* Token Selection */}
        <div className="space-y-4">
          {selectedServer && selectedServer.tokens && selectedServer.tokens.length > 0 ? (
            <div>
              <label htmlFor="token-select" className="block text-sm font-medium text-surface-700 mb-2">
                Select Token
              </label>
              <select
                id="token-select"
                value={selectedToken?.id || 0}
                onChange={handleTokenSelect}
                className="w-full px-3 py-2 border border-surface-300 rounded-md shadow-sm focus:outline-none focus:ring-brand-500 focus:border-brand-500 bg-white text-surface-900"
              >
                <option value={0}>Select a token...</option>
                {selectedServer.tokens.map((token) => (
                  <option key={token.id} value={token.id}>
                    {token.token.substring(0, 20)}... - Created: {new Date(token.created_at).toLocaleDateString()}
                    {token.expires_at && ` - Expires: ${new Date(token.expires_at).toLocaleDateString()}`}
                    {!token.is_active && ' (Inactive)'}
                    {token.expires_at && new Date(token.expires_at) < new Date() && ' (Expired)'}
                  </option>
                ))}
              </select>
            </div>
          ) : selectedServer ? (
            <div className="p-4 bg-warning-50 border border-warning-200 rounded-lg">
              <div className="flex items-center">
                <svg className="w-5 h-5 text-warning-400 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.732-.833-2.5 0L4.268 19.5c-.77.833.192 2.5 1.732 2.5z" />
                </svg>
                <div>
                  <h4 className="font-semibold text-warning-800">No Tokens Available</h4>
                  <p className="text-sm text-warning-700">This server has no authentication tokens</p>
                </div>
              </div>
            </div>
          ) : (
            <div className="p-4 bg-surface-50 border border-surface-200 rounded-lg">
              <div className="flex items-center">
                <svg className="w-5 h-5 text-surface-400 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
                </svg>
                <div>
                  <h4 className="font-semibold text-surface-800">Select Server First</h4>
                  <p className="text-sm text-surface-600">Choose a server to see available tokens</p>
                </div>
              </div>
            </div>
          )}

          {/* Token Details */}
          {selectedToken && (
            <div className="p-4 bg-brand-50 border border-brand-200 rounded-lg">
              <h4 className="font-semibold text-brand-900 mb-2">Selected Token</h4>
              <div className="space-y-3">
                <div>
                  <h5 className="text-sm font-medium text-surface-700 mb-1">Token Information</h5>
                  <div className="text-sm text-surface-600 space-y-1">
                    <div><span className="font-medium">Token:</span> <span className="font-mono">{selectedToken.token.substring(0, 30)}...</span></div>
                    <div><span className="font-medium">Status:</span> 
                      <span className={`ml-1 px-2 py-1 text-xs rounded-full ${
                        selectedToken.is_active ? 'bg-success-100 text-success-700' : 'bg-surface-100 text-surface-700'
                      }`}>
                        {selectedToken.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </div>
                  </div>
                </div>
                <div>
                  <h5 className="text-sm font-medium text-surface-700 mb-1">Timeline</h5>
                  <div className="text-sm text-surface-600 space-y-1">
                    <div><span className="font-medium">Created:</span> {new Date(selectedToken.created_at).toLocaleString()}</div>
                    {selectedToken.expires_at && (
                      <div><span className="font-medium">Expires:</span> 
                        <span className={`ml-1 ${new Date(selectedToken.expires_at) < new Date() ? 'text-error-600' : 'text-surface-600'}`}>
                          {new Date(selectedToken.expires_at).toLocaleString()}
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {selectedServer && selectedToken && (
        <div className="p-4 bg-success-50 border border-success-200 rounded-lg">
          <div className="flex items-center">
            <svg className="w-5 h-5 text-success-400 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div>
              <h4 className="font-semibold text-success-800">Ready to Connect</h4>
              <p className="text-sm text-success-700">
                Server: <span className="font-mono">{selectedServer.server_name}</span> | 
                Token: <span className="font-mono">{selectedToken.token.substring(0, 20)}...</span>
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ServerTokenSelector;
