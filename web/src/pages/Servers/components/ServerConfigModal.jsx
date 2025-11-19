import React, { useState, useEffect, useCallback } from 'react';
import { api } from '../../../services/api';
import { Cursor, Claude, Windsurf, Cline } from '@lobehub/icons';

const ServerConfigModal = ({ server, isOpen, onClose }) => {
  const [config, setConfig] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [copied, setCopied] = useState(false);
  const [activeTab, setActiveTab] = useState('auto'); // 'auto' or 'manual'
  const [oneClickStatus, setOneClickStatus] = useState({});

  const fetchServerConfig = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      // Fetch server tokens to get the bearer token
      const tokens = await api.getServerTokens(server.id);
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

  const handleOneClickInstall = async (agentName) => {
    if (!config) return;
    
    setOneClickStatus({ ...oneClickStatus, [agentName]: 'loading' });
    
    try {
      // Get the server name (first key in config object)
      const serverName = Object.keys(config)[0];
      const serverConfig = config[serverName];
      
      // For agents that support deep links
      if (agentName === 'cursor') {
        // Create the config object in the format expected by Cursor
        const cursorConfig = {
          type: "http",
          description: `${serverName} - MCP Server`,
          url: serverConfig.url,
          headers: serverConfig.headers
        };
        
        // Base64 encode the configuration
        const configJson = JSON.stringify(cursorConfig);
        const base64Config = btoa(configJson);
        
        // Generate deep link
        const deepLink = `cursor://anysphere.cursor-deeplink/mcp/install?name=${encodeURIComponent(serverName)}&config=${encodeURIComponent(base64Config)}`;
        
        // Open deep link
        window.location.href = deepLink;
        
        // Show success message
        setOneClickStatus({ ...oneClickStatus, [agentName]: 'success' });
        
        // Show instructions
        const instructions = getAgentInstructions(agentName);
        alert(instructions);
        
        // Reset status after 3 seconds
        setTimeout(() => {
          setOneClickStatus({ ...oneClickStatus, [agentName]: null });
        }, 3000);
        
      } else if (agentName === 'vscode' || agentName === 'vscode-insiders') {
        // VS Code / VS Code Insiders deep link
        const protocol = agentName === 'vscode' ? 'vscode' : 'vscode-insiders';
        
        // Create the config object with name included
        const vscodeConfig = {
          name: serverName,
          type: "http",
          description: `${serverName} - MCP Server`,
          url: serverConfig.url,
          headers: serverConfig.headers
        };
        
        // Log the config to verify headers are included
        console.log('VS Code Config:', vscodeConfig);
        console.log('Headers:', serverConfig.headers);
        
        // Generate deep link with JSON-encoded config
        const deepLink = `${protocol}:mcp/install?${encodeURIComponent(JSON.stringify(vscodeConfig))}`;
        
        console.log('Deep Link:', deepLink);
        
        // Open deep link
        window.location.href = deepLink;
        
        // Show success message
        setOneClickStatus({ ...oneClickStatus, [agentName]: 'success' });
        
        // Show instructions
        const instructions = getAgentInstructions(agentName);
        alert(instructions);
        
        // Reset status after 3 seconds
        setTimeout(() => {
          setOneClickStatus({ ...oneClickStatus, [agentName]: null });
        }, 3000);
        
      } else if (agentName === 'claude-desktop') {
        // Claude Desktop - copy to clipboard for now
        await navigator.clipboard.writeText(JSON.stringify(config, null, 2));
        
        setOneClickStatus({ ...oneClickStatus, [agentName]: 'success' });
        setTimeout(() => {
          setOneClickStatus({ ...oneClickStatus, [agentName]: null });
        }, 3000);
        
        const instructions = getAgentInstructions(agentName);
        alert(`Configuration copied to clipboard!\n\n${instructions}`);
        
      } else {
        // For other agents, copy to clipboard
        await navigator.clipboard.writeText(JSON.stringify(config, null, 2));
        
        setOneClickStatus({ ...oneClickStatus, [agentName]: 'success' });
        setTimeout(() => {
          setOneClickStatus({ ...oneClickStatus, [agentName]: null });
        }, 3000);
        
        const instructions = getAgentInstructions(agentName);
        alert(`Configuration copied to clipboard!\n\n${instructions}`);
      }
      
    } catch (err) {
      console.error('Failed to install:', err);
      setOneClickStatus({ ...oneClickStatus, [agentName]: 'error' });
      setTimeout(() => {
        setOneClickStatus({ ...oneClickStatus, [agentName]: null });
      }, 3000);
    }
  };

  const getAgentInstructions = (agentName) => {
    const instructions = {
      'cursor': 'Opening Cursor to install MCP server...\n\nCursor should open automatically and prompt you to install the server configuration.\n\nIf Cursor doesn\'t open:\n1. Make sure Cursor is installed\n2. Try clicking the button again\n3. Or manually copy the config from the JSON tab',
      'vscode': 'Opening VS Code to install MCP server...\n\nVS Code should open automatically and prompt you to install the server configuration.\n\nIf VS Code doesn\'t open:\n1. Make sure VS Code is installed\n2. Try clicking the button again\n3. Or manually copy the config from the JSON tab',
      'vscode-insiders': 'Opening VS Code Insiders to install MCP server...\n\nVS Code Insiders should open automatically and prompt you to install the server configuration.\n\nIf VS Code Insiders doesn\'t open:\n1. Make sure VS Code Insiders is installed\n2. Try clicking the button again\n3. Or manually copy the config from the JSON tab',
      'claude-desktop': 'To complete setup in Claude Desktop:\n1. Open Claude Desktop settings\n2. Navigate to Developer Settings\n3. Click "Edit claude_desktop_config.json"\n4. Paste the configuration in the "mcpServers" section\n5. Restart Claude Desktop',
      'windsurf': 'To complete setup in Windsurf:\n1. Open Windsurf Settings\n2. Search for "MCP Configuration"\n3. Click "Edit Configuration"\n4. Paste the configuration\n5. Restart Windsurf',
      'cline': 'To complete setup in Cline:\n1. Open VS Code Settings (Cmd/Ctrl + ,)\n2. Search for "Cline MCP"\n3. Click "Edit MCP Settings"\n4. Paste the configuration\n5. Reload VS Code window'
    };
    return instructions[agentName] || 'Configuration copied! Please paste it into your agent\'s MCP configuration file.';
  };

  const agents = [
    {
      id: 'cursor',
      name: 'Cursor',
      iconType: 'component',
      icon: <Cursor.Combine size={56} />,
      description: 'One-click automatic install',
      color: 'from-purple-500 to-indigo-600'
    },
    {
      id: 'vscode',
      name: 'VS Code',
      iconType: 'svg',
      icon: (
        <svg width="56" height="56" viewBox="0 0 256 256" fill="none" xmlns="http://www.w3.org/2000/svg">
          <mask id="mask0" mask-type="alpha" maskUnits="userSpaceOnUse" x="0" y="0" width="256" height="256">
            <path fillRule="evenodd" clipRule="evenodd" d="M181.534 254.252C185.566 255.823 190.164 255.722 194.234 253.764L246.94 228.403C252.478 225.738 256 220.132 256 213.983V42.0181C256 35.8689 252.478 30.2638 246.94 27.5988L194.234 2.23681C188.893 -0.333132 182.642 0.296344 177.955 3.70418C177.285 4.191 176.647 4.73454 176.049 5.33354L74.2376 99.4751L31.0923 67.4806C26.1746 63.5354 19.0639 63.777 14.4016 68.0315L3.06159 78.6862C-1.0205 82.3897 -1.0205 88.6103 3.06159 92.3138L40.3053 128L3.06159 163.686C-1.0205 167.39 -1.0205 173.61 3.06159 177.314L14.4016 187.969C19.0639 192.223 26.1746 192.465 31.0923 188.519L74.2376 156.525L176.049 250.667C177.645 252.264 179.519 253.467 181.534 254.252ZM192.039 69.8853L115.479 128L192.039 186.115V69.8853Z" fill="white"/>
          </mask>
          <g mask="url(#mask0)">
            <path d="M246.94 27.6383L194.193 2.24138C188.088 -0.698302 180.791 0.541721 175.999 5.33332L3.06226 163.686C-1.02009 167.39 -1.02009 173.61 3.06226 177.314L14.4016 187.969C19.0639 192.223 26.1746 192.465 31.0923 188.519L239.003 34.2269C245.979 28.9347 255.999 33.9103 255.999 42.6667V42.0543C255.999 35.9051 252.478 30.3 246.94 27.6383Z" fill="#0065A9"/>
            <g filter="url(#filter0_d)">
              <path d="M246.94 228.362L194.193 253.759C188.088 256.698 180.791 255.458 175.999 250.667L3.06226 92.3136C-1.02009 88.6101 -1.02009 82.3895 3.06226 78.686L14.4016 68.0306C19.0639 63.7767 26.1746 63.5352 31.0923 67.4804L239.003 221.773C245.979 227.065 255.999 222.09 255.999 213.333V213.946C255.999 220.095 252.478 225.7 246.94 228.362Z" fill="#007ACC"/>
            </g>
            <g filter="url(#filter1_d)">
              <path d="M194.196 253.763C188.089 256.7 180.792 255.459 176 250.667C181.904 256.571 192 252.389 192 244.039V11.9606C192 3.61057 181.904 -0.571175 176 5.33321C180.792 0.541166 188.089 -0.700607 194.196 2.23648L246.934 27.5985C252.476 30.2635 256 35.8686 256 42.0178V213.983C256 220.132 252.476 225.737 246.934 228.402L194.196 253.763Z" fill="#1F9CF0"/>
            </g>
          </g>
          <defs>
            <filter id="filter0_d" x="-21.4896" y="40.5225" width="298.822" height="236.149" filterUnits="userSpaceOnUse" colorInterpolationFilters="sRGB">
              <feFlood floodOpacity="0" result="BackgroundImageFix"/>
              <feColorMatrix in="SourceAlpha" type="matrix" values="0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 127 0"/>
              <feOffset/>
              <feGaussianBlur stdDeviation="10.6667"/>
              <feColorMatrix type="matrix" values="0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0.25 0"/>
              <feBlend mode="overlay" in2="BackgroundImageFix" result="effect1_dropShadow"/>
              <feBlend mode="normal" in="SourceGraphic" in2="effect1_dropShadow" result="shape"/>
            </filter>
            <filter id="filter1_d" x="154.667" y="-20.5212" width="122.667" height="297.04" filterUnits="userSpaceOnUse" colorInterpolationFilters="sRGB">
              <feFlood floodOpacity="0" result="BackgroundImageFix"/>
              <feColorMatrix in="SourceAlpha" type="matrix" values="0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 127 0"/>
              <feOffset/>
              <feGaussianBlur stdDeviation="10.6667"/>
              <feColorMatrix type="matrix" values="0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0.25 0"/>
              <feBlend mode="overlay" in2="BackgroundImageFix" result="effect1_dropShadow"/>
              <feBlend mode="normal" in="SourceGraphic" in2="effect1_dropShadow" result="shape"/>
            </filter>
          </defs>
        </svg>
      ),
      description: 'One-click automatic install',
      color: 'from-blue-600 to-blue-800'
    },
    {
      id: 'vscode-insiders',
      name: 'VS Code Insiders',
      iconType: 'svg',
      icon: (
        <svg width="56" height="56" viewBox="0 0 256 256" fill="none" xmlns="http://www.w3.org/2000/svg">
          <mask id="mask0_insiders" mask-type="alpha" maskUnits="userSpaceOnUse" x="0" y="0" width="256" height="256">
            <path fillRule="evenodd" clipRule="evenodd" d="M181.534 254.252C185.566 255.823 190.164 255.722 194.234 253.764L246.94 228.403C252.478 225.738 256 220.132 256 213.983V42.0181C256 35.8689 252.478 30.2638 246.94 27.5988L194.234 2.23681C188.893 -0.333132 182.642 0.296344 177.955 3.70418C177.285 4.191 176.647 4.73454 176.049 5.33354L74.2376 99.4751L31.0923 67.4806C26.1746 63.5354 19.0639 63.777 14.4016 68.0315L3.06159 78.6862C-1.0205 82.3897 -1.0205 88.6103 3.06159 92.3138L40.3053 128L3.06159 163.686C-1.0205 167.39 -1.0205 173.61 3.06159 177.314L14.4016 187.969C19.0639 192.223 26.1746 192.465 31.0923 188.519L74.2376 156.525L176.049 250.667C177.645 252.264 179.519 253.467 181.534 254.252ZM192.039 69.8853L115.479 128L192.039 186.115V69.8853Z" fill="white"/>
          </mask>
          <g mask="url(#mask0_insiders)">
            <path d="M246.94 27.6383L194.193 2.24138C188.088 -0.698302 180.791 0.541721 175.999 5.33332L3.06226 163.686C-1.02009 167.39 -1.02009 173.61 3.06226 177.314L14.4016 187.969C19.0639 192.223 26.1746 192.465 31.0923 188.519L239.003 34.2269C245.979 28.9347 255.999 33.9103 255.999 42.6667V42.0543C255.999 35.9051 252.478 30.3 246.94 27.6383Z" fill="#1B7F47"/>
            <g filter="url(#filter0_d_insiders)">
              <path d="M246.94 228.362L194.193 253.759C188.088 256.698 180.791 255.458 175.999 250.667L3.06226 92.3136C-1.02009 88.6101 -1.02009 82.3895 3.06226 78.686L14.4016 68.0306C19.0639 63.7767 26.1746 63.5352 31.0923 67.4804L239.003 221.773C245.979 227.065 255.999 222.09 255.999 213.333V213.946C255.999 220.095 252.478 225.7 246.94 228.362Z" fill="#1E9E6D"/>
            </g>
            <g filter="url(#filter1_d_insiders)">
              <path d="M194.196 253.763C188.089 256.7 180.792 255.459 176 250.667C181.904 256.571 192 252.389 192 244.039V11.9606C192 3.61057 181.904 -0.571175 176 5.33321C180.792 0.541166 188.089 -0.700607 194.196 2.23648L246.934 27.5985C252.476 30.2635 256 35.8686 256 42.0178V213.983C256 220.132 252.476 225.737 246.934 228.402L194.196 253.763Z" fill="#29D37A"/>
            </g>
          </g>
          <defs>
            <filter id="filter0_d_insiders" x="-21.4896" y="40.5225" width="298.822" height="236.149" filterUnits="userSpaceOnUse" colorInterpolationFilters="sRGB">
              <feFlood floodOpacity="0" result="BackgroundImageFix"/>
              <feColorMatrix in="SourceAlpha" type="matrix" values="0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 127 0"/>
              <feOffset/>
              <feGaussianBlur stdDeviation="10.6667"/>
              <feColorMatrix type="matrix" values="0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0.25 0"/>
              <feBlend mode="overlay" in2="BackgroundImageFix" result="effect1_dropShadow"/>
              <feBlend mode="normal" in="SourceGraphic" in2="effect1_dropShadow" result="shape"/>
            </filter>
            <filter id="filter1_d_insiders" x="154.667" y="-20.5212" width="122.667" height="297.04" filterUnits="userSpaceOnUse" colorInterpolationFilters="sRGB">
              <feFlood floodOpacity="0" result="BackgroundImageFix"/>
              <feColorMatrix in="SourceAlpha" type="matrix" values="0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 127 0"/>
              <feOffset/>
              <feGaussianBlur stdDeviation="10.6667"/>
              <feColorMatrix type="matrix" values="0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0.25 0"/>
              <feBlend mode="overlay" in2="BackgroundImageFix" result="effect1_dropShadow"/>
              <feBlend mode="normal" in="SourceGraphic" in2="effect1_dropShadow" result="shape"/>
            </filter>
          </defs>
        </svg>
      ),
      description: 'One-click automatic install',
      color: 'from-blue-500 to-cyan-600'
    },
    {
      id: 'claude-desktop',
      name: 'Claude Desktop',
      iconType: 'component',
      icon: <Claude.Combine size={56} />,
      description: 'Claude desktop app',
      color: 'from-orange-500 to-red-600'
    },
    {
      id: 'windsurf',
      name: 'Windsurf',
      iconType: 'component',
      icon: <Windsurf.Combine size={56} />,
      description: 'AI coding assistant',
      color: 'from-teal-500 to-green-600'
    },
    {
      id: 'cline',
      name: 'Cline',
      iconType: 'component',
      icon: <Cline.Combine size={56} />,
      description: 'VS Code extension',
      color: 'from-pink-500 to-rose-600'
    }
  ];

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
        <div className="overflow-y-auto max-h-[calc(90vh-140px)]">
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
              {/* Tabs */}
              <div className="border-b border-gray-200">
                <div className="flex">
                  <button
                    onClick={() => setActiveTab('auto')}
                    className={`px-6 py-3 text-sm font-medium transition-colors relative ${
                      activeTab === 'auto'
                        ? 'text-purple-600 border-b-2 border-purple-600'
                        : 'text-gray-600 hover:text-gray-900'
                    }`}
                  >
                    <div className="flex items-center space-x-2">
                      <span>⚡</span>
                      <span>Auto</span>
                    </div>
                  </button>
                  <button
                    onClick={() => setActiveTab('manual')}
                    className={`px-6 py-3 text-sm font-medium transition-colors relative ${
                      activeTab === 'manual'
                        ? 'text-purple-600 border-b-2 border-purple-600'
                        : 'text-gray-600 hover:text-gray-900'
                    }`}
                  >
                    <div className="flex items-center space-x-2">
                      <span>📋</span>
                      <span>JSON</span>
                    </div>
                  </button>
                </div>
              </div>

              {/* Tab Content */}
              <div className="p-6">
                {activeTab === 'auto' ? (
                  <div>
                    <div className="mb-6">
                      <h3 className="text-lg font-semibold text-gray-900 mb-2">
                        Connect this server to your AI coding assistant with one click
                      </h3>
                      <p className="text-sm text-gray-600">
                        Choose your preferred agent below. We'll copy the configuration and guide you through the setup.
                      </p>
                    </div>

                    {/* Agents Grid */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {agents.map((agent) => (
                        <button
                          key={agent.id}
                          onClick={() => handleOneClickInstall(agent.id)}
                          disabled={oneClickStatus[agent.id] === 'loading'}
                          className={`relative overflow-hidden rounded-xl border-2 p-6 text-left transition-all hover:shadow-lg hover:scale-[1.02] ${
                            oneClickStatus[agent.id] === 'success'
                              ? 'border-green-500 bg-green-50'
                              : oneClickStatus[agent.id] === 'error'
                              ? 'border-red-500 bg-red-50'
                              : 'border-gray-200 bg-white hover:border-purple-300'
                          }`}
                        >
                          {/* Background Gradient */}
                          <div className={`absolute top-0 right-0 w-32 h-32 bg-gradient-to-br ${agent.color} opacity-10 rounded-full transform translate-x-16 -translate-y-16`}></div>
                          
                          <div className="relative">
                            <div className="flex items-start justify-between mb-3">
                              <div className="flex items-center space-x-2">
                                {agent.iconType === 'component' || agent.iconType === 'svg' ? (
                                  <div>{agent.icon}</div>
                                ) : agent.iconType === 'emoji' ? (
                                  <div className="text-4xl">{agent.icon}</div>
                                ) : (
                                  <div>{agent.icon}</div>
                                )}
                                {(agent.id === 'cursor' || agent.id === 'vscode' || agent.id === 'vscode-insiders') && (
                                  <span className="px-2 py-1 text-xs font-semibold bg-green-100 text-green-700 rounded-full border border-green-300">
                                    AUTO
                                  </span>
                                )}
                              </div>
                              {oneClickStatus[agent.id] === 'loading' && (
                                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-purple-600"></div>
                              )}
                              {oneClickStatus[agent.id] === 'success' && (
                                <div className="text-green-600">
                                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                  </svg>
                                </div>
                              )}
                            </div>
                            
                            <h4 className="text-lg font-semibold text-gray-900 mb-1">
                              {agent.name}
                            </h4>
                            <p className="text-sm text-gray-600 mb-4">
                              {agent.description}
                            </p>
                            
                            <div className="flex items-center text-purple-600 font-medium text-sm">
                              {oneClickStatus[agent.id] === 'success' ? (
                                <>
                                  <span>✓ Configuration Copied!</span>
                                </>
                              ) : (
                                <>
                                  <span>One-Click Install</span>
                                  <svg className="w-4 h-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                                  </svg>
                                </>
                              )}
                            </div>
                          </div>
                        </button>
                      ))}
                    </div>

                    {/* Info Box */}
                    <div className="mt-6 p-4 bg-purple-50 rounded-lg border border-purple-200">
                      <div className="flex items-start">
                        <svg className="w-5 h-5 text-purple-600 mt-0.5 mr-2 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        <div className="text-sm text-purple-800">
                          <p className="font-medium mb-1">How it works:</p>
                          <ul className="list-disc list-inside space-y-1 text-purple-700">
                            <li>Click on your preferred agent</li>
                            <li>Configuration will be copied to your clipboard automatically</li>
                            <li>Follow the on-screen instructions to complete the setup</li>
                            <li>Restart your agent to connect to this MCP server</li>
                          </ul>
                        </div>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div>
                    <div className="mb-4">
                      <p className="text-sm text-gray-600 mb-2">
                        Copy this configuration to use in your MCP client:
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
                          <p className="font-medium mb-1">Manual setup:</p>
                          <ul className="list-disc list-inside space-y-1 text-blue-700">
                            <li>Copy the configuration above</li>
                            <li>Add it to your MCP client's configuration file</li>
                            <li>Restart your MCP client to connect to this server</li>
                          </ul>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
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
