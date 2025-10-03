import React, { useState, useEffect } from 'react';
import Form from '@rjsf/core';
import validator from '@rjsf/validator-ajv8';

function App() {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [currentRoute, setCurrentRoute] = useState('dashboard');
  const [connectors, setConnectors] = useState([]);
  const [loadingConnectors, setLoadingConnectors] = useState(false);
  const [connectorsError, setConnectorsError] = useState(null);
  
  // Servers state
  const [servers, setServers] = useState([]);
  const [loadingServers, setLoadingServers] = useState(false);
  const [serversError, setServersError] = useState(null);
  
  // Configuration modal state
  const [showConfigModal, setShowConfigModal] = useState(false);
  const [selectedConnector, setSelectedConnector] = useState(null);
  const [connectorSchema, setConnectorSchema] = useState(null);
  const [loadingSchema, setLoadingSchema] = useState(false);
  const [formData, setFormData] = useState({});
  const [serverName, setServerName] = useState('');
  const [tokenExpiresAt, setTokenExpiresAt] = useState('');

  // Server tools state
  const [selectedServer, setSelectedServer] = useState(null);
  const [serverTools, setServerTools] = useState([]);
  const [selectedTool, setSelectedTool] = useState(null);
  const [loadingTools, setLoadingTools] = useState(false);
  const [toolsError, setToolsError] = useState(null);
  const [toolInputs, setToolInputs] = useState({});
  const [showJsonView, setShowJsonView] = useState(false);

  // Fetch connectors when the connectors route is selected
  useEffect(() => {
    if (currentRoute === 'connectors') {
      setLoadingConnectors(true);
      setConnectorsError(null);
      fetch('http://localhost:9000/api/connectors')
        .then(response => {
          if (!response.ok) {
            throw new Error('Failed to fetch connectors');
          }
          return response.json();
        })
        .then(data => {
          // Transform the data into a flat array
          const connectorsList = data.flatMap(connectorObj => 
            Object.entries(connectorObj).map(([key, value]) => ({
              id: key,
              name: value.name,
              description: value.description,
              version: value.version,
              author: value.author,
              status: 'Active'
            }))
          );
          setConnectors(connectorsList);
          setLoadingConnectors(false);
        })
        .catch(error => {
          console.error('Error fetching connectors:', error);
          setConnectorsError(error.message);
          setLoadingConnectors(false);
        });
    }
  }, [currentRoute]);

  // Fetch servers when the servers route is selected
  useEffect(() => {
    if (currentRoute === 'servers') {
      setLoadingServers(true);
      setServersError(null);
      fetch('http://localhost:9000/api/servers')
        .then(response => {
          if (!response.ok) {
            throw new Error('Failed to fetch servers');
          }
          return response.json();
        })
        .then(data => {
          setServers(data);
          setLoadingServers(false);
        })
        .catch(error => {
          console.error('Error fetching servers:', error);
          setServersError(error.message);
          setLoadingServers(false);
        });
    }
  }, [currentRoute]);

  // Fetch server tools when the server-tools route is selected
  useEffect(() => {
    if (currentRoute === 'server-tools' && selectedServer) {
      setLoadingTools(true);
      setToolsError(null);
      fetch(`http://localhost:9000/api/servers/${selectedServer.id}/tools`)
        .then(response => {
          if (!response.ok) {
            throw new Error('Failed to fetch tools');
          }
          return response.json();
        })
        .then(data => {
          setServerTools(data.tools || []);
          // Auto-select first tool
          if (data.tools && data.tools.length > 0) {
            setSelectedTool(data.tools[0]);
          }
          setLoadingTools(false);
        })
        .catch(error => {
          console.error('Error fetching tools:', error);
          setToolsError(error.message);
          setLoadingTools(false);
        });
    }
  }, [currentRoute, selectedServer]);

  // Reset tool inputs and initialize with defaults when tool changes
  useEffect(() => {
    if (selectedTool && selectedTool.inputSchema && selectedTool.inputSchema.properties) {
      const initialInputs = {};
      Object.entries(selectedTool.inputSchema.properties).forEach(([paramName, paramSchema]) => {
        if (paramSchema.default !== undefined) {
          initialInputs[paramName] = paramSchema.default;
        }
      });
      setToolInputs(initialInputs);
    } else {
      setToolInputs({});
    }
  }, [selectedTool]);

  // Handle opening configuration modal
  const handleConfigureConnector = (connector) => {
    setSelectedConnector(connector);
    setShowConfigModal(true);
    setLoadingSchema(true);
    setFormData({});
    setServerName('');
    setTokenExpiresAt('');
    
    // Fetch connector schema
    fetch(`http://localhost:9000/api/connector-schema/${connector.id}`)
      .then(response => {
        if (!response.ok) {
          throw new Error('Failed to fetch connector schema');
        }
        return response.json();
      })
      .then(schema => {
        setConnectorSchema(schema);
        setLoadingSchema(false);
      })
      .catch(error => {
        console.error('Error fetching schema:', error);
        setLoadingSchema(false);
        alert('Failed to load connector schema: ' + error.message);
      });
  };

  // Handle form submission
  const handleFormSubmit = ({ formData }) => {
    // Validate server name
    if (!serverName.trim()) {
      alert('⚠️ Please enter a server name');
      return;
    }
    
    console.log('Form submitted with data:', formData);
    console.log('Server name:', serverName);
    
    // Create server payload
    const serverData = {
      connector_name: selectedConnector.id,
      server_name: serverName.trim(),
      configuration: formData,
      token_expires_at: tokenExpiresAt || null
    };
    
    // Create server via backend API
    fetch(`http://localhost:9000/api/servers`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(serverData)
    })
      .then(response => {
        if (!response.ok) {
          throw new Error('Failed to create server');
        }
        return response.json();
      })
      .then(data => {
        console.log('Server created:', data);
        const message = [
          `✅ ${data.message}`,
          ``,
          `Server ID: ${data.server_id}`,
          `Connector: ${data.connector_name}`,
          `Server Name: ${data.server_name}`,
          `Token: ${data.token}`,
          ``,
          `⚠️ Please save this token securely. It won't be shown again!`
        ].join('\n');
        alert(message);
        
        // Close the modal
        setShowConfigModal(false);
        setSelectedConnector(null);
        setConnectorSchema(null);
        setServerName('');
        setTokenExpiresAt('');
      })
      .catch(error => {
        console.error('Error creating server:', error);
        alert(`❌ Failed to create server: ${error.message}\n\nPlease check that the database is running and configured correctly.`);
      });
  };

  // Handle closing modal
  const handleCloseModal = () => {
    setShowConfigModal(false);
    setSelectedConnector(null);
    setConnectorSchema(null);
    setFormData({});
    setServerName('');
    setTokenExpiresAt('');
  };

  // Handle server deletion
  const handleDeleteServer = (server) => {
    const confirmMessage = `⚠️ Are you sure you want to delete server "${server.server_name}"?\n\nThis will permanently delete:\n• The server configuration\n• All associated tokens\n• All associated tools\n\nThis action cannot be undone.`;
    
    if (window.confirm(confirmMessage)) {
      // Delete the server
      fetch(`http://localhost:9000/api/servers/${server.id}`, {
        method: 'DELETE',
      })
        .then(response => {
          if (!response.ok) {
            throw new Error('Failed to delete server');
          }
          return response.json();
        })
        .then(data => {
          console.log('Server deleted:', data);
          const message = [
            `✅ ${data.message}`,
            ``,
            `Deleted tokens: ${data.deleted_tokens}`,
            `Deleted tools: ${data.deleted_tools}`
          ].join('\n');
          alert(message);
          
          // Refresh the servers list
          setLoadingServers(true);
          setServersError(null);
          fetch('http://localhost:9000/api/servers')
            .then(response => {
              if (!response.ok) {
                throw new Error('Failed to fetch servers');
              }
              return response.json();
            })
            .then(data => {
              setServers(data);
              setLoadingServers(false);
            })
            .catch(error => {
              console.error('Error fetching servers:', error);
              setServersError(error.message);
              setLoadingServers(false);
            });
        })
        .catch(error => {
          console.error('Error deleting server:', error);
          alert(`❌ Failed to delete server: ${error.message}`);
        });
    }
  };

  // SVG Icons
  const MenuIcon = () => (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
    </svg>
  );

  const HomeIcon = () => (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
    </svg>
  );

  const DashboardIcon = () => (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 5a1 1 0 011-1h4a1 1 0 011 1v7a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM14 5a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1V5zM4 16a1 1 0 011-1h4a1 1 0 011 1v3a1 1 0 01-1 1H5a1 1 0 01-1-1v-3zM14 13a1 1 0 011-1h4a1 1 0 011 1v7a1 1 0 01-1 1h-4a1 1 0 01-1-1v-7z" />
    </svg>
  );

  const TableIcon = () => (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M3 14h18m-9-4v8m-7 0h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
    </svg>
  );

  const ChartIcon = () => (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" />
    </svg>
  );

  const ToolsIcon = () => (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
    </svg>
  );

  const ChatIcon = () => (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
    </svg>
  );

  const DatabaseIcon = () => (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" />
    </svg>
  );

  const DocumentIcon = () => (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
    </svg>
  );

  const CompanyIcon = () => (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
    </svg>
  );

  const ChevronRightIcon = () => (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
    </svg>
  );

  const InfoIcon = () => (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  );

  const CloseIcon = () => (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
    </svg>
  );

  const ConnectorIcon = () => (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
    </svg>
  );

  const navigationItems = [
    { id: 'getting-started', name: 'Getting Started', icon: <HomeIcon />, route: 'getting-started' },
    { id: 'dashboard', name: 'Dashboard', icon: <DashboardIcon />, route: 'dashboard', highlighted: true },
    { id: 'connectors', name: 'Connectors', icon: <ConnectorIcon />, route: 'connectors' },
    { id: 'servers', name: 'Servers', icon: <DatabaseIcon />, route: 'servers' },
    { id: 'cap-table', name: 'Cap table', icon: <TableIcon />, route: 'cap-table', hasSubmenu: true },
    { id: 'equity-plans', name: 'Equity plans', icon: <ChartIcon />, route: 'equity-plans', hasSubmenu: true },
    { id: 'tools', name: 'Tools', icon: <ToolsIcon />, route: 'tools', hasSubmenu: true },
    { id: 'communication', name: 'Communication', icon: <ChatIcon />, route: 'communication' },
    { id: 'data-room', name: 'Data room', icon: <DatabaseIcon />, route: 'data-room' },
    { id: 'secondaries', name: 'Secondaries', icon: <ChartIcon />, route: 'secondaries' },
    { id: 'documents', name: 'Documents', icon: <DocumentIcon />, route: 'documents', hasSubmenu: true },
    { id: 'company', name: 'Company', icon: <CompanyIcon />, route: 'company', hasSubmenu: true },
  ];

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <div className={`${sidebarCollapsed ? 'w-16' : 'w-64'} bg-white border-r border-gray-200 transition-all duration-300 flex flex-col`}>
        {/* Logo and Toggle */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          {!sidebarCollapsed && (
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-black rounded-lg flex items-center justify-center text-white font-bold text-sm">
                C
              </div>
              <span className="font-semibold text-lg">Cake.</span>
            </div>
          )}
          <button
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            className="p-1 rounded-lg hover:bg-gray-100 text-gray-600"
          >
            <MenuIcon />
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-3 overflow-y-auto">
          <div className="space-y-1">
            {navigationItems.map((item) => (
              <button
                key={item.id}
                onClick={() => setCurrentRoute(item.route)}
                className={`w-full flex items-center ${sidebarCollapsed ? 'justify-center' : 'justify-between'} px-3 py-2 rounded-lg text-sm transition-colors ${
                  currentRoute === item.route
                    ? 'bg-purple-50 text-purple-600'
                    : 'text-gray-700 hover:bg-gray-50'
                }`}
                title={sidebarCollapsed ? item.name : ''}
              >
                <div className="flex items-center space-x-3">
                  <span className={currentRoute === item.route ? 'text-purple-600' : 'text-gray-500'}>
                    {item.icon}
                  </span>
                  {!sidebarCollapsed && <span>{item.name}</span>}
                </div>
                {!sidebarCollapsed && item.hasSubmenu && (
                  <ChevronRightIcon />
                )}
              </button>
            ))}
          </div>
        </nav>

        {/* What's New Section */}
        {!sidebarCollapsed && (
          <div className="p-4 border-t border-gray-200">
            <div className="bg-gradient-to-br from-purple-50 to-blue-50 rounded-lg p-3 border border-purple-200">
              <div className="text-purple-700 text-sm font-semibold mb-2">✨ What's New</div>
              <div className="space-y-2 text-xs text-gray-600">
                <div className="flex items-center space-x-2">
                  <InfoIcon />
                  <span>2FA security</span>
                </div>
                <div className="flex items-center space-x-2">
                  <InfoIcon />
                  <span>Bare trusts & SPVs</span>
                </div>
                <div className="flex items-center space-x-2">
                  <InfoIcon />
                  <span>Reporting</span>
                </div>
              </div>
              <div className="mt-2 text-xs text-gray-400">version: 0d5ba1f5</div>
            </div>
          </div>
        )}
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <header className="bg-white border-b border-gray-200 px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <div className="w-8 h-8 bg-gray-900 rounded-full flex items-center justify-center text-white text-sm">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <span className="font-semibold">JMobbin</span>
                <span className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded-full">Free</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="flex items-center space-x-2 text-sm">
                  <div className="w-6 h-6 bg-gray-100 rounded-full flex items-center justify-center">
                    <svg className="w-4 h-4 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 21v-4m0 0V5a2 2 0 012-2h6.5l1 1H21l-3 6 3 6h-8.5l-1-1H5a2 2 0 00-2 2zm9-13.5V9" />
                    </svg>
                  </div>
                  <span className="text-gray-700">Issue overseas equity right</span>
                </div>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2 px-3 py-2 bg-blue-50 text-blue-700 text-sm rounded-lg">
                <span className="font-semibold">33.</span>
                <span>Getting started 🚀</span>
              </div>
              <button className="w-8 h-8 bg-red-500 rounded-full flex items-center justify-center text-white relative">
                <span className="absolute -top-1 -right-1 w-3 h-3 bg-red-600 rounded-full"></span>
                🔔
              </button>
              <button className="p-2 hover:bg-gray-100 rounded-lg text-gray-600">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" />
                </svg>
              </button>
              <button className="px-4 py-2 bg-purple-600 text-white text-sm font-medium rounded-lg hover:bg-purple-700">
                Invite co-pilots
              </button>
              <button className="px-4 py-2 bg-purple-600 text-white text-sm font-medium rounded-lg hover:bg-purple-700">
                Upgrade
              </button>
              <div className="flex items-center space-x-2">
                <span className="text-sm text-gray-700">Company</span>
                <span className="text-sm text-gray-700">Portal</span>
              </div>
              <div className="w-8 h-8 bg-purple-600 rounded-full flex items-center justify-center text-white font-semibold">
                JS
              </div>
            </div>
          </div>
        </header>

        {/* Banner */}
        <div className="bg-purple-100 border-b border-purple-200 px-6 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-purple-200 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                </svg>
              </div>
              <span className="text-purple-900 font-medium">Have your say on the new Cake Dashboard</span>
            </div>
            <div className="flex items-center space-x-3">
              <button className="px-4 py-2 bg-purple-200 text-purple-900 text-sm font-medium rounded-lg hover:bg-purple-300">
                Check it out
              </button>
              <button className="text-purple-700 hover:text-purple-900">
                <CloseIcon />
              </button>
            </div>
          </div>
        </div>

        {/* Main Content Area */}
        <main className="flex-1 overflow-y-auto p-6">
          {currentRoute === 'server-tools' ? (
            // Server Tools Page
            <div>
              <div className="mb-6">
                <div className="flex items-center space-x-3 mb-2">
                  <button
                    onClick={() => {
                      setCurrentRoute('servers');
                      setSelectedServer(null);
                      setServerTools([]);
                      setSelectedTool(null);
                    }}
                    className="text-purple-600 hover:text-purple-700 flex items-center space-x-1"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                    </svg>
                    <span className="text-sm font-medium">Back to Servers</span>
                  </button>
                </div>
                <h1 className="text-3xl font-bold text-gray-900 mb-2">
                  {selectedServer?.server_name || 'Server'} - Tools
                </h1>
                <p className="text-gray-600">
                  Available tools for {selectedServer?.connector_name || 'this server'}
                </p>
              </div>

              {loadingTools ? (
                <div className="flex items-center justify-center h-64">
                  <div className="text-center">
                    <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
                    <p className="mt-4 text-gray-600">Loading tools...</p>
                  </div>
                </div>
              ) : toolsError ? (
                <div className="bg-red-50 border border-red-200 rounded-lg p-6">
                  <div className="flex items-center space-x-3">
                    <svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <div>
                      <h3 className="text-red-900 font-semibold">Error loading tools</h3>
                      <p className="text-red-700 text-sm mt-1">{toolsError}</p>
                      <p className="text-red-600 text-sm mt-2">Make sure the MCP server is running</p>
                    </div>
                  </div>
                  <button
                    onClick={() => {
                      setCurrentRoute('server-tools');
                    }}
                    className="mt-4 px-4 py-2 bg-red-600 text-white text-sm font-medium rounded-lg hover:bg-red-700"
                  >
                    Retry
                  </button>
                </div>
              ) : serverTools.length > 0 ? (
                <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
                  {/* Left Column - Tools List */}
                  <div className="lg:col-span-2">
                    <div className="bg-white rounded-lg border border-gray-200 p-6">
                      <h2 className="text-lg font-semibold text-gray-900 mb-4">Available Tools</h2>
                      <div className="space-y-2 max-h-[600px] overflow-y-auto pr-2">
                        {serverTools.map((tool, index) => (
                          <label
                            key={index}
                            className={`flex items-start space-x-3 p-4 rounded-lg border-2 cursor-pointer transition-colors ${
                              selectedTool?.name === tool.name
                                ? 'border-purple-500 bg-purple-50'
                                : 'border-gray-200 hover:border-purple-200 hover:bg-gray-50'
                            }`}
                          >
                            <input
                              type="radio"
                              name="tool-selection"
                              checked={selectedTool?.name === tool.name}
                              onChange={() => setSelectedTool(tool)}
                              className="mt-1 w-4 h-4 text-purple-600 focus:ring-purple-500"
                            />
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center space-x-2 mb-1">
                                <span className={`text-sm font-semibold ${
                                  selectedTool?.name === tool.name ? 'text-purple-900' : 'text-gray-900'
                                }`}>
                                  {tool.name}
                                </span>
                              </div>
                              {tool.description && (
                                <p className={`text-xs ${
                                  selectedTool?.name === tool.name ? 'text-purple-700' : 'text-gray-600'
                                } line-clamp-2`}>
                                  {tool.description}
                                </p>
                              )}
                            </div>
                          </label>
                        ))}
                      </div>
                    </div>
                  </div>

                  {/* Right Column - Tool Details */}
                  <div className="lg:col-span-3">
                    <div className="bg-white rounded-lg border border-gray-200 p-6">
                      <div className="flex items-center justify-between mb-4">
                        <h2 className="text-lg font-semibold text-gray-900">
                          {showJsonView ? 'Tool Configuration (JSON)' : 'Tool Parameters'}
                        </h2>
                        <div className="flex items-center space-x-2">
                          <button
                            onClick={() => setShowJsonView(!showJsonView)}
                            className="text-sm text-gray-600 hover:text-gray-700 font-medium flex items-center space-x-1 px-3 py-1 border border-gray-300 rounded-lg hover:bg-gray-50"
                          >
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                            </svg>
                            <span>{showJsonView ? 'Show Form' : 'Show JSON'}</span>
                          </button>
                          {showJsonView && (
                            <button
                              onClick={() => {
                                navigator.clipboard.writeText(JSON.stringify(selectedTool, null, 2));
                              }}
                              className="text-sm text-purple-600 hover:text-purple-700 font-medium flex items-center space-x-1"
                            >
                              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                              </svg>
                              <span>Copy JSON</span>
                            </button>
                          )}
                        </div>
                      </div>
                      
                      {selectedTool ? (
                        showJsonView ? (
                          <div className="bg-gray-900 rounded-lg p-4 overflow-x-auto">
                            <pre className="text-xs text-gray-100 font-mono">
                              {JSON.stringify(selectedTool, null, 2)}
                            </pre>
                          </div>
                        ) : (
                          <div className="space-y-4">
                            {/* Tool Description */}
                            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                              <h3 className="text-sm font-semibold text-blue-900 mb-2">
                                {selectedTool.name}
                              </h3>
                              <p className="text-sm text-blue-700">
                                {selectedTool.description || 'No description available'}
                              </p>
                            </div>

                            {/* Input Parameters */}
                            {selectedTool.inputSchema && selectedTool.inputSchema.properties ? (
                              <div className="space-y-4">
                                <h4 className="text-sm font-semibold text-gray-900">Parameters</h4>
                                {Object.entries(selectedTool.inputSchema.properties).map(([paramName, paramSchema]) => (
                                  <div key={paramName} className="space-y-2">
                                    <label htmlFor={paramName} className="block text-sm font-medium text-gray-700">
                                      {paramName}
                                      {selectedTool.inputSchema.required && selectedTool.inputSchema.required.includes(paramName) && (
                                        <span className="text-red-500 ml-1">*</span>
                                      )}
                                    </label>
                                    
                                    {/* Handle different input types */}
                                    {paramSchema.type === 'boolean' ? (
                                      <select
                                        id={paramName}
                                        value={toolInputs[paramName] || 'false'}
                                        onChange={(e) => setToolInputs({...toolInputs, [paramName]: e.target.value})}
                                        className="w-full px-4 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                                      >
                                        <option value="true">true</option>
                                        <option value="false">false</option>
                                      </select>
                                    ) : paramSchema.type === 'number' || paramSchema.type === 'integer' ? (
                                      <input
                                        type="number"
                                        id={paramName}
                                        value={toolInputs[paramName] || paramSchema.default || ''}
                                        onChange={(e) => setToolInputs({...toolInputs, [paramName]: e.target.value})}
                                        placeholder={paramSchema.default !== undefined ? `Default: ${paramSchema.default}` : `Enter ${paramName}`}
                                        className="w-full px-4 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                                      />
                                    ) : paramSchema.enum ? (
                                      <select
                                        id={paramName}
                                        value={toolInputs[paramName] || paramSchema.default || ''}
                                        onChange={(e) => setToolInputs({...toolInputs, [paramName]: e.target.value})}
                                        className="w-full px-4 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                                      >
                                        <option value="">Select {paramName}</option>
                                        {paramSchema.enum.map(option => (
                                          <option key={option} value={option}>{option}</option>
                                        ))}
                                      </select>
                                    ) : (
                                      <input
                                        type="text"
                                        id={paramName}
                                        value={toolInputs[paramName] || paramSchema.default || ''}
                                        onChange={(e) => setToolInputs({...toolInputs, [paramName]: e.target.value})}
                                        placeholder={paramSchema.default !== undefined ? `Default: ${paramSchema.default}` : `Enter ${paramName}`}
                                        className="w-full px-4 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                                      />
                                    )}
                                    
                                    {/* Parameter description and metadata */}
                                    <div className="space-y-1">
                                      {paramSchema.description && (
                                        <p className="text-xs text-gray-600">{paramSchema.description}</p>
                                      )}
                                      <div className="flex flex-wrap gap-2">
                                        <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
                                          Type: {paramSchema.type || 'string'}
                                        </span>
                                        {paramSchema.default !== undefined && (
                                          <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
                                            Default: {JSON.stringify(paramSchema.default)}
                                          </span>
                                        )}
                                      </div>
                                    </div>
                                  </div>
                                ))}

                                {/* Execute Button */}
                                <div className="pt-4 border-t border-gray-200">
                                  <button
                                    onClick={() => {
                                      console.log('Tool Inputs:', toolInputs);
                                      alert('Tool execution not yet implemented\n\nInputs: ' + JSON.stringify(toolInputs, null, 2));
                                    }}
                                    className="w-full px-4 py-2 bg-purple-600 text-white text-sm font-medium rounded-lg hover:bg-purple-700"
                                  >
                                    Execute Tool
                                  </button>
                                </div>
                              </div>
                            ) : (
                              <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 text-center">
                                <p className="text-sm text-gray-600">This tool has no input parameters</p>
                              </div>
                            )}
                          </div>
                        )
                      ) : (
                        <div className="text-center py-12 text-gray-500">
                          <p>Select a tool to view its configuration</p>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="bg-white rounded-lg border-2 border-dashed border-gray-300 p-12 text-center">
                  <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    </svg>
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">No tools available</h3>
                  <p className="text-gray-600">This server has no tools configured</p>
                </div>
              )}
            </div>
          ) : currentRoute === 'servers' ? (
            // Servers Page
            <div>
              <div className="mb-6">
                <h1 className="text-3xl font-bold text-gray-900 mb-2">MCP Servers</h1>
                <p className="text-gray-600">Manage your configured MCP server instances</p>
              </div>

              {loadingServers ? (
                <div className="flex items-center justify-center h-64">
                  <div className="text-center">
                    <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
                    <p className="mt-4 text-gray-600">Loading servers...</p>
                  </div>
                </div>
              ) : serversError ? (
                <div className="bg-red-50 border border-red-200 rounded-lg p-6">
                  <div className="flex items-center space-x-3">
                    <svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <div>
                      <h3 className="text-red-900 font-semibold">Error loading servers</h3>
                      <p className="text-red-700 text-sm mt-1">{serversError}</p>
                      <p className="text-red-600 text-sm mt-2">Make sure the API server is running on port 9000</p>
                    </div>
                  </div>
                </div>
              ) : (
                <div>
                  {/* Action Bar */}
                  <div className="mb-6 flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                      <button 
                        onClick={() => setCurrentRoute('connectors')}
                        className="px-4 py-2 bg-purple-600 text-white text-sm font-medium rounded-lg hover:bg-purple-700 flex items-center space-x-2"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                        </svg>
                        <span>Create New Server</span>
                      </button>
                      <button 
                        onClick={() => setCurrentRoute('servers')}
                        className="px-4 py-2 border border-gray-300 text-gray-700 text-sm font-medium rounded-lg hover:bg-gray-50 flex items-center space-x-2"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                        </svg>
                        <span>Refresh</span>
                      </button>
                    </div>
                    <div className="text-sm text-gray-600">
                      Total Servers: <span className="font-semibold text-gray-900">{servers.length}</span>
                    </div>
                  </div>

                  {/* Servers List */}
                  {servers.length > 0 ? (
                    <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
                      <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                          <tr>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                              Server Name
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                              Connector
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                              Created
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                              Updated
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                              Status
                            </th>
                            <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                              Actions
                            </th>
                          </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                          {servers.map((server) => (
                            <tr key={server.id} className="hover:bg-gray-50">
                              <td className="px-6 py-4 whitespace-nowrap">
                                <div className="flex items-center">
                                  <div className="flex-shrink-0 h-10 w-10 bg-gradient-to-br from-purple-500 to-blue-500 rounded-lg flex items-center justify-center">
                                    <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01" />
                                    </svg>
                                  </div>
                                  <div className="ml-4">
                                    <div className="text-sm font-medium text-gray-900">{server.server_name}</div>
                                    <div className="text-sm text-gray-500">ID: {server.id}</div>
                                  </div>
                                </div>
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap">
                                <div className="text-sm text-gray-900">{server.connector_name}</div>
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap">
                                <div className="text-sm text-gray-900">
                                  {new Date(server.created_at).toLocaleDateString()}
                                </div>
                                <div className="text-xs text-gray-500">
                                  {new Date(server.created_at).toLocaleTimeString()}
                                </div>
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap">
                                <div className="text-sm text-gray-900">
                                  {new Date(server.updated_at).toLocaleDateString()}
                                </div>
                                <div className="text-xs text-gray-500">
                                  {new Date(server.updated_at).toLocaleTimeString()}
                                </div>
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap">
                                <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                                  server.is_active 
                                    ? 'bg-green-100 text-green-800' 
                                    : 'bg-gray-100 text-gray-800'
                                }`}>
                                  {server.is_active ? 'Active' : 'Inactive'}
                                </span>
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                <button 
                                  onClick={() => {
                                    setSelectedServer(server);
                                    setCurrentRoute('server-tools');
                                  }}
                                  className="text-purple-600 hover:text-purple-900 mr-3"
                                >
                                  View
                                </button>
                                <button className="text-blue-600 hover:text-blue-900 mr-3">
                                  Edit
                                </button>
                                <button 
                                  onClick={() => handleDeleteServer(server)}
                                  className="text-red-600 hover:text-red-900"
                                >
                                  Delete
                                </button>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ) : (
                    <div className="bg-white rounded-lg border-2 border-dashed border-gray-300 p-12 text-center">
                      <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                        <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01" />
                        </svg>
                      </div>
                      <h3 className="text-lg font-semibold text-gray-900 mb-2">No servers configured</h3>
                      <p className="text-gray-600 mb-4">Get started by creating your first MCP server</p>
                      <button 
                        onClick={() => setCurrentRoute('connectors')}
                        className="px-6 py-3 bg-purple-600 text-white font-medium rounded-lg hover:bg-purple-700"
                      >
                        Create Your First Server
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>
          ) : currentRoute === 'connectors' ? (
            // Connectors Page
            <div>
              <div className="mb-6">
                <h1 className="text-3xl font-bold text-gray-900 mb-2">Connectors</h1>
                <p className="text-gray-600">Manage and configure your data connectors</p>
              </div>

              {loadingConnectors ? (
                <div className="flex items-center justify-center h-64">
                  <div className="text-center">
                    <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
                    <p className="mt-4 text-gray-600">Loading connectors...</p>
                  </div>
                </div>
              ) : connectorsError ? (
                <div className="bg-red-50 border border-red-200 rounded-lg p-6">
                  <div className="flex items-center space-x-3">
                    <svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <div>
                      <h3 className="text-red-900 font-semibold">Error loading connectors</h3>
                      <p className="text-red-700 text-sm mt-1">{connectorsError}</p>
                      <p className="text-red-600 text-sm mt-2">Make sure the API server is running on port 9000</p>
                    </div>
                  </div>
                </div>
              ) : (
                <div>
                  {/* Action Bar */}
                  <div className="mb-6 flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                      <button className="px-4 py-2 bg-purple-600 text-white text-sm font-medium rounded-lg hover:bg-purple-700 flex items-center space-x-2">
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                        </svg>
                        <span>Add Connector</span>
                      </button>
                      <button className="px-4 py-2 border border-gray-300 text-gray-700 text-sm font-medium rounded-lg hover:bg-gray-50 flex items-center space-x-2">
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                        </svg>
                        <span>Refresh</span>
                      </button>
                    </div>
                    <div className="flex items-center space-x-2">
                      <input
                        type="text"
                        placeholder="Search connectors..."
                        className="px-4 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                      />
                      <button className="p-2 border border-gray-300 rounded-lg hover:bg-gray-50">
                        <svg className="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
                        </svg>
                      </button>
                    </div>
                  </div>

                  {/* Connectors Grid */}
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {connectors.map((connector) => (
                      <div key={connector.id} className="bg-white rounded-lg border border-gray-200 p-6 hover:shadow-lg transition-shadow">
                        <div className="flex items-start justify-between mb-4">
                          <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-blue-500 rounded-lg flex items-center justify-center">
                            <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" />
                            </svg>
                          </div>
                          <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                            connector.status === 'Active' 
                              ? 'bg-green-100 text-green-700' 
                              : 'bg-gray-100 text-gray-700'
                          }`}>
                            {connector.status}
                          </span>
                        </div>
                        
                        <h3 className="text-lg font-semibold text-gray-900 mb-2">{connector.name}</h3>
                        <p className="text-sm text-gray-600 mb-4">{connector.description}</p>
                        
                        <div className="space-y-2 mb-4 text-xs text-gray-500">
                          <div className="flex items-center justify-between">
                            <span>Version:</span>
                            <span className="font-medium text-gray-700">{connector.version}</span>
                          </div>
                          <div className="flex items-center justify-between">
                            <span>Author:</span>
                            <span className="font-medium text-gray-700">{connector.author}</span>
                          </div>
                        </div>
                        
                        <div className="flex items-center space-x-2 pt-4 border-t border-gray-100">
                          <button 
                            onClick={() => handleConfigureConnector(connector)}
                            className="flex-1 px-3 py-2 bg-purple-600 text-white text-sm font-medium rounded-lg hover:bg-purple-700"
                          >
                            Create Server
                          </button>
                          <button className="px-3 py-2 border border-gray-300 text-gray-700 text-sm font-medium rounded-lg hover:bg-gray-50">
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z" />
                            </svg>
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* Empty State */}
                  {connectors.length === 0 && !loadingConnectors && !connectorsError && (
                    <div className="bg-white rounded-lg border-2 border-dashed border-gray-300 p-12 text-center">
                      <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                        <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                        </svg>
                      </div>
                      <h3 className="text-lg font-semibold text-gray-900 mb-2">No connectors available</h3>
                      <p className="text-gray-600 mb-4">Get started by adding your first connector</p>
                      <button className="px-6 py-3 bg-purple-600 text-white font-medium rounded-lg hover:bg-purple-700">
                        Add Your First Connector
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>
          ) : (
            // Dashboard Page
            <div>
              <h1 className="text-3xl font-bold text-gray-900 mb-6">JMobbin</h1>

          {/* Stats Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
            {/* Left Column - Company Stats */}
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <div className="space-y-6">
                <div className="flex items-center space-x-3 pb-4 border-b border-gray-100">
                  <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
                    <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
                    </svg>
                  </div>
                  <div>
                    <div className="text-3xl font-bold text-gray-900">2</div>
                    <div className="text-sm text-gray-500 flex items-center space-x-1">
                      <span>Stakeholders</span>
                      <InfoIcon />
                    </div>
                  </div>
                </div>

                <div className="flex items-center space-x-3 pb-4 border-b border-gray-100">
                  <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                    <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <div>
                    <div className="text-3xl font-bold text-gray-900">30</div>
                    <div className="text-sm text-gray-500 flex items-center space-x-1">
                      <span>Total shares</span>
                      <InfoIcon />
                    </div>
                  </div>
                </div>

                <div className="flex items-center space-x-3 pb-4 border-b border-gray-100">
                  <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
                    <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                  </div>
                  <div>
                    <div className="text-3xl font-bold text-gray-900">38</div>
                    <div className="text-sm text-gray-500 flex items-center space-x-1">
                      <span>Total securities</span>
                      <InfoIcon />
                    </div>
                  </div>
                </div>

                <div className="flex items-center space-x-3 pb-4 border-b border-gray-100">
                  <div className="w-10 h-10 bg-yellow-100 rounded-lg flex items-center justify-center">
                    <svg className="w-6 h-6 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <div>
                    <div className="text-3xl font-bold text-gray-900">$100</div>
                    <div className="text-sm text-gray-500 flex items-center space-x-1">
                      <span>Valuation</span>
                      <InfoIcon />
                    </div>
                  </div>
                </div>

                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 bg-indigo-100 rounded-lg flex items-center justify-center">
                    <svg className="w-6 h-6 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                    </svg>
                  </div>
                  <div>
                    <div className="text-3xl font-bold text-gray-900">$2.63157</div>
                    <div className="text-sm text-gray-500 flex items-center space-x-1">
                      <span>Share price</span>
                      <InfoIcon />
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Middle Column - Ownership */}
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h2 className="text-lg font-semibold text-gray-900">Ownership</h2>
                  <p className="text-sm text-gray-500">Equity distribution in your company</p>
                </div>
                <button className="text-sm text-purple-600 font-medium hover:text-purple-700">
                  Download cap table
                </button>
              </div>

              {/* Donut Chart */}
              <div className="flex justify-center mb-6">
                <div className="relative w-48 h-48">
                  <svg viewBox="0 0 100 100" className="transform -rotate-90">
                    {/* Green segment (Jon Smith - 68.42%) */}
                    <circle
                      cx="50"
                      cy="50"
                      r="40"
                      fill="none"
                      stroke="#a3e635"
                      strokeWidth="20"
                      strokeDasharray="171 251"
                      strokeDashoffset="0"
                    />
                    {/* Yellow segment (Unallocated - 21.05%) */}
                    <circle
                      cx="50"
                      cy="50"
                      r="40"
                      fill="none"
                      stroke="#fde047"
                      strokeWidth="20"
                      strokeDasharray="53 251"
                      strokeDashoffset="-171"
                    />
                    {/* Blue segment (Jane Smith - 10.52%) */}
                    <circle
                      cx="50"
                      cy="50"
                      r="40"
                      fill="none"
                      stroke="#60a5fa"
                      strokeWidth="20"
                      strokeDasharray="27 251"
                      strokeDashoffset="-224"
                    />
                  </svg>
                  <div className="absolute inset-0 flex items-center justify-center">
                    <div className="text-4xl">🎂</div>
                  </div>
                </div>
              </div>

              {/* Legend */}
              <div className="flex items-center justify-center space-x-4 mb-6">
                <div className="flex items-center space-x-2">
                  <div className="w-3 h-3 bg-yellow-300 rounded-full"></div>
                  <span className="text-xs text-gray-600">Fully Diluted</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-3 h-3 bg-lime-400 rounded-full"></div>
                  <span className="text-xs text-gray-600">Undiluted</span>
                </div>
              </div>

              {/* Top Stakeholders */}
              <div>
                <h3 className="text-sm font-semibold text-gray-700 mb-3">Top Stakeholders</h3>
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center text-white text-xs font-semibold">
                        JS
                      </div>
                      <span className="text-sm text-gray-700">Jon Smith</span>
                    </div>
                    <span className="text-sm font-semibold text-gray-900">68.42%</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <div className="w-8 h-8 bg-blue-400 rounded-full flex items-center justify-center text-white text-xs font-semibold">
                        JS
                      </div>
                      <span className="text-sm text-gray-700">Jane Smith</span>
                    </div>
                    <span className="text-sm font-semibold text-gray-900">10.52%</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <div className="w-8 h-8 bg-purple-400 rounded-full flex items-center justify-center text-white text-xs font-semibold">
                        UO
                      </div>
                      <span className="text-sm text-gray-700">Unallocated Options</span>
                    </div>
                    <span className="text-sm font-semibold text-gray-900">21.05%</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Right Column - Activity */}
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <div className="mb-4">
                <h2 className="text-lg font-semibold text-gray-900">Activity</h2>
                <p className="text-sm text-gray-500">Last 30 days vs Previous</p>
              </div>

              <div className="flex items-center justify-between py-4 border-b border-gray-100">
                <div className="flex items-center space-x-2">
                  <div className="w-8 h-8 bg-gray-100 rounded-lg flex items-center justify-center">
                    🔔
                  </div>
                  <span className="text-sm font-semibold text-gray-900">1</span>
                  <span className="text-sm text-gray-600">ACTION ITEMS</span>
                </div>
                <ChevronRightIcon />
              </div>

              <div className="space-y-6 mt-6">
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm text-gray-600">Options vested</span>
                    <span className="text-sm text-gray-900">-</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Options granted</span>
                    <span className="text-sm text-gray-900">-</span>
                  </div>
                </div>

                <div>
                  <div className="flex items-center space-x-2 mb-2">
                    <span className="text-2xl font-bold text-gray-900">2</span>
                    <span className="text-green-600">📈</span>
                  </div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm text-gray-600">Offers created</span>
                    <span className="text-sm text-gray-900">-</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Offers signed</span>
                    <span className="text-sm text-gray-900">-</span>
                  </div>
                </div>

                <div>
                  <div className="flex items-center space-x-2 mb-2">
                    <span className="text-2xl font-bold text-gray-900">2</span>
                    <span className="text-green-600">📈</span>
                  </div>
                  <div className="text-sm text-gray-600">Announcements sent</div>
                </div>
              </div>
            </div>
          </div>

          {/* Bottom Section */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Funding Rounds */}
            <div className="lg:col-span-2 bg-white rounded-lg border border-gray-200 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-6">Funding rounds</h2>
              
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-700">Bootstrapped</span>
                  <button className="px-6 py-2 bg-purple-600 text-white text-sm font-medium rounded-lg hover:bg-purple-700">
                    Update
                  </button>
                </div>

                {/* Progress Bar */}
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <div className="flex items-center space-x-2">
                      <span className="text-purple-600">▼</span>
                      <span className="text-gray-700">$20.00 committed</span>
                    </div>
                  </div>
                  <div className="relative">
                    <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                      <div className="h-full bg-gradient-to-r from-purple-600 to-purple-400" style={{ width: '0%' }}></div>
                    </div>
                    <div className="absolute left-0 top-0 h-2 w-0 border-l-2 border-purple-600"></div>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-700">$0.00 committed</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-semibold text-gray-900">$110.00 Raise goal</span>
                    <span className="text-sm text-purple-600 font-medium">23 days left</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Total Options */}
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-gray-900">Total options</h2>
                <span className="px-2 py-1 bg-purple-100 text-purple-700 text-xs font-medium rounded">1 pool</span>
              </div>

              <div className="mb-4">
                <div className="text-2xl font-bold text-gray-900 mb-1">0%</div>
                <div className="text-sm text-gray-500">▼ Allocated</div>
              </div>

              <div className="relative h-2 bg-gray-200 rounded-full mb-4">
                <div className="absolute h-full bg-purple-600 rounded-full" style={{ width: '0%' }}></div>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-sm font-semibold text-gray-900">8</span>
                <span className="text-sm text-gray-600">Total options</span>
              </div>
            </div>
          </div>
            </div>
          )}
        </main>
      </div>

      {/* Configuration Modal */}
      {showConfigModal && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex items-center justify-center min-h-screen px-4 pt-4 pb-20 text-center sm:block sm:p-0">
            {/* Background overlay */}
            <div 
              className="fixed inset-0 transition-opacity bg-gray-500 bg-opacity-75"
              onClick={handleCloseModal}
            ></div>

            {/* Modal panel */}
            <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-2xl sm:w-full">
              {/* Header */}
              <div className="bg-gradient-to-r from-purple-600 to-blue-600 px-6 py-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-xl font-semibold text-white">
                      Create Server
                    </h3>
                    <p className="text-purple-100 text-sm mt-1">
                      Create a new {selectedConnector?.name} MCP server instance
                    </p>
                  </div>
                  <button
                    onClick={handleCloseModal}
                    className="text-white hover:text-gray-200 transition-colors"
                  >
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
              </div>

              {/* Body */}
              <div className="px-6 py-6 max-h-96 overflow-y-auto">
                {loadingSchema ? (
                  <div className="flex items-center justify-center py-12">
                    <div className="text-center">
                      <div className="inline-block animate-spin rounded-full h-10 w-10 border-b-2 border-purple-600"></div>
                      <p className="mt-4 text-gray-600">Loading configuration schema...</p>
                    </div>
                  </div>
                ) : connectorSchema ? (
                  <div>
                    {/* Server Name Input */}
                    <div className="mb-6 pb-6 border-b border-gray-200">
                      <label htmlFor="serverName" className="block text-sm font-medium text-gray-700 mb-2">
                        Server Name <span className="text-red-500">*</span>
                      </label>
                      <input
                        type="text"
                        id="serverName"
                        value={serverName}
                        onChange={(e) => setServerName(e.target.value)}
                        placeholder={`e.g., ${selectedConnector?.name} Production`}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                        required
                      />
                      <p className="mt-1 text-xs text-gray-500">
                        A friendly name to identify this server instance
                      </p>
                    </div>

                    {/* Token Expiry Date Input */}
                    <div className="mb-6 pb-6 border-b border-gray-200">
                      <label htmlFor="tokenExpiresAt" className="block text-sm font-medium text-gray-700 mb-2">
                        Token Expiry Date (Optional)
                      </label>
                      <input
                        type="datetime-local"
                        id="tokenExpiresAt"
                        value={tokenExpiresAt}
                        onChange={(e) => setTokenExpiresAt(e.target.value)}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                      />
                      <p className="mt-1 text-xs text-gray-500">
                        When should the generated token expire? Leave blank for no expiration
                      </p>
                    </div>

                    {/* Configuration Form */}
                    <div className="rjsf-form-wrapper">
                      <h4 className="text-sm font-semibold text-gray-700 mb-4">Configuration</h4>
                      <Form
                        schema={connectorSchema}
                        validator={validator}
                        formData={formData}
                        onChange={(e) => setFormData(e.formData)}
                        onSubmit={handleFormSubmit}
                        uiSchema={{
                          'ui:submitButtonOptions': {
                            norender: true
                          }
                        }}
                      >
                        {/* Custom submit button rendered outside */}
                        <div></div>
                      </Form>
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <p className="text-red-600">Failed to load configuration schema</p>
                  </div>
                )}
              </div>

              {/* Footer */}
              {connectorSchema && !loadingSchema && (
                <div className="bg-gray-50 px-6 py-4 flex items-center justify-end space-x-3 border-t border-gray-200">
                  <button
                    onClick={handleCloseModal}
                    className="px-4 py-2 border border-gray-300 text-gray-700 text-sm font-medium rounded-lg hover:bg-gray-100"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={() => {
                      // Trigger form submission
                      const form = document.querySelector('.rjsf-form-wrapper form');
                      if (form) {
                        form.dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }));
                      }
                    }}
                    className="px-4 py-2 bg-purple-600 text-white text-sm font-medium rounded-lg hover:bg-purple-700"
                  >
                    Create Server
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;

