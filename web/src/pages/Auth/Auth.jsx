import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import LoginForm from './components/LoginForm';
import SignupForm from './components/SignupForm';
import { formatError, extractFieldErrors, mapApiFieldToFormField } from '../../utils/errorUtils';
import { api } from '../../services/api';
import { useAuth } from '../../contexts/AuthContext';
import { SuperMCPIcon } from '../../components/icons';

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
      // Use AuthContext's login function
      const result = await authLogin(formData);

      if (result.success) {
        // Login successful - AuthContext has updated the auth state
        navigate('/dashboard', { replace: true });
      } else {
        // Login failed - show error
        setError(result.error || 'Login failed');
      }
    } catch (error) {
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
    <div className="min-h-screen bg-surface-50 flex">
      {/* Left side - Branding & Content */}
      <div className="hidden lg:flex w-1/2 bg-brand-900 relative flex-col justify-between p-12 overflow-hidden">
        {/* Subtle Background Pattern */}
        <div className="absolute inset-0 opacity-10">
          <svg className="h-full w-full" viewBox="0 0 100 100" preserveAspectRatio="none">
            <path d="M0 100 C 20 0 50 0 100 100 Z" fill="white" />
          </svg>
        </div>

        <div className="relative z-10">
          <div className="flex items-center space-x-3 mb-12">
            <div className="w-10 h-10 bg-white/10 rounded-lg flex items-center justify-center backdrop-blur-sm border border-white/20">
              <SuperMCPIcon className="w-6 h-6 text-white" />
            </div>
            <span className="text-xl font-bold text-white tracking-tight">SuperMCP</span>
          </div>

          <div className="max-w-md">
            <h1 className="text-4xl font-bold text-white mb-6 leading-tight">
              Manage your MCP servers with confidence
            </h1>
            <p className="text-brand-100 text-lg mb-8 leading-relaxed">
              Enterprise-grade management platform for the Model Context Protocol. Secure, scalable, and built for developers.
            </p>

            <div className="space-y-6">
              {[
                { title: 'Multi-Server Management', desc: 'Centralized control plane for all your MCP instances' },
                { title: 'JWT Authentication', desc: 'Secure access with industry-standard protocols' },
                { title: 'Real-time Observability', desc: 'Built-in OpenTelemetry integration' }
              ].map((item, i) => (
                <div key={i} className="flex items-start space-x-4">
                  <div className="w-6 h-6 rounded-full bg-brand-500/20 flex items-center justify-center flex-shrink-0 mt-1">
                    <svg className="w-3.5 h-3.5 text-brand-200" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                  <div>
                    <h3 className="text-white font-medium">{item.title}</h3>
                    <p className="text-brand-200/80 text-sm mt-0.5">{item.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="relative z-10 text-brand-200/60 text-sm">
          © 2025 SuperMCP Inc.
        </div>
      </div>

      {/* Right side - Auth Form */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-8 bg-white">
        <div className="w-full max-w-md space-y-8">
          {/* Mobile Logo */}
          <div className="lg:hidden flex justify-center mb-8">
             <div className="flex items-center space-x-2">
                <div className="w-10 h-10 bg-brand-600 rounded-lg flex items-center justify-center">
                  <SuperMCPIcon className="w-6 h-6 text-white" />
                </div>
                <span className="text-xl font-bold text-surface-900">SuperMCP</span>
             </div>
          </div>

          <div className="text-center">
            <h2 className="text-2xl font-bold text-surface-900">
              {isLogin ? 'Welcome back' : 'Create an account'}
            </h2>
            <p className="mt-2 text-sm text-surface-500">
              {isLogin ? 'Sign in to access your dashboard' : 'Get started with your 14-day free trial'}
            </p>
          </div>

          <div className="mt-8">
            {/* Tab Switcher */}
            <div className="flex p-1 bg-surface-100 rounded-lg mb-8">
              <button
                onClick={() => navigate('/auth/login')}
                className={`flex-1 py-2.5 text-sm font-medium rounded-md transition-all duration-200 ${
                  isLogin
                    ? 'bg-white text-brand-600 shadow-sm'
                    : 'text-surface-500 hover:text-surface-700'
                }`}
              >
                Sign In
              </button>
              <button
                onClick={() => navigate('/auth/signup')}
                className={`flex-1 py-2.5 text-sm font-medium rounded-md transition-all duration-200 ${
                  !isLogin
                    ? 'bg-white text-brand-600 shadow-sm'
                    : 'text-surface-500 hover:text-surface-700'
                }`}
              >
                Sign Up
              </button>
            </div>

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
  );
};

export default Auth;
