import React from 'react';

const LoadingSpinner = ({ message = 'Loading...' }) => {
  return (
    <div className="flex items-center justify-center h-64">
      <div className="text-center">
        <div className="inline-block animate-spin rounded-full h-10 w-10 border-4 border-surface-200 border-t-brand-600"></div>
        <p className="mt-4 text-sm font-medium text-surface-500 animate-pulse">{message}</p>
      </div>
    </div>
  );
};

export default LoadingSpinner;
