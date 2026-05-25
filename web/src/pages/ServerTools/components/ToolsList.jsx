import React, { useState } from 'react';
import ToolTemplateModal from './ToolTemplateModal';
import ConfirmationModal from '../../../components/ConfirmationModal';
import Notification from '../../../components/common/Notification';
import { API_BASE_URL } from '../../../constants/env';

const ToolsList = ({ tools, selectedTool, onSelectTool, serverId, onToolUpdate, server }) => {
  const [updatingToolId, setUpdatingToolId] = useState(null);
  const [localTools, setLocalTools] = useState(tools);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [toolToDelete, setToolToDelete] = useState(null);
  const [deletingToolId, setDeletingToolId] = useState(null);
  const [notification, setNotification] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');

  // Update local tools when props change
  React.useEffect(() => {
    setLocalTools(tools);
  }, [tools]);

  const filteredTools = localTools.filter(tool =>
    tool.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (tool.description && tool.description.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  const handleToggleAllTools = async (active) => {
    // Filter currently visible tools that need changing
    const toolsToUpdate = filteredTools.filter(t => t.is_active !== active);
    if (toolsToUpdate.length === 0) return;

    setUpdatingToolId('all'); // Visual indicator for bulk action

    // Optimistically update local state
    setLocalTools(prevTools =>
      prevTools.map(t => {
        const shouldUpdate = toolsToUpdate.some(tu => tu.id === t.id);
        return shouldUpdate ? { ...t, is_active: active } : t;
      })
    );

    try {
      // Execute all PATCH calls in parallel
      const updatePromises = toolsToUpdate.map(async (tool) => {
        const response = await fetch(`${API_BASE_URL}/api/servers/${serverId}/tools/${tool.id}`, {
          method: 'PATCH',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            is_active: active
          })
        });
        if (!response.ok) {
          throw new Error(`Failed to update tool "${tool.name}"`);
        }
        return response.json();
      });

      await Promise.all(updatePromises);

      setNotification({
        type: 'success',
        message: `${active ? 'Enabled' : 'Disabled'} ${toolsToUpdate.length} tool${toolsToUpdate.length > 1 ? 's' : ''} successfully`
      });

      if (onToolUpdate) {
        onToolUpdate();
      }
    } catch (error) {
      console.error('Error toggling tools:', error);
      // Revert to original tools on error
      setLocalTools(tools);
      setNotification({
        type: 'error',
        message: `Failed to update some tools: ${error.message}`
      });
    } finally {
      setUpdatingToolId(null);
    }
  };

  const handleCreateTool = () => {
    setShowCreateModal(true);
  };

  const handleCloseModal = () => {
    setShowCreateModal(false);
  };

  const handleToolCreated = () => {
    // Refresh tools list
    if (onToolUpdate) {
      onToolUpdate();
    }
    setShowCreateModal(false);
  };

  const handleDeleteClick = (tool, e) => {
    e.stopPropagation(); // Prevent tool selection when clicking delete
    setToolToDelete(tool);
    setShowDeleteModal(true);
  };

  const handleConfirmDelete = async () => {
    if (!toolToDelete) return;
    
    setDeletingToolId(toolToDelete.id);
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/servers/${serverId}/tools/${toolToDelete.id}`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
        }
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to delete tool');
      }
      
      // Remove tool from local state
      setLocalTools(prevTools => 
        prevTools.filter(t => t.id !== toolToDelete.id)
      );
      
      // Show success notification
      setNotification({
        type: 'success',
        message: `Tool "${toolToDelete.name}" deleted successfully`
      });
      
      // Close modal
      setShowDeleteModal(false);
      setToolToDelete(null);
      
    } catch (error) {
      console.error('Error deleting tool:', error);
      
      // Show error notification
      setNotification({
        type: 'error',
        message: `Failed to delete tool: ${error.message}`
      });
      
      // Close modal on error too
      setShowDeleteModal(false);
      setToolToDelete(null);
    } finally {
      setDeletingToolId(null);
    }
  };

  const handleCancelDelete = () => {
    setShowDeleteModal(false);
    setToolToDelete(null);
  };

  const handleToggleActive = async (tool, e) => {
    e.stopPropagation(); // Prevent tool selection when clicking toggle
    
    setUpdatingToolId(tool.id);
    
    // Optimistically update local state first
    setLocalTools(prevTools => 
      prevTools.map(t => 
        t.id === tool.id ? { ...t, is_active: !t.is_active } : t
      )
    );
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/servers/${serverId}/tools/${tool.id}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          is_active: !tool.is_active
        })
      });

      if (!response.ok) {
        throw new Error('Failed to update tool status');
      }

      const data = await response.json();
      console.log('Tool status updated:', data);
      
      // No need to refetch - local state is already updated
    } catch (error) {
      console.error('Error updating tool status:', error);
      // Revert optimistic update on error
      setLocalTools(prevTools => 
        prevTools.map(t => 
          t.id === tool.id ? { ...t, is_active: tool.is_active } : t
        )
      );
      
      // Show error notification
      setNotification({
        type: 'error',
        message: `Failed to update tool status: ${error.message}`
      });
    } finally {
      setUpdatingToolId(null);
    }
  };

  return (
    <>
      {/* Notification Toast */}
      {notification && (
        <Notification
          message={notification.message}
          type={notification.type}
          duration={4000}
          onClose={() => setNotification(null)}
        />
      )}

      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Available Tools</h2>
          <button
            onClick={handleCreateTool}
            className="px-4 py-2 bg-brand-100 text-brand-700 text-sm font-medium rounded-lg hover:bg-brand-200 border border-brand-300 flex items-center space-x-2 flex-shrink-0"
          >
            <svg className="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            <span>Create Tool</span>
          </button>
        </div>

        {/* Search and Bulk Toggle Actions */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 mb-6">
          <div className="relative flex-1">
            <span className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
              <svg className="h-4 w-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </span>
            <input
              type="text"
              placeholder="Search tools by name or description..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent text-sm"
            />
          </div>
          
          <div className="flex items-center space-x-2 flex-shrink-0">
            <button
              onClick={() => handleToggleAllTools(true)}
              disabled={updatingToolId === 'all' || filteredTools.every(t => t.is_active)}
              className="px-3 py-1.5 bg-green-50 text-green-700 text-xs font-semibold rounded-lg hover:bg-green-100 border border-green-200 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
            >
              {updatingToolId === 'all' ? 'Updating...' : 'Enable All'}
            </button>
            <button
              onClick={() => handleToggleAllTools(false)}
              disabled={updatingToolId === 'all' || filteredTools.every(t => !t.is_active)}
              className="px-3 py-1.5 bg-red-50 text-red-700 text-xs font-semibold rounded-lg hover:bg-red-100 border border-red-200 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
            >
              {updatingToolId === 'all' ? 'Updating...' : 'Disable All'}
            </button>
          </div>
        </div>

        <div className="space-y-2 max-h-[600px] overflow-y-auto pr-2">
          {filteredTools.length === 0 ? (
            <div className="text-center py-12 text-gray-500 text-sm border border-dashed border-gray-200 rounded-lg bg-gray-50">
              No tools found matching "{searchQuery}"
            </div>
          ) : (
            filteredTools.map((tool, index) => (
              <div
                key={index}
                className={`relative p-4 rounded-lg border-2 transition-colors ${
                  selectedTool?.name === tool.name
                    ? 'border-brand-500 bg-brand-50'
                    : 'border-gray-200 hover:border-brand-200 hover:bg-gray-50'
                } ${!tool.is_active ? 'opacity-60' : ''}`}
              >
                {/* Top row with radio button and delete/toggle buttons */}
                <div className="flex items-center justify-between mb-3 gap-4">
                  <div className="flex items-center space-x-3 min-w-0 flex-1">
                    <input
                      type="radio"
                      name="tool-selection"
                      checked={selectedTool?.name === tool.name}
                      onChange={() => onSelectTool(tool)}
                      className="w-4 h-4 text-brand-600 focus:ring-brand-500 cursor-pointer flex-shrink-0"
                    />
                    <span 
                      className={`text-sm font-semibold truncate ${
                        selectedTool?.name === tool.name ? 'text-brand-900' : 'text-gray-900'
                      }`}
                      title={tool.name}
                    >
                      {tool.name}
                    </span>
                  </div>
                  
                  <div className="flex items-center space-x-3 flex-shrink-0">
                    {/* Delete button for dynamic tools only */}
                    {tool.tool_type === 'dynamic' && (
                      <button
                        onClick={(e) => handleDeleteClick(tool, e)}
                        disabled={deletingToolId === tool.id || updatingToolId === 'all'}
                        className="group relative inline-flex items-center justify-center w-8 h-8 bg-red-50 border border-red-200 text-red-600 hover:bg-red-100 hover:border-red-300 hover:text-red-700 rounded-lg transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-1 shadow-sm hover:shadow-md"
                        title="Delete tool"
                      >
                        {deletingToolId === tool.id ? (
                          <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                          </svg>
                        ) : (
                          <svg className="w-4 h-4 group-hover:scale-110 transition-transform duration-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                          </svg>
                        )}
                        {/* Tooltip on hover */}
                        <div className="absolute -top-8 left-1/2 transform -translate-x-1/2 bg-gray-900 text-white text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none whitespace-nowrap z-10">
                          Delete tool
                        </div>
                      </button>
                    )}
                    
                    {/* Toggle Switch */}
                    <div className="w-11 h-6 flex-shrink-0">
                      <button
                        onClick={(e) => handleToggleActive(tool, e)}
                        disabled={updatingToolId === tool.id || updatingToolId === 'all'}
                        className={`w-full h-full inline-flex items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-brand-500 focus:ring-offset-2 ${
                          updatingToolId === tool.id || updatingToolId === 'all'
                            ? 'opacity-50 cursor-not-allowed'
                            : 'cursor-pointer'
                        } ${
                          tool.is_active ? 'bg-green-600' : 'bg-gray-300'
                        }`}
                        title={tool.is_active ? 'Click to deactivate' : 'Click to activate'}
                      >
                        <span
                          className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                            tool.is_active ? 'translate-x-6' : 'translate-x-1'
                          }`}
                        />
                      </button>
                    </div>
                  </div>
                </div>

                {/* Tool type and status badges */}
                <div className="flex items-center space-x-2 mb-2 flex-wrap gap-y-1">
                  <span className={`px-2 py-0.5 text-xs rounded-full font-medium flex-shrink-0 ${
                    tool.tool_type === 'dynamic' 
                      ? 'bg-blue-100 text-blue-700' 
                      : 'bg-green-100 text-green-700'
                  }`}>
                    {tool.tool_type}
                  </span>
                  {!tool.is_active && (
                    <span className="px-2 py-0.5 bg-gray-200 text-gray-600 text-xs rounded-full flex-shrink-0">
                      Inactive
                    </span>
                  )}
                </div>
                
                {/* Tool description below */}
                {tool.description && (
                  <p className={`text-xs ${
                    selectedTool?.name === tool.name ? 'text-brand-700' : 'text-gray-600'
                  } line-clamp-2`}>
                    {tool.description}
                  </p>
                )}
              </div>
            ))
          )}
        </div>

      {/* Create Tool Modal */}
      <ToolTemplateModal
        isOpen={showCreateModal}
        onClose={handleCloseModal}
        onSuccess={handleToolCreated}
        server={server}
      />

      {/* Delete Confirmation Modal */}
      <ConfirmationModal
        isOpen={showDeleteModal}
        onClose={handleCancelDelete}
        onConfirm={handleConfirmDelete}
        title="Permanently Delete Tool"
        message={`Are you sure you want to permanently delete the tool "${toolToDelete?.name}"? This action cannot be undone and the tool will be completely removed from the database.`}
        confirmText={deletingToolId ? "Deleting..." : "Delete"}
        cancelText="Cancel"
        isDestructive={true}
      />
      </div>
    </>
  );
};

export default ToolsList;

