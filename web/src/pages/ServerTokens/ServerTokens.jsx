import React, { useState, useEffect, useCallback } from 'react';
import { api } from '../../services/api';
import { LoadingSpinner, ErrorMessage, Notification } from '../../components/common';
import ConfirmationModal from '../../components/ConfirmationModal';

const ServerTokens = ({ server, onBack }) => {
  const [tokens, setTokens] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [notification, setNotification] = useState(null);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [tokenToDelete, setTokenToDelete] = useState(null);
  const [deletingTokenId, setDeletingTokenId] = useState(null);
  const [updatingTokenId, setUpdatingTokenId] = useState(null);
  const [tokenExpiresAt, setTokenExpiresAt] = useState('');
  const [createdToken, setCreatedToken] = useState(null);
  const [showTokenModal, setShowTokenModal] = useState(false);

  const fetchTokens = useCallback(async () => {
    if (!server?.id) return;
    
    setLoading(true);
    setError(null);
    try {
      const data = await api.getServerTokens(server.id);
      setTokens(data);
    } catch (err) {
      console.error('Error fetching tokens:', err);
      setError(`Failed to load tokens: ${err.message}`);
    } finally {
      setLoading(false);
    }
  }, [server?.id]);

  useEffect(() => {
    fetchTokens();
  }, [fetchTokens]);

  const handleCreateToken = async () => {
    if (!server?.id) return;

    try {
      const tokenData = {
        expires_at: tokenExpiresAt || null
      };
      
      const response = await api.createServerToken(server.id, tokenData);
      setCreatedToken(response);
      setShowTokenModal(true);
      setShowCreateModal(false);
      setTokenExpiresAt('');
      fetchTokens();
    } catch (err) {
      console.error('Error creating token:', err);
      setNotification({
        type: 'error',
        message: `Failed to create token: ${err.message}`
      });
    }
  };

  const handleDeleteClick = (token) => {
    setTokenToDelete(token);
    setShowDeleteModal(true);
  };

  const handleConfirmDelete = async () => {
    if (!tokenToDelete || !server?.id) return;

    setDeletingTokenId(tokenToDelete.id);
    
    try {
      await api.deleteServerToken(server.id, tokenToDelete.id);
      
      setNotification({
        type: 'success',
        message: 'Token deleted successfully'
      });
      
      setShowDeleteModal(false);
      setTokenToDelete(null);
      fetchTokens();
    } catch (err) {
      console.error('Error deleting token:', err);
      setNotification({
        type: 'error',
        message: `Failed to delete token: ${err.message}`
      });
    } finally {
      setDeletingTokenId(null);
    }
  };

  const handleToggleActive = async (token) => {
    if (!server?.id) return;

    setUpdatingTokenId(token.id);
    
    try {
      await api.updateServerToken(server.id, token.id, {
        is_active: !token.is_active
      });
      
      setNotification({
        type: 'success',
        message: `Token ${!token.is_active ? 'enabled' : 'disabled'} successfully`
      });
      
      fetchTokens();
    } catch (err) {
      console.error('Error updating token:', err);
      setNotification({
        type: 'error',
        message: `Failed to update token: ${err.message}`
      });
    } finally {
      setUpdatingTokenId(null);
    }
  };

  const handleCopyToken = () => {
    if (createdToken?.token) {
      navigator.clipboard.writeText(createdToken.token);
      setNotification({
        type: 'success',
        message: 'Token copied to clipboard!'
      });
    }
  };

  const handleCloseTokenModal = () => {
    setShowTokenModal(false);
    setCreatedToken(null);
  };

  if (!server) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-600">No server selected</p>
      </div>
    );
  }

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

      <div>
        <div className="mb-6">
          <div className="flex items-center space-x-3 mb-2">
            <button
              onClick={onBack}
              className="text-purple-600 hover:text-purple-700 flex items-center space-x-1"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
              <span className="text-sm font-medium">Back to Servers</span>
            </button>
          </div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            {server.server_name} - Tokens
          </h1>
          <p className="text-gray-600">
            Manage authentication tokens for {server.connector_id}
          </p>
        </div>

        {loading ? (
          <LoadingSpinner message="Loading tokens..." />
        ) : error ? (
          <ErrorMessage
            title="Error loading tokens"
            message={error}
          />
        ) : (
          <div>
            {/* Action Bar */}
            <div className="mb-6 flex items-center justify-between">
              <button
                onClick={() => setShowCreateModal(true)}
                className="px-4 py-2 bg-purple-600 text-white text-sm font-medium rounded-lg hover:bg-purple-700 flex items-center space-x-2"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                <span>Create New Token</span>
              </button>
              <div className="text-sm text-gray-600">
                Total Tokens: <span className="font-semibold text-gray-900">{tokens.length}</span>
              </div>
            </div>

            {/* Tokens List */}
            {tokens.length === 0 ? (
              <div className="bg-white rounded-lg border-2 border-dashed border-gray-300 p-12 text-center">
                <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
                  </svg>
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">No tokens configured</h3>
                <p className="text-gray-600 mb-4">Create your first token to get started</p>
              </div>
            ) : (
              <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Token
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Created
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Expires
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
                      {tokens.map((token) => (
                        <tr key={token.id} className="hover:bg-gray-50">
                          <td className="px-6 py-4 whitespace-nowrap">
                            <code className="text-sm font-mono text-gray-900 bg-gray-100 px-2 py-1 rounded">
                              {token.token.substring(0, 20)}...
                            </code>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="text-sm text-gray-900">
                              {new Date(token.created_at).toLocaleDateString()}
                            </div>
                            <div className="text-xs text-gray-500">
                              {new Date(token.created_at).toLocaleTimeString()}
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="text-sm text-gray-900">
                              {token.expires_at 
                                ? new Date(token.expires_at).toLocaleDateString()
                                : 'Never'
                              }
                            </div>
                            {token.expires_at && (
                              <div className="text-xs text-gray-500">
                                {new Date(token.expires_at).toLocaleTimeString()}
                              </div>
                            )}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                              token.is_active 
                                ? 'bg-green-100 text-green-800' 
                                : 'bg-gray-100 text-gray-800'
                            }`}>
                              {token.is_active ? 'Active' : 'Inactive'}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                            <div className="flex items-center justify-end space-x-3">
                              <button
                                onClick={() => handleToggleActive(token)}
                                disabled={updatingTokenId === token.id}
                                className={`w-11 h-6 inline-flex items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 ${
                                  updatingTokenId === token.id
                                    ? 'opacity-50 cursor-not-allowed'
                                    : 'cursor-pointer'
                                } ${
                                  token.is_active ? 'bg-green-600' : 'bg-gray-300'
                                }`}
                                title={token.is_active ? 'Click to disable' : 'Click to enable'}
                              >
                                <span
                                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                                    token.is_active ? 'translate-x-6' : 'translate-x-1'
                                  }`}
                                />
                              </button>
                              <button
                                onClick={() => handleDeleteClick(token)}
                                disabled={deletingTokenId === token.id}
                                className="text-red-600 hover:text-red-900 disabled:opacity-50 disabled:cursor-not-allowed"
                              >
                                {deletingTokenId === token.id ? 'Deleting...' : 'Delete'}
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Create Token Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex items-center justify-center min-h-screen px-4 pt-4 pb-20 text-center sm:block sm:p-0">
            <div 
              className="fixed inset-0 transition-opacity bg-gray-500 bg-opacity-75"
              onClick={() => setShowCreateModal(false)}
            ></div>
            <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
              <div className="bg-gradient-to-r from-purple-600 to-blue-600 px-6 py-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-xl font-semibold text-white">Create New Token</h3>
                  <button
                    onClick={() => setShowCreateModal(false)}
                    className="text-white hover:text-gray-200 transition-colors"
                  >
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
              </div>
              <div className="px-6 py-6">
                <div className="mb-4">
                  <label htmlFor="tokenExpiresAt" className="block text-sm font-medium text-gray-700 mb-2">
                    Expiry Date (Optional)
                  </label>
                  <input
                    type="datetime-local"
                    id="tokenExpiresAt"
                    value={tokenExpiresAt}
                    onChange={(e) => setTokenExpiresAt(e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  />
                  <p className="mt-1 text-xs text-gray-500">
                    When should this token expire? Leave blank for no expiration.
                  </p>
                </div>
              </div>
              <div className="bg-gray-50 px-6 py-4 flex items-center justify-end space-x-3 border-t border-gray-200">
                <button
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 border border-gray-300 text-gray-700 text-sm font-medium rounded-lg hover:bg-gray-100"
                >
                  Cancel
                </button>
                <button
                  onClick={handleCreateToken}
                  className="px-4 py-2 bg-purple-600 text-white text-sm font-medium rounded-lg hover:bg-purple-700"
                >
                  Create Token
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Token Display Modal */}
      {showTokenModal && createdToken && (
        <div className="fixed inset-0 z-[60] overflow-y-auto">
          <div className="flex items-center justify-center min-h-screen px-4">
            <div className="fixed inset-0 bg-gray-900 bg-opacity-75" onClick={handleCloseTokenModal}></div>
            <div className="relative bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 p-6">
              <div className="mb-4">
                <div className="flex items-center justify-center w-12 h-12 bg-green-100 rounded-full mx-auto mb-4">
                  <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <h3 className="text-xl font-semibold text-gray-900 text-center mb-2">
                  Token Created Successfully!
                </h3>
                <p className="text-sm text-gray-600 text-center">
                  Please save this token securely. It will only be shown once.
                </p>
              </div>
              <div className="bg-gray-50 rounded-lg p-4 mb-6">
                <p className="text-xs text-gray-500 mb-2">Access Token</p>
                <div className="flex items-center space-x-2">
                  <code className="flex-1 bg-white border border-gray-300 rounded px-3 py-2 text-sm font-mono text-gray-900 overflow-x-auto">
                    {createdToken.token}
                  </code>
                  <button
                    onClick={handleCopyToken}
                    className="px-4 py-2 bg-purple-600 text-white text-sm font-medium rounded-lg hover:bg-purple-700 flex items-center space-x-2"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                    </svg>
                    <span>Copy</span>
                  </button>
                </div>
              </div>
              <div className="flex justify-end">
                <button
                  onClick={handleCloseTokenModal}
                  className="px-6 py-2 bg-purple-600 text-white text-sm font-medium rounded-lg hover:bg-purple-700"
                >
                  Done
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      <ConfirmationModal
        isOpen={showDeleteModal}
        onClose={() => {
          setShowDeleteModal(false);
          setTokenToDelete(null);
        }}
        onConfirm={handleConfirmDelete}
        title="Delete Token"
        message={tokenToDelete ? `Are you sure you want to delete this token? This action cannot be undone.` : ''}
        confirmText={deletingTokenId ? "Deleting..." : "Delete"}
        cancelText="Cancel"
        isDestructive={true}
      />
    </>
  );
};

export default ServerTokens;

