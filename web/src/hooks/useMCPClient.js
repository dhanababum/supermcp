import React from 'react';
import { useMcp } from 'use-mcp/react';

export const useMCPClient = (serverUrl, transportType = 'auto', authToken = null) => {
  // Ensure the URL is properly formatted for MCP
  const normalizedUrl = React.useMemo(() => {
    if (!serverUrl || typeof serverUrl !== 'string') {
      console.warn('Invalid serverUrl provided to useMCPClient:', serverUrl);
      return null;
    }
    return serverUrl.endsWith('/') ? serverUrl.slice(0, -1) : serverUrl;
  }, [serverUrl]);
  
  const debug = true; // Enable debug logging
  
  // Create mcpOptions with proper dependency tracking
  const mcpOptions = React.useMemo(() => {
    // Don't create options if we don't have a valid URL
    if (!normalizedUrl) {
      return null;
    }

    const options = {
      url: normalizedUrl,
      transportType: transportType === 'streamable-http' ? 'http' : transportType === 'sse' ? 'sse' : 'auto',
      debug,
      // Disable all automatic retry mechanisms
      autoRetry: false,
      autoReconnect: false, // Disable automatic reconnection
      preventAutoAuth: true,
      // OAuth configuration for proper session handling
      clientName: 'forge-mcp-client',
      clientUri: typeof window !== 'undefined' ? window.location.origin : 'http://localhost:3000',
      callbackUrl: typeof window !== 'undefined' ? `${window.location.origin}/oauth/callback` : 'http://localhost:3000/oauth/callback',
      storageKeyPrefix: 'forge-mcp',
      // Add client configuration for better session handling
      clientConfig: {
        name: 'forge-mcp-client',
        version: '1.0.0'
      }
    };

    // Add authentication headers if token is provided
    if (authToken) {
      options.customHeaders = {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json'
      };
    } else {
      options.customHeaders = {
        'Content-Type': 'application/json'
      };
    }

    console.log('options######## ', options);
    return options;
  }, [normalizedUrl, transportType, authToken, debug]);

  // Always call useMcp with valid options (React hooks must be called unconditionally)
  const mcpResult = useMcp(mcpOptions || {
    url: 'http://localhost:9000', // Default URL to prevent errors
    transportType: 'auto',
    debug: false,
    autoRetry: false,
    autoReconnect: false,
    preventAutoAuth: true,
    clientName: 'forge-mcp-client',
    clientUri: typeof window !== 'undefined' ? window.location.origin : 'http://localhost:3000',
    callbackUrl: typeof window !== 'undefined' ? `${window.location.origin}/oauth/callback` : 'http://localhost:3000/oauth/callback',
    storageKeyPrefix: 'forge-mcp',
    clientConfig: {
      name: 'forge-mcp-client',
      version: '1.0.0'
    },
    customHeaders: {
      'Content-Type': 'application/json'
    }
  });
  
  // Safely destructure with fallbacks
  const {
    tools = [],
    resources = [],
    resourceTemplates = [],
    prompts = [],
    state = 'disconnected',
    error = null,
    authUrl = null,
    log = [],
    callTool = () => Promise.resolve(null),
    listResources = () => Promise.resolve([]),
    readResource = () => Promise.resolve(null),
    listPrompts = () => Promise.resolve([]),
    getPrompt = () => Promise.resolve(null),
    retry = () => {},
    disconnect = () => Promise.resolve(),
    authenticate = () => Promise.resolve(),
    clearStorage = () => {}
  } = mcpResult || {};

  // Debug the useMcp hook state
  React.useEffect(() => {
    if (debug) {
      console.log('useMcp hook state:', { 
        state, 
        error, 
        toolsCount: tools?.length || 0,
        authUrl: authUrl ? 'present' : 'none',
        hasAuthToken: !!authToken
      });
    }
  }, [state, error, tools, authUrl, authToken, debug]);

  // Map the use-mcp state to our expected interface
  const isConnected = state === 'ready' && !!normalizedUrl;
  const isConnecting = (state === 'connecting' || state === 'loading' || state === 'discovering') && !!normalizedUrl;
  const needsAuth = state === 'pending_auth' || state === 'authenticating';

  // Enhanced error handling
  const enhancedError = error || 
    (!normalizedUrl ? 'Invalid server URL provided' : null) ||
    (state === 'failed' ? 'Connection failed' : null);
  
  // Log connection state changes for debugging
  React.useEffect(() => {
    if (debug) {
      console.log(`[MCP Client] State changed to: ${state}`, { 
        url: normalizedUrl, 
        transportType: mcpOptions?.transportType || 'none',
        error: enhancedError 
      });
    }
  }, [state, normalizedUrl, mcpOptions?.transportType, enhancedError, debug]);

  // Legacy compatibility methods
  const connect = async (url, transport) => {
    // The use-mcp hook automatically connects when the URL changes
    // This is just for compatibility
    console.log('use-mcp automatically handles connection');
  };

  const getTools = async () => {
    return tools || [];
  };

  const sendMessage = async (message) => {
    if (!normalizedUrl) {
      throw new Error('Cannot send message: Invalid server URL');
    }
    // For compatibility, we'll try to call a tool named 'echo' if it exists
    const echoTool = tools?.find(tool => tool.name === 'echo');
    if (echoTool) {
      return await callTool('echo', { message });
    }
    return 'Message sent (no echo tool available)';
  };

  // Manual retry function - only retries when explicitly called
  const manualRetry = () => {
    console.log('[MCP Client] Manual retry requested');
    if (retry) {
      retry();
    }
  };

  return {
    // Legacy compatibility
    client: null, // use-mcp doesn't expose the raw client
    isConnected,
    isConnecting,
    needsAuth,
    error: enhancedError,
    connect,
    disconnect,
    sendMessage,
    getTools,
    callTool,
    
    // New use-mcp specific properties
    tools,
    resources,
    resourceTemplates,
    prompts,
    state,
    authUrl,
    log,
    listResources,
    readResource,
    listPrompts,
    getPrompt,
    retry: manualRetry, // Use manual retry instead of automatic
    authenticate,
    clearStorage
  };
};
