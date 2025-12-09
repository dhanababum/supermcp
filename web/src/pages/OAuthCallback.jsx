import React, { useEffect } from 'react';
import { onMcpAuthorization } from 'use-mcp';

const OAuthCallback = () => {
  useEffect(() => {
    onMcpAuthorization();
  }, []);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full bg-white rounded-lg shadow-md p-6">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-brand-600 mx-auto mb-4"></div>
          <h1 className="text-xl font-semibold text-gray-900 mb-2">Authenticating...</h1>
          <p className="text-gray-600">This window should close automatically.</p>
        </div>
      </div>
    </div>
  );
};

export default OAuthCallback;
