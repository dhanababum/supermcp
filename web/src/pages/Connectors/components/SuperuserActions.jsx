import React, { useState } from 'react';
import { api } from '../../../services/api';
import UserSearchModal from './UserSearchModal';
import { Notification } from '../../../components/common';

const SuperuserActions = ({ connector, onAccessUpdate }) => {
  const [showAccessModal, setShowAccessModal] = useState(false);
  const [showUserSearchModal, setShowUserSearchModal] = useState(false);
  const [accessList, setAccessList] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [notification, setNotification] = useState(null);

  const handleManageAccess = async () => {
    setLoading(true);
    setError(null);
    try {
      const access = await api.getConnectorAccess(connector.id);
      setAccessList(access);
      setShowAccessModal(true);
    } catch (err) {
      setError('Failed to load access list');
      console.error('Error loading connector access:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCloseModal = () => {
    setShowAccessModal(false);
    setAccessList([]);
    setError(null);
  };

  const handleCloseUserSearchModal = () => {
    setShowUserSearchModal(false);
  };

  const handleUserGranted = async (user) => {
    // Refresh the access list
    await handleManageAccess();
    if (onAccessUpdate) {
      onAccessUpdate();
    }
    setNotification({
      message: `Access granted to ${user.email}`,
      type: 'success'
    });
  };

  const handleRevokeAccess = async (userId) => {
    if (!window.confirm('Are you sure you want to revoke access for this user?')) {
      return;
    }

    try {
      await api.revokeConnectorAccess(userId, connector.id);
      // Refresh the access list
      await handleManageAccess();
      if (onAccessUpdate) {
        onAccessUpdate();
      }
      setNotification({
        message: 'Access revoked successfully',
        type: 'success'
      });
    } catch (err) {
      setError('Failed to revoke access');
      setNotification({
        message: 'Failed to revoke access',
        type: 'error'
      });
      console.error('Revoke access error:', err);
    }
  };

  return (
    <>
      <div className="flex items-center space-x-2">
        <button
          onClick={handleManageAccess}
          disabled={loading}
          className="px-3 py-1.5 text-sm bg-purple-100 text-purple-700 rounded-md hover:bg-purple-200 transition-colors disabled:opacity-50"
        >
          {loading ? 'Loading...' : 'Manage Access'}
        </button>
      </div>

      {/* Access Management Modal */}
      {showAccessModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-hidden">
            {/* Header */}
            <div className="flex items-center justify-between p-6 border-b border-gray-200">
              <div>
                <h2 className="text-xl font-semibold text-gray-900">Manage Access</h2>
                <p className="text-sm text-gray-600 mt-1">{connector.name}</p>
              </div>
              <button
                onClick={handleCloseModal}
                className="text-gray-400 hover:text-gray-600 transition-colors"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Content */}
            <div className="p-6 overflow-y-auto max-h-[calc(90vh-140px)]">
              {error ? (
                <div className="text-center py-8">
                  <div className="text-red-600 mb-4">
                    <svg className="w-12 h-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <p className="text-red-600 font-medium">{error}</p>
                </div>
              ) : accessList.length > 0 ? (
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <h3 className="text-lg font-medium text-gray-900">Users with Access</h3>
                    <button
                      onClick={() => setShowUserSearchModal(true)}
                      className="px-3 py-1.5 text-sm bg-purple-600 text-white rounded-md hover:bg-purple-700 transition-colors"
                    >
                      Grant Access
                    </button>
                  </div>
                  <div className="space-y-3">
                    {accessList.map((access) => (
                      <div key={access.id} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                        <div>
                          <p className="font-medium text-gray-900">{access.user_email}</p>
                          <p className="text-sm text-gray-500">
                            Granted by: {access.granted_by_email}
                          </p>
                          <p className="text-xs text-gray-400">
                            {new Date(access.created_at).toLocaleDateString()}
                          </p>
                        </div>
                        <button
                          onClick={() => handleRevokeAccess(access.user_id)}
                          className="px-3 py-1 text-sm bg-red-100 text-red-700 rounded-md hover:bg-red-200 transition-colors"
                        >
                          Revoke
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="text-center py-8">
                  <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z" />
                    </svg>
                  </div>
                  <h3 className="text-lg font-medium text-gray-900 mb-2">No Users with Access</h3>
                  <p className="text-gray-600 mb-4">
                    No users have been granted access to this connector yet.
                  </p>
                  <button
                    onClick={() => setShowUserSearchModal(true)}
                    className="px-4 py-2 bg-purple-600 text-white text-sm font-medium rounded-lg hover:bg-purple-700"
                  >
                    Grant Access to User
                  </button>
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="flex items-center justify-end p-6 border-t border-gray-200 bg-gray-50">
              <button
                onClick={handleCloseModal}
                className="px-4 py-2 text-gray-700 text-sm font-medium rounded-lg hover:bg-gray-200 transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* User Search Modal */}
      <UserSearchModal
        isOpen={showUserSearchModal}
        onClose={handleCloseUserSearchModal}
        onUserSelect={handleUserGranted}
        connectorId={connector.id}
        existingAccess={accessList}
      />

      {/* Notification */}
      {notification && (
        <Notification
          message={notification.message}
          type={notification.type}
          onClose={() => setNotification(null)}
        />
      )}
    </>
  );
};

export default SuperuserActions;
