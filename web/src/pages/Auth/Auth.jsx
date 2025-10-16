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
    <div>
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
  );
};

export default Auth;
