import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useMCPClient } from '../../hooks/useMCPClient';
import ServerTokenSelector from '../../components/ServerTokenSelector';

const MCPClientAdvanced = () => {
  const [serverUrl, setServerUrl] = useState('http://localhost:8016/mcp');
  const [, setConnectionStatus] = useState('disconnected');
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [transportType, setTransportType] = useState('streamable-http');
  const [availableTools, setAvailableTools] = useState([]);
  const [selectedTool, setSelectedTool] = useState(null);
  const [toolArguments, setToolArguments] = useState({}); // Store arguments per tool: {toolName: {arg1: value1, arg2: value2}}
  const [selectedServer, setSelectedServer] = useState(null);
  const [selectedToken, setSelectedToken] = useState(null);
  const [useServerSelection, setUseServerSelection] = useState(true);
  const [connectionAttempted, setConnectionAttempted] = useState(false);
  const [copySuccess, setCopySuccess] = useState(false);
  const messagesEndRef = useRef(null);

  const { 
    disconnect, 
    sendMessage, 
    callTool,
    isConnected, 
    isConnecting,
    needsAuth,
    error,
    tools: availableToolsFromHook,
    authUrl,
    authenticate,
    retry,
    clearStorage
  } = useMCPClient(serverUrl, transportType, selectedToken?.token) || {};

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const addMessage = useCallback((type, content, timestamp = new Date()) => {
    setMessages(prev => [...prev, { type, content, timestamp }]);
  }, []);

  const handleServerTokenSelect = async (server, token) => {
    console.log('handleServerTokenSelect called with:', { 
      server: server?.server_name, 
      token: token ? `${token.token.substring(0, 20)}...` : 'null' 
    });

    console.log('server############## ', server);
    
    // If we're currently connected, disconnect first
    if (isConnected) {
      try {
        await disconnect();
        addMessage('system', 'Disconnected from previous server');
      } catch (err) {
        console.warn('Failed to disconnect from previous server:', err);
      }
    }
    
    setSelectedServer(server);
    setSelectedToken(token);
    setConnectionAttempted(false); // Reset connection attempt flag
    
    // Use the server_url from the server data, or fallback to a default
    const serverUrl = (typeof server.server_url === 'string' && server.server_url.trim()) 
      ? `${server.server_url.trim()}/mcp/${server.id}`
      : `http://localhost:8016/mcp`;
    setServerUrl(serverUrl);
    
    const tokenPreview = token && typeof token.token === 'string' 
      ? token.token.substring(0, 20) + '...' 
      : 'invalid token';
    addMessage('system', `Selected server: ${server.server_name} with token: ${tokenPreview}`);
    addMessage('system', `Server URL set to: ${serverUrl}`);
    addMessage('system', 'Click Connect to establish connection with the new server');
  };

  // Add helpful message about testing
  useEffect(() => {
    addMessage('system', 'MCP Client ready! Enter a server URL to connect.');
    addMessage('system', '💡 Tip: Make sure your MCP server is running and accessible.');
  }, [addMessage]);

  // Debug selectedToken changes
  useEffect(() => {
    const tokenPreview = selectedToken && typeof selectedToken.token === 'string' 
      ? `${selectedToken.token.substring(0, 20)}...` 
      : 'null';
    console.log('selectedToken changed:', tokenPreview);
  }, [selectedToken]);

  // Update available tools when they change from the hook
  useEffect(() => {
    if (availableToolsFromHook && Array.isArray(availableToolsFromHook) && availableToolsFromHook.length > 0) {
      setAvailableTools(availableToolsFromHook);
      addMessage('system', `Loaded ${availableToolsFromHook.length} available tools`);
    }
  }, [availableToolsFromHook, addMessage]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Update connection status based on hook state
  useEffect(() => {
    if (isConnected) {
      setConnectionStatus('connected');
      setConnectionAttempted(true);
      addMessage('system', 'Connected to MCP server');
    } else if (isConnecting) {
      setConnectionStatus('connecting');
      addMessage('system', 'Connecting to MCP server...');
    } else if (needsAuth) {
      setConnectionStatus('authenticating');
      addMessage('system', 'Authentication required');
    } else {
      setConnectionStatus('disconnected');
      setAvailableTools([]);
      // Only reset connectionAttempted if we were previously connected
      if (connectionAttempted) {
        setConnectionAttempted(false);
      }
    }
  }, [isConnected, isConnecting, needsAuth, addMessage, connectionAttempted]);

  useEffect(() => {
    if (error) {
      let errorMessage = `Error: ${error}`;
      
      // Provide specific guidance for common MCP errors
      if (error.includes('Missing session ID')) {
        errorMessage += '\n\n💡 This usually means the MCP server requires proper session initialization. Try:';
        errorMessage += '\n• Ensure the server URL is correct and accessible';
        errorMessage += '\n• Check if the server requires authentication';
        errorMessage += '\n• Verify the server is running and accepting MCP connections';
      } else if (error.includes('HTTP 400')) {
        errorMessage += '\n\n💡 Bad Request error. This might indicate:';
        errorMessage += '\n• The server URL format is incorrect';
        errorMessage += '\n• The server doesn\'t support the requested transport type';
        errorMessage += '\n• Missing required headers or parameters';
      }
      
      addMessage('error', errorMessage);
    }
  }, [error, addMessage]);

  const handleConnect = async () => {
    try {
      setConnectionAttempted(true);
      addMessage('system', `Connecting to ${serverUrl} using ${transportType}...`);
      
      // If we're already connected, disconnect first
      if (isConnected) {
        await disconnect();
        addMessage('system', 'Disconnected from previous connection');
      }
      
      // The hook automatically connects when URL/token changes
      // We need to trigger a reconnection by updating the URL slightly
      const currentUrl = serverUrl;
      setServerUrl(''); // Clear URL briefly
      setTimeout(() => {
        setServerUrl(currentUrl); // Set it back to trigger connection
      }, 100);
      
      if (needsAuth && authUrl) {
        authenticate();
      } else {
        addMessage('system', 'Connection initiated...');
      }
    } catch (err) {
      addMessage('error', `Connection failed: ${err.message}`);
      setConnectionAttempted(false);
    }
  };

  const handleDisconnect = async () => {
    try {
      await disconnect();
      // Clear any stored authentication data
      if (clearStorage) {
        clearStorage();
      }
      addMessage('system', 'Disconnected from MCP server');
      setConnectionStatus('disconnected');
      setConnectionAttempted(false);
      setAvailableTools([]);
      setSelectedTool(null);
      setToolArguments({}); // Clear all tool arguments
    } catch (err) {
      addMessage('error', `Disconnect failed: ${err.message}`);
    }
  };

  const handleRetry = async () => {
    try {
      addMessage('system', 'Retrying connection...');
      setConnectionAttempted(true);
      
      // If we're connected, disconnect first
      if (isConnected) {
        await disconnect();
        addMessage('system', 'Disconnected for retry');
      }
      
      // Trigger a new connection attempt
      const currentUrl = serverUrl;
      setServerUrl(''); // Clear URL briefly
      setTimeout(() => {
        setServerUrl(currentUrl); // Set it back to trigger connection
      }, 100);
      
      retry();
    } catch (err) {
      addMessage('error', `Retry failed: ${err.message}`);
      setConnectionAttempted(false);
    }
  };

  const handleAuthenticate = () => {
    if (authUrl) {
      window.open(authUrl, '_blank');
      addMessage('system', 'Authentication window opened');
    } else {
      authenticate();
    }
  };

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || !isConnected) return;

    try {
      addMessage('user', inputMessage);
      const response = await sendMessage(inputMessage);
      addMessage('server', response);
      setInputMessage('');
    } catch (err) {
      addMessage('error', `Send failed: ${err.message}`);
    }
  };

  // Convert string arguments to proper types based on JSON schema
  const convertArgumentsToProperTypes = (args, schema) => {
    if (!schema || !schema.properties) {
      return args;
    }

    const converted = {};
    
    Object.entries(args).forEach(([key, value]) => {
      const prop = schema.properties[key];
      if (!prop || value === '' || value === null || value === undefined) {
        converted[key] = value;
        return;
      }

      switch (prop.type) {
        case 'integer':
          const intValue = parseInt(value, 10);
          if (isNaN(intValue)) {
            console.warn(`Invalid integer value for ${key}: ${value}`);
            converted[key] = value; // Keep original value if conversion fails
          } else {
            converted[key] = intValue;
          }
          break;
        case 'number':
          const floatValue = parseFloat(value);
          if (isNaN(floatValue)) {
            console.warn(`Invalid number value for ${key}: ${value}`);
            converted[key] = value; // Keep original value if conversion fails
          } else {
            converted[key] = floatValue;
          }
          break;
        case 'boolean':
          // Handle various boolean representations
          if (typeof value === 'string') {
            converted[key] = value.toLowerCase() === 'true' || value === '1';
          } else {
            converted[key] = Boolean(value);
          }
          break;
        case 'array':
          // Try to parse as JSON array, fallback to string
          try {
            converted[key] = JSON.parse(value);
          } catch {
            converted[key] = value;
          }
          break;
        case 'object':
          // Try to parse as JSON object, fallback to string
          try {
            converted[key] = JSON.parse(value);
          } catch {
            converted[key] = value;
          }
          break;
        default:
          // For string and other types, keep as is
          converted[key] = value;
      }
    });

    return converted;
  };

  const handleCallTool = async () => {
    if (!selectedTool || !isConnected) return;

    try {
      addMessage('user', `Calling tool: ${selectedTool.name}`);
      
      // Get arguments for the selected tool
      const currentToolArgs = toolArguments[selectedTool.name] || {};
      
      // Convert tool arguments to proper types based on schema
      const convertedArguments = convertArgumentsToProperTypes(currentToolArgs, selectedTool.inputSchema);
      
      console.log('Original arguments:', currentToolArgs);
      console.log('Converted arguments:', convertedArguments);
      
      const result = await callTool(selectedTool.name, convertedArguments);
      addMessage('server', `Tool result: ${JSON.stringify(result, null, 2)}`);
    } catch (err) {
      addMessage('error', `Tool call failed: ${err.message}`);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleCopyServerConfig = async () => {
    if (!selectedServer || !selectedToken) {
      addMessage('error', 'No server or token selected');
      return;
    }

    try {
      // Generate the server URL with server ID
      const baseUrl = (typeof selectedServer.server_url === 'string' && selectedServer.server_url.trim()) 
        ? selectedServer.server_url.trim() 
        : `http://localhost:8016`;
      const serverUrl = `${baseUrl}/mcp/${selectedServer.id}`;

      const serverConfig = {
        [selectedServer.server_name]: {
          url: serverUrl,
          headers: {
            "Authorization": `Bearer ${selectedToken.token}`
          }
        }
      };

      const configText = JSON.stringify(serverConfig, null, 2);
      await navigator.clipboard.writeText(configText);
      
      setCopySuccess(true);
      addMessage('system', 'Server configuration copied to clipboard!');
      
      // Reset copy success after 2 seconds
      setTimeout(() => setCopySuccess(false), 2000);
    } catch (err) {
      console.error('Failed to copy server config:', err);
      addMessage('error', `Failed to copy configuration: ${err.message}`);
    }
  };

  const renderToolArguments = (tool) => {
    if (!tool.inputSchema || !tool.inputSchema.properties) {
      return <div className="text-sm text-gray-500">No arguments required</div>;
    }

    return Object.entries(tool.inputSchema.properties).map(([key, prop]) => {
      const getInputType = () => {
        switch (prop.type) {
          case 'integer':
          case 'number':
            return 'number';
          case 'boolean':
            return 'checkbox';
          default:
            return 'text';
        }
      };

      const getInputValue = () => {
        const currentToolArgs = toolArguments[tool.name] || {};
        const value = currentToolArgs[key];
        if (prop.type === 'boolean') {
          return value === true || value === 'true';
        }
        return value || '';
      };

      const handleInputChange = (e) => {
        const newValue = e.target.type === 'checkbox' ? e.target.checked : e.target.value;
        setToolArguments(prev => ({
          ...prev,
          [tool.name]: {
            ...prev[tool.name],
            [key]: newValue
          }
        }));
      };

      return (
        <div key={key} className="mb-3">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            {key} {tool.inputSchema.required?.includes(key) && <span className="text-red-500">*</span>}
            <span className="text-xs text-gray-500 ml-2">({prop.type})</span>
          </label>
          
          {prop.type === 'boolean' ? (
            <div className="flex items-center">
              <input
                type="checkbox"
                checked={getInputValue()}
                onChange={handleInputChange}
                className="w-4 h-4 text-purple-600 focus:ring-purple-500 border-gray-300 rounded"
              />
              <span className="ml-2 text-sm text-gray-700">
                {getInputValue() ? 'True' : 'False'}
              </span>
            </div>
          ) : (
            <input
              type={getInputType()}
              value={getInputValue()}
              onChange={handleInputChange}
              placeholder={prop.description || `Enter ${key}`}
              step={prop.type === 'integer' ? '1' : undefined}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-purple-500 focus:border-purple-500"
            />
          )}
          
          {prop.description && (
            <div className="text-xs text-gray-500 mt-1">{prop.description}</div>
          )}
        </div>
      );
    });
  };

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">MCP Client</h1>
        <p className="text-gray-600">Connect to MCP servers using HTTP streaming or SSE transport</p>
      </div>

      {/* Connection Panel */}
      <div className="bg-white rounded-lg border border-gray-200 p-6 mb-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Connection Settings</h2>
        
        {/* Connection Mode Toggle */}
        <div className="mb-6">
          <div className="flex items-center space-x-4">
            <label className="flex items-center">
              <input
                type="radio"
                name="connectionMode"
                checked={useServerSelection}
                onChange={() => setUseServerSelection(true)}
                className="w-4 h-4 text-purple-600 focus:ring-purple-500"
              />
              <span className="ml-2 text-sm font-medium text-gray-700">Select from existing servers</span>
            </label>
            <label className="flex items-center">
              <input
                type="radio"
                name="connectionMode"
                checked={!useServerSelection}
                onChange={() => setUseServerSelection(false)}
                className="w-4 h-4 text-purple-600 focus:ring-purple-500"
              />
              <span className="ml-2 text-sm font-medium text-gray-700">Manual URL entry</span>
            </label>
          </div>
        </div>

        {useServerSelection ? (
          /* Server Selection Mode */
          <div className="mb-6">
            <ServerTokenSelector
              onServerTokenSelect={handleServerTokenSelect}
              selectedServer={selectedServer}
              selectedToken={selectedToken}
            />
            
            {/* Copy Server Configuration Button */}
            {selectedServer && selectedToken && (
              <div className="mt-4 p-4 bg-gray-50 rounded-lg border border-gray-200">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-sm font-medium text-gray-900">Server Configuration</h3>
                    <p className="text-xs text-gray-600 mt-1">
                      Copy this configuration for client-side tools
                    </p>
                  </div>
                  <button
                    onClick={handleCopyServerConfig}
                    disabled={copySuccess}
                    className={`px-3 py-2 text-sm font-medium rounded-md transition-colors flex items-center ${
                      copySuccess
                        ? 'bg-green-100 text-green-700 border border-green-300'
                        : 'bg-purple-100 text-purple-700 border border-purple-300 hover:bg-purple-200'
                    }`}
                  >
                    {copySuccess ? (
                      <>
                        <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                        Copied!
                      </>
                    ) : (
                      <>
                        <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                        </svg>
                        Copy Config
                      </>
                    )}
                  </button>
                </div>
              </div>
            )}
          </div>
        ) : (
          /* Manual URL Entry Mode */
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            <div>
              <label htmlFor="serverUrl" className="block text-sm font-medium text-gray-700 mb-2">
                Server URL
              </label>
              <input
                type="url"
                id="serverUrl"
                value={serverUrl}
                onChange={(e) => setServerUrl(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-purple-500 focus:border-purple-500"
                placeholder="http://localhost:8016/mcp"
              />
            </div>
            
            <div>
              <label htmlFor="transportType" className="block text-sm font-medium text-gray-700 mb-2">
                Transport Type
              </label>
              <select
                id="transportType"
                value={transportType}
                onChange={(e) => setTransportType(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-purple-500 focus:border-purple-500"
              >
                <option value="streamable-http">Streamable HTTP</option>
                <option value="sse">Server-Sent Events (SSE)</option>
              </select>
            </div>
          </div>
        )}

        {/* Transport Type for Server Selection Mode */}
        {useServerSelection && (
          <div className="mb-4">
            <label htmlFor="transportType" className="block text-sm font-medium text-gray-700 mb-2">
              Transport Type
            </label>
            <select
              id="transportType"
              value={transportType}
              onChange={(e) => setTransportType(e.target.value)}
              className="w-full md:w-1/3 px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-purple-500 focus:border-purple-500"
            >
              <option value="streamable-http">Streamable HTTP</option>
              <option value="sse">Server-Sent Events (SSE)</option>
            </select>
          </div>
        )}

        <div className="flex items-center space-x-4">
          {needsAuth ? (
            <button
              onClick={handleAuthenticate}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              Authenticate
            </button>
          ) : (
            <button
              onClick={handleConnect}
              disabled={isConnecting || isConnected || (useServerSelection && (!selectedServer || !selectedToken)) || (!useServerSelection && !serverUrl.trim())}
              className="px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isConnecting ? 'Connecting...' : 'Connect'}
            </button>
          )}
          
          <button
            onClick={handleDisconnect}
            disabled={!isConnected}
            className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Disconnect
          </button>

          {error && !isConnected && !isConnecting && (
            <button
              onClick={handleRetry}
              disabled={isConnecting}
              className="px-4 py-2 bg-orange-600 text-white rounded-md hover:bg-orange-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Retry
            </button>
          )}
          
          <div className={`px-3 py-2 rounded-full text-sm font-medium ${
            isConnected 
              ? 'bg-green-100 text-green-800' 
              : isConnecting
              ? 'bg-yellow-100 text-yellow-800'
              : needsAuth
              ? 'bg-blue-100 text-blue-800'
              : 'bg-red-100 text-red-800'
          }`}>
            {isConnected ? '🟢 Connected' : 
             isConnecting ? '🟡 Connecting...' : 
             needsAuth ? '🔵 Auth Required' :
             '🔴 Disconnected'}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Tools Panel */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Available Tools</h2>
          
          {!availableTools || availableTools.length === 0 ? (
            <div className="text-center text-gray-500 py-8">
              {isConnected ? 'No tools available' : 'Connect to a server to see available tools'}
            </div>
          ) : (
            <div className="max-h-80 overflow-y-auto space-y-2 mb-4 pr-2">
              {(availableTools || []).map((tool, index) => (
                <button
                  key={index}
                  onClick={() => setSelectedTool(tool)}
                  className={`w-full text-left p-3 rounded-lg border transition-colors ${
                    selectedTool?.name === tool.name
                      ? 'border-purple-500 bg-purple-50'
                      : 'border-gray-200 hover:border-purple-200 hover:bg-gray-50'
                  }`}
                >
                  <div className="font-medium text-gray-900">{tool.name}</div>
                  <div className="text-sm text-gray-600">{tool.description}</div>
                </button>
              ))}
            </div>
          )}

          {selectedTool && (
            <div className="border-t pt-4">
              <h3 className="font-medium text-gray-900 mb-3">Tool Arguments</h3>
              {renderToolArguments(selectedTool)}
              <button
                onClick={handleCallTool}
                disabled={!isConnected}
                className="w-full px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Call Tool
              </button>
            </div>
          )}
        </div>

        {/* Chat Interface */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">MCP Communication</h2>
          
          {/* Messages */}
          <div className="h-96 overflow-y-auto border border-gray-200 rounded-md p-4 mb-4 bg-gray-50">
            {!messages || messages.length === 0 ? (
              <div className="text-center text-gray-500 py-8">
                No messages yet. Connect to a server and start communicating.
              </div>
            ) : (
              (messages || []).map((message, index) => (
                <div key={index} className={`mb-3 ${
                  message.type === 'user' ? 'text-right' : 
                  message.type === 'error' ? 'text-red-600' : 'text-left'
                }`}>
                  <div className={`inline-block max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                    message.type === 'user' 
                      ? 'bg-purple-600 text-white' 
                      : message.type === 'error'
                      ? 'bg-red-100 text-red-800'
                      : 'bg-white text-gray-800 border'
                  }`}>
                    <div className="text-sm whitespace-pre-wrap">{message.content}</div>
                    <div className={`text-xs mt-1 ${
                      message.type === 'user' ? 'text-purple-100' : 'text-gray-500'
                    }`}>
                      {message.timestamp.toLocaleTimeString()}
                    </div>
                  </div>
                </div>
              ))
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div className="flex space-x-2">
            <input
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder={isConnected ? "Type your message..." : "Connect to a server first"}
              disabled={!isConnected}
              className="flex-1 px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-purple-500 focus:border-purple-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
            />
            <button
              onClick={handleSendMessage}
              disabled={!isConnected || !inputMessage.trim()}
              className="px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Send
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MCPClientAdvanced;
