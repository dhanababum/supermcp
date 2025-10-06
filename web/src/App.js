import React, { useState, useEffect } from 'react';
import { Sidebar, Banner } from './components/layout';
import { Dashboard, Connectors, Servers, ServerTools, MCPClient } from './pages';
import OAuthCallback from './pages/OAuthCallback';

function App() {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [currentRoute, setCurrentRoute] = useState('dashboard');
  const [selectedServer, setSelectedServer] = useState(null);

  // Handle URL-based routing for OAuth callback
  useEffect(() => {
    const path = window.location.pathname;
    if (path === '/oauth/callback') {
      setCurrentRoute('oauth-callback');
    }
  }, []);

  const handleNavigate = (route) => {
    setCurrentRoute(route);
    if (route !== 'server-tools') {
      setSelectedServer(null);
    }
  };

  const handleSelectServer = (server) => {
    setSelectedServer(server);
  };

  const handleBackToServers = () => {
    setCurrentRoute('servers');
    setSelectedServer(null);
  };

  const renderPage = () => {
    switch (currentRoute) {
      case 'connectors':
        return <Connectors />;
      case 'servers':
        return (
          <Servers
            onNavigate={handleNavigate}
            onSelectServer={handleSelectServer}
          />
        );
      case 'server-tools':
        return (
          <ServerTools
            server={selectedServer}
            onBack={handleBackToServers}
          />
        );
      case 'mcp-client':
        return <MCPClient />;
      case 'oauth-callback':
        return <OAuthCallback />;
      case 'dashboard':
      default:
        return <Dashboard />;
    }
  };

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <Sidebar
        collapsed={sidebarCollapsed}
        onToggleCollapse={() => setSidebarCollapsed(!sidebarCollapsed)}
        currentRoute={currentRoute}
        onRouteChange={handleNavigate}
      />

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        {/* <Header /> */}

        {/* Banner */}
        <Banner />

        {/* Main Content Area */}
        <main className="flex-1 overflow-y-auto p-6">
          {renderPage()}
        </main>
      </div>
    </div>
  );
}

export default App;
