import React from 'react';

const ToolsList = ({ tools, selectedTool, onSelectTool }) => {
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Available Tools</h2>
      <div className="space-y-2 max-h-[600px] overflow-y-auto pr-2">
        {tools.map((tool, index) => (
          <label
            key={index}
            className={`flex items-start space-x-3 p-4 rounded-lg border-2 cursor-pointer transition-colors ${
              selectedTool?.name === tool.name
                ? 'border-purple-500 bg-purple-50'
                : 'border-gray-200 hover:border-purple-200 hover:bg-gray-50'
            }`}
          >
            <input
              type="radio"
              name="tool-selection"
              checked={selectedTool?.name === tool.name}
              onChange={() => onSelectTool(tool)}
              className="mt-1 w-4 h-4 text-purple-600 focus:ring-purple-500"
            />
            <div className="flex-1 min-w-0">
              <div className="flex items-center space-x-2 mb-1">
                <span className={`text-sm font-semibold ${
                  selectedTool?.name === tool.name ? 'text-purple-900' : 'text-gray-900'
                }`}>
                  {tool.name}
                </span>
              </div>
              {tool.description && (
                <p className={`text-xs ${
                  selectedTool?.name === tool.name ? 'text-purple-700' : 'text-gray-600'
                } line-clamp-2`}>
                  {tool.description}
                </p>
              )}
            </div>
          </label>
        ))}
      </div>
    </div>
  );
};

export default ToolsList;

