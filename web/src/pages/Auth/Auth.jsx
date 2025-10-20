import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import LoginForm from './components/LoginForm';
import SignupForm from './components/SignupForm';
import { formatError, extractFieldErrors, mapApiFieldToFormField } from '../../utils/errorUtils';
import { api } from '../../services/api';
import { useAuth } from '../../contexts/AuthContext';

const Auth = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { login: authLogin } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [fieldErrors, setFieldErrors] = useState({});
  const [isLogin, setIsLogin] = useState(true);

  // Update form type based on URL
  useEffect(() => {
    const path = location.pathname;
    setIsLogin(path === '/auth/login');
  }, [location.pathname]);

  const handleLogin = async (formData) => {
    setLoading(true);
    setError(null);
    setFieldErrors({});

    try {
      console.log('🔐 Attempting login with:', {
        username: formData.email,
        password: '***'
      });

      // Use AuthContext's login function
      const result = await authLogin(formData);
      console.log('📡 Login result:', result);

      if (result.success) {
        // Login successful - AuthContext has updated the auth state
        console.log('✅ Login successful - redirecting to dashboard');
        navigate('/dashboard', { replace: true });
      } else {
        // Login failed - show error
        console.log('❌ Login failed:', result.error);
        setError(result.error || 'Login failed');
      }
    } catch (error) {
      console.error('❌ Login error:', error);
      setError(error.message || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  const handleSignup = async (formData) => {
    setLoading(true);
    setError(null);
    setFieldErrors({});

    try {
      const response = await api.register(formData);

      if (response.ok) {
        // Registration successful, show success message and redirect to login
        setError(null);
        setFieldErrors({});
        alert('Account created successfully! Please sign in.');
        navigate('/auth/login');
      } else {
        const errorData = await response.json();
        
        // Extract field-specific errors
        const apiFieldErrors = extractFieldErrors(errorData);
        const mappedFieldErrors = {};
        
        // Map API field names to form field names
        Object.keys(apiFieldErrors).forEach(apiField => {
          const formField = mapApiFieldToFormField(apiField);
          mappedFieldErrors[formField] = apiFieldErrors[apiField];
        });
        
        setFieldErrors(mappedFieldErrors);
        
        // Set general error if no field-specific errors
        if (Object.keys(mappedFieldErrors).length === 0) {
          setError(formatError(errorData.detail) || 'Registration failed');
        }
      }
    } catch (error) {
      setError('Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-blue-50 to-indigo-100 relative overflow-hidden">
      {/* Background decoration */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-purple-300 rounded-full mix-blend-multiply filter blur-xl opacity-30 animate-blob"></div>
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-blue-300 rounded-full mix-blend-multiply filter blur-xl opacity-30 animate-blob animation-delay-2000"></div>
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-80 h-80 bg-indigo-300 rounded-full mix-blend-multiply filter blur-xl opacity-30 animate-blob animation-delay-4000"></div>
      </div>

      {/* Main container - Full screen */}
      <div className="relative h-screen">
        <div className="h-full bg-white shadow-2xl">
          <div className="flex flex-col lg:flex-row h-full">
            {/* Left side - Branding */}
            <div className="lg:w-1/2 bg-gradient-to-br from-purple-600 via-purple-700 to-indigo-800 p-12 lg:p-16 flex flex-col justify-center relative overflow-hidden">
              {/* Decorative elements */}
              <div className="absolute top-0 right-0 w-64 h-64 bg-white opacity-5 rounded-full -mr-32 -mt-32"></div>
              <div className="absolute bottom-0 left-0 w-96 h-96 bg-white opacity-5 rounded-full -ml-48 -mb-48"></div>
              
              <div className="relative z-10">
                {/* Logo/Brand */}
                <div className="mb-8">
                  <div className="flex items-center space-x-3 mb-4">
                    <div className="w-16 h-16 bg-white rounded-2xl flex items-center justify-center shadow-lg">
                      <svg className="w-10 h-10 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                      </svg>
                    </div>
                    <h1 className="text-4xl font-bold text-white">SuperMCP</h1>
                  </div>
                  <p className="text-purple-100 text-lg">
                    Model Context Protocol Management Platform
                  </p>
                </div>

                {/* Features */}
                <div className="space-y-4 mt-12">
                  <div className="flex items-start space-x-3">
                    <div className="w-10 h-10 bg-purple-500 bg-opacity-30 rounded-xl flex items-center justify-center flex-shrink-0">
                      <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01" />
                      </svg>
                    </div>
                    <div>
                      <h3 className="text-white font-semibold">Multi-Server Management</h3>
                      <p className="text-purple-200 text-sm">Create and manage multiple MCP servers using existing connectors</p>
                    </div>
                  </div>
                  
                  <div className="flex items-start space-x-3">
                    <div className="w-10 h-10 bg-purple-500 bg-opacity-30 rounded-xl flex items-center justify-center flex-shrink-0">
                      <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                      </svg>
                    </div>
                    <div>
                      <h3 className="text-white font-semibold">JWT Authentication</h3>
                      <p className="text-purple-200 text-sm">Enterprise-grade security with JWT-protected MCP servers</p>
                    </div>
                  </div>
                  
                  <div className="flex items-start space-x-3">
                    <div className="w-10 h-10 bg-purple-500 bg-opacity-30 rounded-xl flex items-center justify-center flex-shrink-0">
                      <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" />
                      </svg>
                    </div>
                    <div>
                      <h3 className="text-white font-semibold">Flexible Control</h3>
                      <p className="text-purple-200 text-sm">Enable/disable servers and tools on-demand via platform</p>
                    </div>
                  </div>
                  
                  <div className="flex items-start space-x-3">
                    <div className="w-10 h-10 bg-purple-500 bg-opacity-30 rounded-xl flex items-center justify-center flex-shrink-0">
                      <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 4a2 2 0 114 0v1a1 1 0 001 1h3a1 1 0 011 1v3a1 1 0 01-1 1h-1a2 2 0 100 4h1a1 1 0 011 1v3a1 1 0 01-1 1h-3a1 1 0 01-1-1v-1a2 2 0 10-4 0v1a1 1 0 01-1 1H7a1 1 0 01-1-1v-3a1 1 0 00-1-1H4a2 2 0 110-4h1a1 1 0 001-1V7a1 1 0 011-1h3a1 1 0 001-1V4z" />
                      </svg>
                    </div>
                    <div>
                      <h3 className="text-white font-semibold">Custom Tool Builder</h3>
                      <p className="text-purple-200 text-sm">Create custom tools based on connector specifications</p>
                    </div>
                  </div>
                  
                  <div className="flex items-start space-x-3">
                    <div className="w-10 h-10 bg-purple-500 bg-opacity-30 rounded-xl flex items-center justify-center flex-shrink-0">
                      <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                      </svg>
                    </div>
                    <div>
                      <h3 className="text-white font-semibold">OpenTelemetry Integration</h3>
                      <p className="text-purple-200 text-sm">Complete observability with OpenTelemetry for all servers</p>
                    </div>
                  </div>
                </div>

                {/* Stats */}
                <div className="grid grid-cols-3 gap-4 mt-10 pt-8 border-t border-purple-400 border-opacity-30">
                  <div className="text-center">
                    <div className="text-3xl font-bold text-white mb-1">∞</div>
                    <div className="text-purple-200 text-xs">MCP Servers</div>
                  </div>
                  <div className="text-center">
                    <div className="text-3xl font-bold text-white mb-1">100%</div>
                    <div className="text-purple-200 text-xs">Secure</div>
                  </div>
                  <div className="text-center">
                    <div className="text-3xl font-bold text-white mb-1">24/7</div>
                    <div className="text-purple-200 text-xs">Monitored</div>
                  </div>
                </div>
              </div>
            </div>

            {/* Right side - Form */}
            <div className="lg:w-1/2 p-8 lg:p-16 flex items-center justify-center overflow-y-auto">
              <div className="w-full max-w-md">
                {/* Tab switcher */}
                <div className="flex bg-gray-100 rounded-xl p-1 mb-8">
                  <button
                    onClick={() => navigate('/auth/login')}
                    className={`flex-1 py-3 px-6 rounded-lg font-semibold transition-all duration-200 ${
                      isLogin
                        ? 'bg-white text-purple-600 shadow-md'
                        : 'text-gray-600 hover:text-gray-900'
                    }`}
                  >
                    Sign In
                  </button>
                  <button
                    onClick={() => navigate('/auth/signup')}
                    className={`flex-1 py-3 px-6 rounded-lg font-semibold transition-all duration-200 ${
                      !isLogin
                        ? 'bg-white text-purple-600 shadow-md'
                        : 'text-gray-600 hover:text-gray-900'
                    }`}
                  >
                    Sign Up
                  </button>
                </div>

                {/* Form content */}
                {isLogin ? (
                  <LoginForm 
                    onLogin={handleLogin} 
                    loading={loading} 
                    error={error}
                    fieldErrors={fieldErrors}
                    onClearError={() => {
                      setError(null);
                      setFieldErrors({});
                    }}
                  />
                ) : (
                  <SignupForm 
                    onSignup={handleSignup} 
                    loading={loading} 
                    error={error}
                    fieldErrors={fieldErrors}
                    onClearError={() => {
                      setError(null);
                      setFieldErrors({});
                    }}
                  />
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Footer - Fixed at bottom */}
      <div className="fixed bottom-0 left-0 right-0 bg-white bg-opacity-90 backdrop-blur-sm border-t border-gray-200 py-4">
        <div className="text-center text-gray-600">
          <p className="text-sm">
            © 2025 SuperMCP. All rights reserved. 
            <span className="mx-2">•</span>
            <button className="text-purple-600 hover:text-purple-700 font-medium">Privacy Policy</button>
            <span className="mx-2">•</span>
            <button className="text-purple-600 hover:text-purple-700 font-medium">Terms of Service</button>
          </p>
        </div>
      </div>

      {/* Custom animations */}
      <style jsx>{`
        @keyframes blob {
          0%, 100% { transform: translate(0, 0) scale(1); }
          33% { transform: translate(30px, -50px) scale(1.1); }
          66% { transform: translate(-20px, 20px) scale(0.9); }
        }
        .animate-blob {
          animation: blob 7s infinite;
        }
        .animation-delay-2000 {
          animation-delay: 2s;
        }
        .animation-delay-4000 {
          animation-delay: 4s;
        }
      `}</style>
    </div>
  );
};

export default Auth;
