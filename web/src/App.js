import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useNavigate, useLocation } from 'react-router-dom';
import { Sidebar, Banner } from './components/layout';
import { ErrorBoundary } from './components/common';
import { Dashboard, Connectors, Servers, ServerTools, MCPClient } from './pages';
import { Auth } from './pages/Auth';
import OAuthCallback from './pages/OAuthCallback';
import { AuthProvider, useAuth } from './contexts/AuthContext';

// Protected Route Component
const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  React.useEffect(() => {
    if (isAuthenticated === false || isAuthenticated === null) {
      navigate('/auth/login', { state: { from: location } });
    }
  }, [isAuthenticated, navigate, location]);

  if (isLoading) {
    // Loading state
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-purple-600"></div>
      </div>
    );
  }

  if (isAuthenticated === false) {
    return null; // Will redirect to login
  }

  return children;
};

// Main App Layout Component
const AppLayout = ({ children }) => {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <Sidebar
        collapsed={sidebarCollapsed}
        onToggleCollapse={() => setSidebarCollapsed(!sidebarCollapsed)}
      />

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Banner */}
        <Banner />

        {/* Main Content Area */}
        <main className="flex-1 overflow-y-auto p-6">
          {children}
        </main>
      </div>
    </div>
  );
};

// Server Tools Page with Server Selection
const ServerToolsPage = () => {
  const [selectedServer, setSelectedServer] = useState(null);
  const navigate = useNavigate();

  const handleSelectServer = (server) => {
    setSelectedServer(server);
  };

  const handleBackToServers = () => {
    setSelectedServer(null);
    navigate('/servers');
  };

  if (!selectedServer) {
    return (
      <Servers
        onNavigate={(route) => navigate(`/${route}`)}
        onSelectServer={handleSelectServer}
      />
    );
  }

  return (
    <ServerTools
      server={selectedServer}
      onBack={handleBackToServers}
    />
  );
};

function App() {
  return (
    <ErrorBoundary>
      <Router>
        <AuthProvider>
          <Routes>
        {/* Authentication Routes */}
        <Route path="/auth/login" element={<Auth />} />
        <Route path="/auth/signup" element={<Auth />} />
        
        {/* OAuth Callback */}
        <Route path="/oauth/callback" element={<OAuthCallback />} />
        
        {/* Protected Routes */}
        <Route path="/" element={
          <ProtectedRoute>
            <AppLayout>
              <Dashboard />
            </AppLayout>
          </ProtectedRoute>
        } />
        
        <Route path="/dashboard" element={
          <ProtectedRoute>
            <AppLayout>
              <Dashboard />
            </AppLayout>
          </ProtectedRoute>
        } />
        
        <Route path="/connectors" element={
          <ProtectedRoute>
            <AppLayout>
              <Connectors />
            </AppLayout>
          </ProtectedRoute>
        } />
        
        <Route path="/servers" element={
          <ProtectedRoute>
            <AppLayout>
              <ServerToolsPage />
            </AppLayout>
          </ProtectedRoute>
        } />
        
        <Route path="/server-tools" element={
          <ProtectedRoute>
            <AppLayout>
              <ServerToolsPage />
            </AppLayout>
          </ProtectedRoute>
        } />
        
        <Route path="/mcp-client" element={
          <ProtectedRoute>
            <AppLayout>
              <MCPClient />
            </AppLayout>
          </ProtectedRoute>
        } />
        
        {/* Redirect root to dashboard */}
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        </Routes>
        </AuthProvider>
      </Router>
    </ErrorBoundary>
  );
}

export default App;
