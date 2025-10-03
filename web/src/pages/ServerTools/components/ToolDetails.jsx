import React, { useState, useEffect } from 'react';

const ToolDetails = ({ tool }) => {
  const [showJsonView, setShowJsonView] = useState(false);
  const [toolInputs, setToolInputs] = useState({});

  useEffect(() => {
    if (tool && tool.inputSchema && tool.inputSchema.properties) {
      const initialInputs = {};
      Object.entries(tool.inputSchema.properties).forEach(([paramName, paramSchema]) => {
        if (paramSchema.default !== undefined) {
          initialInputs[paramName] = paramSchema.default;
        }
      });
      setToolInputs(initialInputs);
    } else {
      setToolInputs({});
    }
  }, [tool]);

  const handleExecute = () => {
    console.log('Tool Inputs:', toolInputs);
    alert('Tool execution not yet implemented\n\nInputs: ' + JSON.stringify(toolInputs, null, 2));
  };

  if (!tool) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="text-center py-12 text-gray-500">
          <p>Select a tool to view its configuration</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-900">
          {showJsonView ? 'Tool Configuration (JSON)' : 'Tool Parameters'}
        </h2>
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setShowJsonView(!showJsonView)}
            className="text-sm text-gray-600 hover:text-gray-700 font-medium flex items-center space-x-1 px-3 py-1 border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
            <span>{showJsonView ? 'Show Form' : 'Show JSON'}</span>
          </button>
          {showJsonView && (
            <button
              onClick={() => {
                navigator.clipboard.writeText(JSON.stringify(tool, null, 2));
              }}
              className="text-sm text-purple-600 hover:text-purple-700 font-medium flex items-center space-x-1"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
              </svg>
              <span>Copy JSON</span>
            </button>
          )}
        </div>
      </div>
      
      {showJsonView ? (
        <div className="bg-gray-900 rounded-lg p-4 overflow-x-auto">
          <pre className="text-xs text-gray-100 font-mono">
            {JSON.stringify(tool, null, 2)}
          </pre>
        </div>
      ) : (
        <div className="space-y-4">
          {/* Tool Description */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h3 className="text-sm font-semibold text-blue-900 mb-2">
              {tool.name}
            </h3>
            <p className="text-sm text-blue-700">
              {tool.description || 'No description available'}
            </p>
          </div>

          {/* Input Parameters */}
          {tool.inputSchema && tool.inputSchema.properties ? (
            <div className="space-y-4">
              <h4 className="text-sm font-semibold text-gray-900">Parameters</h4>
              {Object.entries(tool.inputSchema.properties).map(([paramName, paramSchema]) => (
                <div key={paramName} className="space-y-2">
                  <label htmlFor={paramName} className="block text-sm font-medium text-gray-700">
                    {paramName}
                    {tool.inputSchema.required && tool.inputSchema.required.includes(paramName) && (
                      <span className="text-red-500 ml-1">*</span>
                    )}
                  </label>
                  
                  {/* Handle different input types */}
                  {paramSchema.type === 'boolean' ? (
                    <select
                      id={paramName}
                      value={toolInputs[paramName] || 'false'}
                      onChange={(e) => setToolInputs({...toolInputs, [paramName]: e.target.value})}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                    >
                      <option value="true">true</option>
                      <option value="false">false</option>
                    </select>
                  ) : paramSchema.type === 'number' || paramSchema.type === 'integer' ? (
                    <input
                      type="number"
                      id={paramName}
                      value={toolInputs[paramName] || paramSchema.default || ''}
                      onChange={(e) => setToolInputs({...toolInputs, [paramName]: e.target.value})}
                      placeholder={paramSchema.default !== undefined ? `Default: ${paramSchema.default}` : `Enter ${paramName}`}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                    />
                  ) : paramSchema.enum ? (
                    <select
                      id={paramName}
                      value={toolInputs[paramName] || paramSchema.default || ''}
                      onChange={(e) => setToolInputs({...toolInputs, [paramName]: e.target.value})}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                    >
                      <option value="">Select {paramName}</option>
                      {paramSchema.enum.map(option => (
                        <option key={option} value={option}>{option}</option>
                      ))}
                    </select>
                  ) : (
                    <input
                      type="text"
                      id={paramName}
                      value={toolInputs[paramName] || paramSchema.default || ''}
                      onChange={(e) => setToolInputs({...toolInputs, [paramName]: e.target.value})}
                      placeholder={paramSchema.default !== undefined ? `Default: ${paramSchema.default}` : `Enter ${paramName}`}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                    />
                  )}
                  
                  {/* Parameter description and metadata */}
                  <div className="space-y-1">
                    {paramSchema.description && (
                      <p className="text-xs text-gray-600">{paramSchema.description}</p>
                    )}
                    <div className="flex flex-wrap gap-2">
                      <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
                        Type: {paramSchema.type || 'string'}
                      </span>
                      {paramSchema.default !== undefined && (
                        <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
                          Default: {JSON.stringify(paramSchema.default)}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              ))}

              {/* Execute Button */}
              <div className="pt-4 border-t border-gray-200">
                <button
                  onClick={handleExecute}
                  className="w-full px-4 py-2 bg-purple-600 text-white text-sm font-medium rounded-lg hover:bg-purple-700"
                >
                  Execute Tool
                </button>
              </div>
            </div>
          ) : (
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 text-center">
              <p className="text-sm text-gray-600">This tool has no input parameters</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default ToolDetails;

