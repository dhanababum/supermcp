import React, { useState } from 'react';
import { ServerConfigModal, ServerEditModal } from './index';

const ServerTable = ({ servers, onView, onDelete, onRefresh, onViewTokens }) => {
  const [configModalOpen, setConfigModalOpen] = useState(false);
  const [editModalOpen, setEditModalOpen] = useState(false);
  const [selectedServer, setSelectedServer] = useState(null);
  const [serverToEdit, setServerToEdit] = useState(null);

  const handleViewConfig = (server) => {
    setSelectedServer(server);
    setConfigModalOpen(true);
  };

  const handleCloseConfig = () => {
    setConfigModalOpen(false);
    setSelectedServer(null);
  };

  const handleEditServer = (server) => {
    setServerToEdit(server);
    setEditModalOpen(true);
  };

  const handleCloseEdit = () => {
    setEditModalOpen(false);
    setServerToEdit(null);
  };

  const handleEditSuccess = () => {
    if (onRefresh) {
      onRefresh();
    }
  };

  if (servers.length === 0) {
    return (
      <div className="bg-white rounded-lg border-2 border-dashed border-gray-300 p-12 text-center">
        <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01" />
          </svg>
        </div>
        <h3 className="text-lg font-semibold text-gray-900 mb-2">No servers configured</h3>
        <p className="text-gray-600 mb-4">Get started by creating your first MCP server</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
      <div className="overflow-x-auto">
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
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider sticky right-0 bg-gray-50">
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
                <div className="text-sm text-gray-900">{server.connector_id}</div>
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
              <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium sticky right-0 bg-white">
                <button 
                  onClick={() => onView(server)}
                  className="text-purple-600 hover:text-purple-900 mr-3"
                >
                  View
                </button>
                <button 
                  onClick={() => handleViewConfig(server)}
                  className="text-green-600 hover:text-green-900 mr-3"
                >
                  Config
                </button>
                <button 
                  onClick={() => handleEditServer(server)}
                  className="text-blue-600 hover:text-blue-900 mr-3"
                >
                  Edit
                </button>
                <button 
                  onClick={() => onViewTokens && onViewTokens(server)}
                  className="text-orange-600 hover:text-orange-900 mr-3"
                >
                  Tokens
                </button>
                <button 
                  onClick={() => onDelete(server)}
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
      
      {/* Server Config Modal */}
      <ServerConfigModal
        server={selectedServer}
        isOpen={configModalOpen}
        onClose={handleCloseConfig}
      />
      
      {/* Server Edit Modal */}
      <ServerEditModal
        server={serverToEdit}
        isOpen={editModalOpen}
        onClose={handleCloseEdit}
        onSuccess={handleEditSuccess}
      />
    </div>
  );
};

export default ServerTable;

