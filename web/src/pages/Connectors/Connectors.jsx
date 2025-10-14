import React, { useState } from 'react';
import { useConnectors } from '../../hooks';
import { useAuth } from '../../contexts/AuthContext';
import { LoadingSpinner, ErrorMessage, Notification } from '../../components/common';
import { 
  ConnectorCard, 
  ConfigurationModal, 
  AddConnectorModal, 
  RegisterConnectorModal,
  ActivateConnectorModal,
  RegisterUrlModal,
  AccessRequestPrompt 
} from './components';

const Connectors = () => {
  const { connectors, loading, error, refetch } = useConnectors(true);
  const { isSuperuser, user } = useAuth();
  const [selectedConnector, setSelectedConnector] = useState(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [showRegisterModal, setShowRegisterModal] = useState(false);
  const [showActivateModal, setShowActivateModal] = useState(false);
  const [showRegisterUrlModal, setShowRegisterUrlModal] = useState(false);
  const [connectorToActivate, setConnectorToActivate] = useState(null);
  const [connectorToRegisterUrl, setConnectorToRegisterUrl] = useState(null);
  const [notification, setNotification] = useState(null);

  const handleConfigureConnector = (connector) => {
    setSelectedConnector(connector);
  };

  const handleCloseModal = () => {
    setSelectedConnector(null);
  };

  const handleSuccess = () => {
    // Refresh connectors list
    if (refetch) {
      refetch();
    }
  };

  const handleAddConnector = () => {
    setShowAddModal(true);
  };

  const handleCloseAddModal = () => {
    setShowAddModal(false);
  };

  const handleRegisterConnector = () => {
    setShowRegisterModal(true);
  };

  const handleCloseRegisterModal = () => {
    setShowRegisterModal(false);
  };

  const handleRegisterSuccess = (result) => {
    setNotification({
      type: 'success',
      message: `Connector "${result.name}" registered successfully! You can now activate it.`
    });
    handleSuccess();
  };

  const handleActivateConnector = (connector) => {
    setConnectorToActivate(connector);
    setShowActivateModal(true);
  };

  const handleCloseActivateModal = () => {
    setShowActivateModal(false);
    setConnectorToActivate(null);
  };

  const handleActivateSuccess = (result) => {
    setNotification({
      type: 'success',
      message: `Connector "${result.name}" activated successfully! Found ${result.tools_count} tools.`
    });
    handleSuccess();
  };

  const handleRegisterUrl = (connector) => {
    setConnectorToRegisterUrl(connector);
    setShowRegisterUrlModal(true);
  };

  const handleCloseRegisterUrlModal = () => {
    setShowRegisterUrlModal(false);
    setConnectorToRegisterUrl(null);
  };

  const handleRegisterUrlSuccess = (result) => {
    setNotification({
      type: 'success',
      message: `Connector "${result.connector?.name || 'Unknown'}" registered with URL successfully! Mode updated to ${result.connector?.mode || 'active'}.`
    });
    handleSuccess();
  };


  return (
    <div>
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Connectors</h1>
        <p className="text-gray-600">
          {isSuperuser() 
            ? "Manage and configure data connectors for your organization" 
            : "View and use connectors you have access to"
          }
        </p>
      </div>

      {loading ? (
        <LoadingSpinner message="Loading connectors..." />
      ) : error ? (
        <ErrorMessage
          title="Error loading connectors"
          message={error}
        />
      ) : (
        <div>
          {/* Notification */}
          {notification && (
            <Notification
              type={notification.type}
              message={notification.message}
              onClose={() => setNotification(null)}
            />
          )}

          {/* Role-based Action Bar */}
          {isSuperuser() && (
            <div className="mb-6 flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <button 
                  onClick={handleRegisterConnector}
                  className="px-4 py-2 bg-purple-100 text-purple-700 text-sm font-medium rounded-lg hover:bg-purple-200 border border-purple-300 flex items-center space-x-2"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                  </svg>
                  <span>Register Connector</span>
                </button>
                <button 
                  onClick={() => refetch()}
                  className="px-4 py-2 border border-gray-300 text-gray-700 text-sm font-medium rounded-lg hover:bg-gray-50 flex items-center space-x-2"
                >
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
          )}

          {/* Regular User Action Bar */}
          {!isSuperuser() && connectors.length > 0 && (
            <div className="mb-6 flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <button 
                  onClick={() => refetch()}
                  className="px-4 py-2 border border-gray-300 text-gray-700 text-sm font-medium rounded-lg hover:bg-gray-50 flex items-center space-x-2"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                  <span>Refresh</span>
                </button>
              </div>
              <div className="flex items-center space-x-2">
                <input
                  type="text"
                  placeholder="Search your connectors..."
                  className="px-4 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                />
              </div>
            </div>
          )}

          {/* Role-based Content */}
          {isSuperuser() ? (
            // Superuser: Show all connectors with management capabilities
            <>
              {/* Connectors Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {connectors.map((connector) => (
                  <ConnectorCard
                    key={connector.id}
                    connector={connector}
                    onConfigure={handleConfigureConnector}
                    onDelete={handleSuccess}
                    onActivate={handleActivateConnector}
                    onRegisterUrl={handleRegisterUrl}
                  />
                ))}
              </div>

              {/* Empty State for Superusers */}
              {connectors.length === 0 && (
                <div className="bg-white rounded-lg border-2 border-dashed border-gray-300 p-12 text-center">
                  <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                    </svg>
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">No connectors available</h3>
                  <p className="text-gray-600 mb-4">Get started by adding your first connector</p>
                  <button 
                    onClick={handleAddConnector}
                    className="px-6 py-3 bg-purple-600 text-white font-medium rounded-lg hover:bg-purple-700"
                  >
                    Add Your First Connector
                  </button>
                </div>
              )}
            </>
          ) : (
            // Regular User: Show accessible connectors or access request prompt
            <>
              {connectors.length > 0 ? (
                // User has access to some connectors
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {connectors.map((connector) => (
                    <ConnectorCard
                      key={connector.id}
                      connector={connector}
                      onConfigure={handleConfigureConnector}
                    />
                  ))}
                </div>
              ) : (
                // User has no connector access
                <AccessRequestPrompt />
              )}
            </>
          )}
        </div>
      )}

      {/* Configuration Modal */}
      {selectedConnector && (
        <ConfigurationModal
          connector={selectedConnector}
          onClose={handleCloseModal}
          onSuccess={handleSuccess}
        />
      )}

      {/* Add Connector Modal - Superuser Only (Old Method) */}
      {isSuperuser() && (
        <AddConnectorModal
          isOpen={showAddModal}
          onClose={handleCloseAddModal}
          onSuccess={handleSuccess}
        />
      )}

      {/* Register Connector Modal - Superuser Only (Step 1) */}
      {isSuperuser() && (
        <RegisterConnectorModal
          isOpen={showRegisterModal}
          onClose={handleCloseRegisterModal}
          onSuccess={handleRegisterSuccess}
        />
      )}

      {/* Activate Connector Modal - Superuser Only (Step 2) */}
      {isSuperuser() && (
        <ActivateConnectorModal
          isOpen={showActivateModal}
          onClose={handleCloseActivateModal}
          connector={connectorToActivate}
          onSuccess={handleActivateSuccess}
        />
      )}

      {/* Register URL Modal - Superuser Only (For Sync Mode) */}
      {isSuperuser() && (
        <RegisterUrlModal
          isOpen={showRegisterUrlModal}
          onClose={handleCloseRegisterUrlModal}
          connector={connectorToRegisterUrl}
          onSuccess={handleRegisterUrlSuccess}
        />
      )}

    </div>
  );
};

export default Connectors;

