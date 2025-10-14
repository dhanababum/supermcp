import React, { useState, useEffect, useCallback } from 'react';
import { api } from '../../../services/api';

const ServerConfigModal = ({ server, isOpen, onClose }) => {
  const [config, setConfig] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [copied, setCopied] = useState(false);

  const fetchServerConfig = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      // Fetch server tokens to get the bearer token
      const tokens = await api.getServerTokens(server.id);
      console.log('server......', server);
      if (tokens && tokens.length > 0) {
        const token = tokens[0]; // Use the first token
        // Generate the server URL with server ID
        const baseUrl = (typeof server.server_url === 'string' && server.server_url.trim()) 
          ? server.server_url.trim() 
          : `http://localhost:8016`;
        const serverUrl = `${baseUrl}/mcp/${server.id}`;
        
        const serverConfig = {
          [server.server_name]: {
            url: serverUrl,
            headers: {
              Authorization: `Bearer ${token.token}`
            }
          }
        };
        
        setConfig(serverConfig);
      } else {
        setError('No tokens found for this server');
      }
    } catch (err) {
      console.error('Error fetching server config:', err);
      setError('Failed to load server configuration');
    } finally {
      setLoading(false);
    }
  }, [server]);

  useEffect(() => {
    if (isOpen && server) {
      fetchServerConfig();
    }
  }, [isOpen, server, fetchServerConfig]);

  const copyToClipboard = async () => {
    if (config) {
      try {
        await navigator.clipboard.writeText(JSON.stringify(config, null, 2));
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
      } catch (err) {
        console.error('Failed to copy to clipboard:', err);
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = JSON.stringify(config, null, 2);
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
      }
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">Server Configuration</h2>
            <p className="text-sm text-gray-600 mt-1">{server?.server_name}</p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-140px)]">
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600"></div>
              <span className="ml-3 text-gray-600">Loading configuration...</span>
            </div>
          ) : error ? (
            <div className="text-center py-8">
              <div className="text-red-600 mb-4">
                <svg className="w-12 h-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <p className="text-red-600 font-medium">{error}</p>
              <button
                onClick={fetchServerConfig}
                className="mt-4 px-4 py-2 bg-red-600 text-white text-sm font-medium rounded-lg hover:bg-red-700"
              >
                Retry
              </button>
            </div>
          ) : config ? (
            <div>
              <div className="mb-4">
                <p className="text-sm text-gray-600 mb-2">
                  Copy this configuration to use in your MCP client (Cursor, VSCode, etc.):
                </p>
              </div>
              
              <div className="bg-gray-900 rounded-lg p-4 relative">
                <pre className="text-green-400 text-sm overflow-x-auto">
                  <code>{JSON.stringify(config, null, 2)}</code>
                </pre>
                
                <button
                  onClick={copyToClipboard}
                  className={`absolute top-2 right-2 px-3 py-1 text-xs font-medium rounded transition-colors ${
                    copied
                      ? 'bg-green-600 text-white'
                      : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                  }`}
                >
                  {copied ? '✓ Copied!' : 'Copy'}
                </button>
              </div>
              
              <div className="mt-4 p-3 bg-blue-50 rounded-lg">
                <div className="flex items-start">
                  <svg className="w-5 h-5 text-blue-600 mt-0.5 mr-2 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <div className="text-sm text-blue-800">
                    <p className="font-medium mb-1">How to use:</p>
                    <ul className="list-disc list-inside space-y-1 text-blue-700">
                      <li>Copy the configuration above</li>
                      <li>Add it to your MCP client's configuration file</li>
                      <li>Restart your MCP client to connect to this server</li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          ) : null}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end p-6 border-t border-gray-200 bg-gray-50">
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-700 text-sm font-medium rounded-lg hover:bg-gray-200 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

export default ServerConfigModal;
