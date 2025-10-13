import React, { useState } from 'react';
import { useAuth } from '../../../contexts/AuthContext';

const AccessRequestPrompt = () => {
  const { user } = useAuth();
  const [isExpanded, setIsExpanded] = useState(false);

  const handleContactAdmin = () => {
    // In a real application, this could open an email client or contact form
    const subject = encodeURIComponent('Request for Connector Access');
    const body = encodeURIComponent(
      `Hello,\n\nI would like to request access to connectors in the MCP Tools platform.\n\nUser: ${user?.email}\n\nPlease grant me access to the connectors I need to create servers.\n\nThank you!`
    );
    
    // Try to open email client
    window.open(`mailto:admin@example.com?subject=${subject}&body=${body}`);
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-8 text-center">
      <div className="w-20 h-20 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-6">
        <svg className="w-10 h-10 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
        </svg>
      </div>
      
      <h3 className="text-xl font-semibold text-gray-900 mb-3">
        Connector Access Required
      </h3>
      
      <p className="text-gray-600 mb-6 max-w-md mx-auto">
        You don't have access to any connectors yet. Connectors are required to create MCP servers. 
        Please contact your administrator to request access to the connectors you need.
      </p>

      <div className="space-y-4">
        <button
          onClick={handleContactAdmin}
          className="px-6 py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors"
        >
          <svg className="w-5 h-5 inline mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 4.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
          </svg>
          Contact Administrator
        </button>

        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="text-sm text-gray-500 hover:text-gray-700 underline"
        >
          {isExpanded ? 'Hide' : 'Show'} more information
        </button>
      </div>

      {isExpanded && (
        <div className="mt-6 p-4 bg-gray-50 rounded-lg text-left">
          <h4 className="font-medium text-gray-900 mb-3">What are Connectors?</h4>
          <ul className="text-sm text-gray-600 space-y-2">
            <li className="flex items-start">
              <svg className="w-4 h-4 text-green-500 mt-0.5 mr-2 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              Connectors are pre-configured integrations that allow you to connect to external services
            </li>
            <li className="flex items-start">
              <svg className="w-4 h-4 text-green-500 mt-0.5 mr-2 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              They provide tools and templates for creating MCP servers
            </li>
            <li className="flex items-start">
              <svg className="w-4 h-4 text-green-500 mt-0.5 mr-2 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              Only administrators can grant access to specific connectors
            </li>
          </ul>
          
          <div className="mt-4 p-3 bg-blue-50 rounded-lg">
            <div className="flex items-start">
              <svg className="w-5 h-5 text-blue-600 mt-0.5 mr-2 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <div className="text-sm text-blue-800">
                <p className="font-medium mb-1">Need Help?</p>
                <p>Contact your system administrator or IT support team to request access to the connectors you need for your projects.</p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AccessRequestPrompt;
