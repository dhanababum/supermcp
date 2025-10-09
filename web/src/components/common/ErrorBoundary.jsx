import React from 'react';
import { ErrorMessage } from './index';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    // Update state so the next render will show the fallback UI
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    // Log error details
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    
    this.setState({
      error: error,
      errorInfo: errorInfo
    });

    // Check if it's an authentication error
    if (error.message && error.message.includes('401')) {
      // Redirect to login for auth errors
      setTimeout(() => {
        window.location.href = '/auth/login';
      }, 2000);
    }
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
  };

  render() {
    if (this.state.hasError) {
      // Check if it's an authentication error
      const isAuthError = this.state.error?.message?.includes('401') || 
                         this.state.error?.message?.includes('Unauthorized');

      return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50">
          <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-6">
            <ErrorMessage
              title={isAuthError ? "Authentication Required" : "Something went wrong"}
              message={
                isAuthError 
                  ? "Your session has expired. You will be redirected to the login page."
                  : "An unexpected error occurred. Please try again or contact support if the problem persists."
              }
              actionButton={
                <div className="flex space-x-3">
                  {!isAuthError && (
                    <button
                      onClick={this.handleRetry}
                      className="px-4 py-2 bg-purple-600 text-white text-sm font-medium rounded-lg hover:bg-purple-700"
                    >
                      Try Again
                    </button>
                  )}
                  <button
                    onClick={() => window.location.reload()}
                    className="px-4 py-2 border border-gray-300 text-gray-700 text-sm font-medium rounded-lg hover:bg-gray-50"
                  >
                    Reload Page
                  </button>
                </div>
              }
            />
            
            {process.env.NODE_ENV === 'development' && this.state.error && (
              <details className="mt-4 p-4 bg-gray-100 rounded-lg">
                <summary className="cursor-pointer text-sm font-medium text-gray-700">
                  Error Details (Development)
                </summary>
                <pre className="mt-2 text-xs text-gray-600 overflow-auto">
                  {this.state.error && this.state.error.toString()}
                  {this.state.errorInfo.componentStack}
                </pre>
              </details>
            )}
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
