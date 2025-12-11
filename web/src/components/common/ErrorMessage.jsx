import React from 'react';

const ErrorMessage = ({ title = 'Error', message, actionButton }) => {
  return (
    <div className="bg-error-50 border border-error-100 rounded-lg p-6 animate-fade-in">
      <div className="flex items-start space-x-4">
        <div className="flex-shrink-0">
          <svg className="w-6 h-6 text-error-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        </div>
        <div className="flex-1">
          <h3 className="text-sm font-semibold text-error-900">{title}</h3>
          <p className="mt-1 text-sm text-error-700 leading-relaxed">{message}</p>
          {actionButton && (
            <div className="mt-4">
              {actionButton}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ErrorMessage;
