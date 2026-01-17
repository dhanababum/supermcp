import React, { useState, useRef, useEffect } from 'react';
import { ServerConfigModal, ServerEditModal } from './index';
import ServerMetricsModal from '../../Dashboard/components/ServerMetricsModal';
import { API_BASE_URL } from '../../../services/api';

const ActionDropdown = ({ server, actions }) => {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleAction = (action) => {
    action();
    setIsOpen(false);
  };

  const menuItems = [
    { label: 'View', onClick: actions.onView, color: 'text-brand-600 hover:bg-brand-50' },
    { label: 'Config', onClick: actions.onConfig, color: 'text-green-600 hover:bg-green-50' },
    { label: 'Edit', onClick: actions.onEdit, color: 'text-blue-600 hover:bg-blue-50' },
    { label: 'Tokens', onClick: actions.onTokens, color: 'text-orange-600 hover:bg-orange-50' },
    { label: 'Metrics', onClick: actions.onMetrics, color: 'text-purple-600 hover:bg-purple-50' },
    { label: 'Delete', onClick: actions.onDelete, color: 'text-red-600 hover:bg-red-50' },
  ];

  return (
    <div ref={dropdownRef} className="relative inline-block text-left">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="p-2 rounded-md hover:bg-gray-100 focus:outline-none"
      >
        <svg className="w-5 h-5 text-gray-500" fill="currentColor" viewBox="0 0 20 20">
          <path d="M10 6a2 2 0 110-4 2 2 0 010 4zM10 12a2 2 0 110-4 2 2 0 010 4zM10 18a2 2 0 110-4 2 2 0 010 4z" />
        </svg>
      </button>
      {isOpen && (
        <div className="absolute right-0 z-10 mt-1 w-36 origin-top-right rounded-md bg-white shadow-lg ring-1 ring-black ring-opacity-5">
          <div className="py-1">
            {menuItems.map((item) => (
              <button
                key={item.label}
                onClick={() => handleAction(item.onClick)}
                className={`block w-full px-4 py-2 text-left text-sm ${item.color}`}
              >
                {item.label}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

const ServerIcon = ({ logoName, serverName }) => {
  const [logoError, setLogoError] = useState(false);
  const logoUrl = logoName && typeof logoName === 'string' && logoName.trim() 
    ? `${API_BASE_URL}/api/connectors/${encodeURIComponent(logoName)}`
    : null;

  return (
    <div className="flex-shrink-0 h-10 w-10 bg-white border border-surface-200 rounded-lg flex items-center justify-center overflow-hidden">
      {logoUrl && !logoError ? (
        <img 
          src={logoUrl} 
          alt={`${serverName} connector`}
          className="w-full h-full object-contain p-1"
          onError={() => setLogoError(true)}
        />
      ) : (
        <svg className="w-5 h-5 text-brand-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01" />
        </svg>
      )}
    </div>
  );
};

const ITEMS_PER_PAGE = 10;

const ServerTable = ({ servers, onView, onDelete, onRefresh, onViewTokens }) => {
  const [configModalOpen, setConfigModalOpen] = useState(false);
  const [editModalOpen, setEditModalOpen] = useState(false);
  const [metricsModalOpen, setMetricsModalOpen] = useState(false);
  const [selectedServer, setSelectedServer] = useState(null);
  const [serverToEdit, setServerToEdit] = useState(null);
  const [serverForMetrics, setServerForMetrics] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);

  const totalPages = Math.ceil(servers.length / ITEMS_PER_PAGE);

  useEffect(() => {
    if (currentPage > totalPages && totalPages > 0) {
      setCurrentPage(totalPages);
    }
  }, [servers.length, totalPages, currentPage]);
  const startIndex = (currentPage - 1) * ITEMS_PER_PAGE;
  const paginatedServers = servers.slice(startIndex, startIndex + ITEMS_PER_PAGE);

  const handleViewConfig = (server) => {
    setSelectedServer(server);
    setConfigModalOpen(true);
  };

  const handleCloseConfig = () => {
    setConfigModalOpen(false);
    setSelectedServer(null);
  };

  const handleViewMetrics = (server) => {
    setServerForMetrics(server);
    setMetricsModalOpen(true);
  };

  const handleCloseMetrics = () => {
    setMetricsModalOpen(false);
    setServerForMetrics(null);
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
    <div className="bg-white rounded-lg border border-gray-200">
      <table className="w-full table-fixed divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="w-[28%] px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Server Name
            </th>
            <th className="w-[18%] px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Connector
            </th>
            <th className="w-[14%] px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Updated
            </th>
            <th className="w-[10%] px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Status
            </th>
            <th className="w-[18%] px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Tools
            </th>
            <th className="w-[12%] px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
              Actions
            </th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {paginatedServers.map((server) => (
            <tr key={server.id} className="hover:bg-gray-50">
              <td className="px-4 py-4">
                <div className="flex items-center min-w-0">
                  <ServerIcon logoName={server.connector_logo_name} serverName={server.server_name} />
                  <div className="ml-3 truncate">
                    <div className="text-sm font-medium text-gray-900 truncate">{server.server_name}</div>
                    <div className="text-xs text-gray-500 truncate">ID: {server.id}</div>
                  </div>
                </div>
              </td>
              <td className="px-4 py-4">
                <div className="text-sm text-gray-900 truncate">{server.connector_id}</div>
              </td>
              <td className="px-4 py-4">
                <div className="text-sm text-gray-900">
                  {new Date(server.updated_at).toLocaleDateString()}
                </div>
                <div className="text-xs text-gray-500">
                  {new Date(server.updated_at).toLocaleTimeString()}
                </div>
              </td>
              <td className="px-4 py-4">
                <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                  server.is_active 
                    ? 'bg-green-100 text-green-800' 
                    : 'bg-gray-100 text-gray-800'
                }`}>
                  {server.is_active ? 'Active' : 'Inactive'}
                </span>
              </td>
              <td className="px-4 py-4">
                <div className="text-sm text-gray-900">
                  {(server.static_tools_count || 0) + (server.dynamic_tools_count || 0)}
                </div>
                <div className="text-xs text-gray-500">
                  {server.static_tools_count || 0} static, {server.dynamic_tools_count || 0} dynamic
                </div>
              </td>
              <td className="px-4 py-4 text-right text-sm font-medium">
                <ActionDropdown
                  server={server}
                  actions={{
                    onView: () => onView(server),
                    onConfig: () => handleViewConfig(server),
                    onEdit: () => handleEditServer(server),
                    onTokens: () => onViewTokens && onViewTokens(server),
                    onMetrics: () => handleViewMetrics(server),
                    onDelete: () => onDelete(server),
                  }}
                />
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {totalPages > 1 && (
        <div className="flex items-center justify-between border-t border-gray-200 bg-white px-4 py-3 sm:px-6">
          <div className="text-sm text-gray-700">
            Showing <span className="font-medium">{startIndex + 1}</span> to{' '}
            <span className="font-medium">{Math.min(startIndex + ITEMS_PER_PAGE, servers.length)}</span> of{' '}
            <span className="font-medium">{servers.length}</span> servers
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
              disabled={currentPage === 1}
              className="px-3 py-1 text-sm border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Previous
            </button>
            {Array.from({ length: totalPages }, (_, i) => i + 1).map(page => (
              <button
                key={page}
                onClick={() => setCurrentPage(page)}
                className={`px-3 py-1 text-sm border rounded-md ${
                  currentPage === page
                    ? 'bg-brand-600 text-white border-brand-600'
                    : 'border-gray-300 hover:bg-gray-50'
                }`}
              >
                {page}
              </button>
            ))}
            <button
              onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages}
              className="px-3 py-1 text-sm border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Next
            </button>
          </div>
        </div>
      )}
      
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

      {/* Server Metrics Modal */}
      {metricsModalOpen && serverForMetrics && (
        <ServerMetricsModal
          server={serverForMetrics}
          onClose={handleCloseMetrics}
        />
      )}
    </div>
  );
};

export default ServerTable;

