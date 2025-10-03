import React from 'react';

const ConnectorCard = ({ connector, onConfigure }) => {
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6 hover:shadow-lg transition-shadow">
      <div className="flex items-start justify-between mb-4">
        <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-blue-500 rounded-lg flex items-center justify-center">
          <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" />
          </svg>
        </div>
        <span className={`px-2 py-1 text-xs font-medium rounded-full ${
          connector.status === 'Active' 
            ? 'bg-green-100 text-green-700' 
            : 'bg-gray-100 text-gray-700'
        }`}>
          {connector.status}
        </span>
      </div>
      
      <h3 className="text-lg font-semibold text-gray-900 mb-2">{connector.name}</h3>
      <p className="text-sm text-gray-600 mb-4">{connector.description}</p>
      
      <div className="space-y-2 mb-4 text-xs text-gray-500">
        <div className="flex items-center justify-between">
          <span>Version:</span>
          <span className="font-medium text-gray-700">{connector.version}</span>
        </div>
        <div className="flex items-center justify-between">
          <span>Author:</span>
          <span className="font-medium text-gray-700">{connector.author}</span>
        </div>
      </div>
      
      <div className="flex items-center space-x-2 pt-4 border-t border-gray-100">
        <button 
          onClick={() => onConfigure(connector)}
          className="flex-1 px-3 py-2 bg-purple-600 text-white text-sm font-medium rounded-lg hover:bg-purple-700"
        >
          Create Server
        </button>
        <button className="px-3 py-2 border border-gray-300 text-gray-700 text-sm font-medium rounded-lg hover:bg-gray-50">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z" />
          </svg>
        </button>
      </div>
    </div>
  );
};

export default ConnectorCard;

