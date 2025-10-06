import React, { useState } from 'react';
import ToolTemplateModal from './ToolTemplateModal';

const ToolsList = ({ tools, selectedTool, onSelectTool, serverId, onToolUpdate, server }) => {
  const [updatingToolId, setUpdatingToolId] = useState(null);
  const [localTools, setLocalTools] = useState(tools);
  const [showCreateModal, setShowCreateModal] = useState(false);

  // Update local tools when props change
  React.useEffect(() => {
    setLocalTools(tools);
  }, [tools]);

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
      const response = await fetch(`http://localhost:9000/api/servers/${serverId}/tools/${tool.id}`, {
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
      alert(`Failed to update tool status: ${error.message}`);
    } finally {
      setUpdatingToolId(null);
    }
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-lg font-semibold text-gray-900">Available Tools</h2>
        <button
          onClick={handleCreateTool}
          className="px-4 py-2 bg-purple-600 text-white text-sm font-medium rounded-lg hover:bg-purple-700 flex items-center space-x-2"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          <span>Create Tool</span>
        </button>
      </div>
      <div className="space-y-2 max-h-[600px] overflow-y-auto pr-2">
        {localTools.map((tool, index) => (
          <div
            key={index}
            className={`relative p-4 rounded-lg border-2 transition-colors ${
              selectedTool?.name === tool.name
                ? 'border-purple-500 bg-purple-50'
                : 'border-gray-200 hover:border-purple-200 hover:bg-gray-50'
            } ${!tool.is_active ? 'opacity-60' : ''}`}
          >
            {/* Toggle Switch - Absolutely positioned in top right corner */}
            <div className="absolute top-3 right-3 w-11 h-6">
              <button
                onClick={(e) => handleToggleActive(tool, e)}
                disabled={updatingToolId === tool.id}
                className={`w-full h-full inline-flex items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 ${
                  updatingToolId === tool.id
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

            {/* Top row with radio button and tool name */}
            <div className="flex items-center mb-2 pr-16">
              <div className="flex items-center space-x-3">
                <input
                  type="radio"
                  name="tool-selection"
                  checked={selectedTool?.name === tool.name}
                  onChange={() => onSelectTool(tool)}
                  className="w-4 h-4 text-purple-600 focus:ring-purple-500 cursor-pointer"
                />
                <span className={`text-sm font-semibold ${
                  selectedTool?.name === tool.name ? 'text-purple-900' : 'text-gray-900'
                }`}>
                  {tool.name}
                </span>
                {!tool.is_active && (
                  <span className="px-2 py-0.5 bg-gray-200 text-gray-600 text-xs rounded-full">
                    Inactive
                  </span>
                )}
              </div>
            </div>
            
            {/* Tool description below */}
            {tool.description && (
              <p className={`text-xs ${
                selectedTool?.name === tool.name ? 'text-purple-700' : 'text-gray-600'
              } line-clamp-2`}>
                {tool.description}
              </p>
            )}
          </div>
        ))}
      </div>

      {/* Create Tool Modal */}
      <ToolTemplateModal
        isOpen={showCreateModal}
        onClose={handleCloseModal}
        onSuccess={handleToolCreated}
        server={server}
      />
    </div>
  );
};

export default ToolsList;

