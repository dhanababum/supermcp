import React, { useState } from 'react';
import { useServers } from '../../hooks';
import { LoadingSpinner, ErrorMessage, Notification } from '../../components/common';
import { ServerTable } from './components';
import { api } from '../../services/api';
import ConfirmationModal from '../../components/ConfirmationModal';

const Servers = ({ onNavigate, onSelectServer }) => {
  const { servers, loading, error, refetch } = useServers(true);
  const [notification, setNotification] = useState(null);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [serverToDelete, setServerToDelete] = useState(null);

  const handleViewServer = (server) => {
    onSelectServer(server);
    onNavigate('server-tools');
  };

  const handleViewTokens = (server) => {
    onSelectServer(server);
    onNavigate('server-tokens');
  };

  const handleDeleteServer = (server) => {
    setServerToDelete(server);
    setShowDeleteModal(true);
  };

  const handleConfirmDelete = async () => {
    if (!serverToDelete) return;

    setShowDeleteModal(false);

    try {
      const data = await api.deleteServer(serverToDelete.id);
      
      setNotification({
        type: 'success',
        message: `${data.message} • Deleted tokens: ${data.deleted_tokens} • Deleted tools: ${data.deleted_tools}`
      });
      
      refetch();
    } catch (err) {
      console.error('Error deleting server:', err);
      
      setNotification({
        type: 'error',
        message: `Failed to delete server: ${err.message}`
      });
    } finally {
      setServerToDelete(null);
    }
  };

  const handleCancelDelete = () => {
    setShowDeleteModal(false);
    setServerToDelete(null);
  };

  return (
    <>
      {/* Notification Toast */}
      {notification && (
        <Notification
          message={notification.message}
          type={notification.type}
          duration={5000}
          onClose={() => setNotification(null)}
        />
      )}

      {/* Delete Confirmation Modal */}
      <ConfirmationModal
        isOpen={showDeleteModal}
        onClose={handleCancelDelete}
        onConfirm={handleConfirmDelete}
        title="Delete Server"
        message={serverToDelete ? `Are you sure you want to delete server "${serverToDelete.server_name}"? This will permanently delete the server configuration, all associated tokens, and all associated tools. This action cannot be undone.` : ''}
        confirmText="Delete Server"
        cancelText="Cancel"
        isDestructive={true}
      />

      <div>
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">MCP Servers</h1>
          <p className="text-gray-600">Manage your configured MCP server instances</p>
        </div>

      {loading ? (
        <LoadingSpinner message="Loading servers..." />
      ) : error ? (
        <ErrorMessage
          title="Error loading servers"
          message={error}
        />
      ) : (
        <div>
          {/* Action Bar */}
          <div className="mb-6 flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <button 
                onClick={() => onNavigate('connectors')}
                className="px-4 py-2 bg-purple-600 text-white text-sm font-medium rounded-lg hover:bg-purple-700 flex items-center space-x-2"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                <span>Create New Server</span>
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
            <div className="text-sm text-gray-600">
              Total Servers: <span className="font-semibold text-gray-900">{servers.length}</span>
            </div>
          </div>

          {/* Servers List */}
          <ServerTable
            servers={servers}
            onView={handleViewServer}
            onDelete={handleDeleteServer}
            onRefresh={refetch}
            onViewTokens={handleViewTokens}
          />
        </div>
      )}
      </div>
    </>
  );
};

export default Servers;

