import React, { useState, useEffect, useCallback } from 'react';
import { api } from '../../../services/api';

const UserSearchModal = ({ isOpen, onClose, onUserSelect, connectorId, existingAccess = [] }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedUser, setSelectedUser] = useState(null);

  // Debounced search
  const debouncedSearch = useCallback(
    (() => {
      let timeoutId;
      return (query) => {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(() => {
          if (query && query.length >= 2) {
            performSearch(query);
          } else {
            setSearchResults([]);
          }
        }, 300);
      };
    })(),
    []
  );

  const performSearch = async (query) => {
    setLoading(true);
    setError(null);
    try {
      const results = await api.searchUsers(query);
      // Filter out users who already have access
      const existingUserIds = existingAccess.map(access => access.user_id);
      const filteredResults = results.filter(user => !existingUserIds.includes(user.id));
      setSearchResults(filteredResults);
    } catch (err) {
      setError('Failed to search users');
      console.error('User search error:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      setSearchQuery('');
      setSearchResults([]);
      setSelectedUser(null);
      setError(null);
    }
  }, [isOpen]);

  useEffect(() => {
    debouncedSearch(searchQuery);
  }, [searchQuery, debouncedSearch]);

  const handleUserSelect = (user) => {
    setSelectedUser(user);
  };

  const handleGrantAccess = async () => {
    if (!selectedUser || !connectorId) return;

    try {
      await api.grantConnectorAccess(selectedUser.id, connectorId);
      onUserSelect(selectedUser);
      onClose();
    } catch (err) {
      setError('Failed to grant access');
      console.error('Grant access error:', err);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">Grant Connector Access</h2>
            <p className="text-sm text-gray-600 mt-1">Search and select a user to grant access</p>
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
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-140px)]">
          {/* Search Input */}
          <div className="mb-6">
            <label htmlFor="userSearch" className="block text-sm font-medium text-gray-700 mb-2">
              Search Users
            </label>
            <div className="relative">
              <input
                type="text"
                id="userSearch"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Type user email to search..."
                className="w-full px-4 py-3 pl-10 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent"
              />
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
              {loading && (
                <div className="absolute inset-y-0 right-0 pr-3 flex items-center">
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-brand-600"></div>
                </div>
              )}
            </div>
            <p className="text-xs text-gray-500 mt-1">Enter at least 2 characters to search</p>
          </div>

          {/* Error Message */}
          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
              <div className="flex items-center">
                <svg className="w-5 h-5 text-red-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span className="text-red-700 text-sm">{error}</span>
              </div>
            </div>
          )}

          {/* Search Results */}
          {searchQuery.length >= 2 && (
            <div className="mb-6">
              <h3 className="text-sm font-medium text-gray-700 mb-3">Search Results</h3>
              {searchResults.length > 0 ? (
                <div className="space-y-2 max-h-60 overflow-y-auto">
                  {searchResults.map((user) => (
                    <div
                      key={user.id}
                      onClick={() => handleUserSelect(user)}
                      className={`p-3 border rounded-lg cursor-pointer transition-colors ${
                        selectedUser?.id === user.id
                          ? 'border-brand-500 bg-brand-50'
                          : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="font-medium text-gray-900">{user.email}</p>
                          <div className="flex items-center space-x-2 mt-1">
                            <span className={`px-2 py-1 text-xs rounded-full ${
                              user.is_superuser 
                                ? 'bg-brand-100 text-brand-700' 
                                : 'bg-blue-100 text-blue-700'
                            }`}>
                              {user.is_superuser ? 'Superuser' : 'User'}
                            </span>
                            <span className={`px-2 py-1 text-xs rounded-full ${
                              user.is_active 
                                ? 'bg-green-100 text-green-700' 
                                : 'bg-gray-100 text-gray-700'
                            }`}>
                              {user.is_active ? 'Active' : 'Inactive'}
                            </span>
                            {user.is_verified && (
                              <span className="px-2 py-1 text-xs rounded-full bg-green-100 text-green-700">
                                Verified
                              </span>
                            )}
                          </div>
                        </div>
                        {selectedUser?.id === user.id && (
                          <div className="text-brand-600">
                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                            </svg>
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              ) : !loading && (
                <div className="text-center py-8 text-gray-500">
                  <svg className="w-12 h-12 mx-auto mb-3 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z" />
                  </svg>
                  <p>No users found matching "{searchQuery}"</p>
                </div>
              )}
            </div>
          )}

          {/* Selected User Summary */}
          {selectedUser && (
            <div className="mb-6 p-4 bg-brand-50 border border-brand-200 rounded-lg">
              <h3 className="text-sm font-medium text-brand-900 mb-2">Selected User</h3>
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-brand-900">{selectedUser.email}</p>
                  <p className="text-sm text-brand-700">
                    {selectedUser.is_superuser ? 'Superuser' : 'Regular User'} • {selectedUser.is_active ? 'Active' : 'Inactive'}
                  </p>
                </div>
                <button
                  onClick={() => setSelectedUser(null)}
                  className="text-brand-600 hover:text-brand-800"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end p-6 border-t border-gray-200 bg-gray-50">
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-700 text-sm font-medium rounded-lg hover:bg-gray-200 transition-colors mr-3"
          >
            Cancel
          </button>
          <button
            onClick={handleGrantAccess}
            disabled={!selectedUser}
            className="px-4 py-2 bg-brand-600 text-white text-sm font-medium rounded-lg hover:bg-brand-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            Grant Access
          </button>
        </div>
      </div>
    </div>
  );
};

export default UserSearchModal;
