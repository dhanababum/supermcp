import React from 'react';
import { useMcp } from 'use-mcp/react';

export const useMCPClient = (serverUrl, transportType = 'auto') => {
  // Ensure the URL is properly formatted for MCP
  const normalizedUrl = serverUrl.endsWith('/') ? serverUrl.slice(0, -1) : serverUrl;
  
  const debug = true; // Enable debug logging
  
  const mcpOptions = {
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

  const {
    tools,
    resources,
    resourceTemplates,
    prompts,
    state,
    error,
    authUrl,
    log,
    callTool,
    listResources,
    readResource,
    listPrompts,
    getPrompt,
    retry,
    disconnect,
    authenticate,
    clearStorage
  } = useMcp(mcpOptions);

  // Map the use-mcp state to our expected interface
  const isConnected = state === 'ready';
  const isConnecting = state === 'connecting' || state === 'loading' || state === 'discovering';
  const needsAuth = state === 'pending_auth' || state === 'authenticating';

  // Enhanced error handling
  const enhancedError = error || (state === 'failed' ? 'Connection failed' : null);
  
  // Log connection state changes for debugging
  React.useEffect(() => {
    if (debug) {
      console.log(`[MCP Client] State changed to: ${state}`, { 
        url: normalizedUrl, 
        transportType: mcpOptions.transportType,
        error: enhancedError 
      });
    }
  }, [state, normalizedUrl, mcpOptions.transportType, enhancedError, debug]);

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
