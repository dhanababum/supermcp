import React, { useState, useEffect } from 'react';
import { useServerTools } from '../../hooks';
import { LoadingSpinner, ErrorMessage } from '../../components/common';
import { ToolsList, ToolDetails } from './components';

const ServerTools = ({ server, onBack }) => {
  const { tools, loading, error, refetch } = useServerTools(server?.id, !!server);
  const [selectedTool, setSelectedTool] = useState(null);

  useEffect(() => {
    if (tools.length > 0 && !selectedTool) {
      setSelectedTool(tools[0]);
    }
  }, [tools, selectedTool]);

  const handleToolUpdate = () => {
    refetch();
  };

  if (!server) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-600">No server selected</p>
      </div>
    );
  }

  return (
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
          {server.server_name} - Tools
        </h1>
        <p className="text-gray-600">
          Available tools for {server.connector_id}
        </p>
      </div>

      {loading ? (
        <LoadingSpinner message="Loading tools..." />
      ) : error ? (
        <ErrorMessage
          title="Error loading tools"
          message={error}
          actionButton={
            <button
              onClick={() => window.location.reload()}
              className="px-4 py-2 bg-red-600 text-white text-sm font-medium rounded-lg hover:bg-red-700"
            >
              Retry
            </button>
          }
        />
      ) : tools.length > 0 ? (
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
          {/* Left Column - Tools List */}
          <div className="lg:col-span-2">
            <ToolsList
              tools={tools}
              selectedTool={selectedTool}
              onSelectTool={setSelectedTool}
              serverId={server.id}
              onToolUpdate={handleToolUpdate}
              server={server}
            />
          </div>

          {/* Right Column - Tool Details */}
          <div className="lg:col-span-3">
            <ToolDetails tool={selectedTool} />
          </div>
        </div>
      ) : (
        <div className="bg-white rounded-lg border-2 border-dashed border-gray-300 p-12 text-center">
          <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">No tools available</h3>
          <p className="text-gray-600">This server has no tools configured</p>
        </div>
      )}
    </div>
  );
};

export default ServerTools;

