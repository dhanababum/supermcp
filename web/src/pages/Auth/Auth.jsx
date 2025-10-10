import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import LoginForm from './components/LoginForm';
import SignupForm from './components/SignupForm';
import { formatError, extractFieldErrors, mapApiFieldToFormField } from '../../utils/errorUtils';

const Auth = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [fieldErrors, setFieldErrors] = useState({});
  const [isLogin, setIsLogin] = useState(true);

  // Check if user is already authenticated
  useEffect(() => {
    const checkAuthStatus = async () => {
      try {
        const response = await fetch('http://localhost:9000/users/me', {
          credentials: 'include', // Include cookies
        });
        
        if (response.ok) {
          // User is already authenticated, redirect to dashboard
          navigate('/dashboard');
        }
      } catch (error) {
        // User is not authenticated, stay on auth page
        console.log('User not authenticated');
      }
    };
    
    checkAuthStatus();
  }, [navigate]);

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
      // Create URLSearchParams for application/x-www-form-urlencoded format
      // This matches the cURL command format
      const formBody = new URLSearchParams();
      formBody.append('username', formData.email);
      formBody.append('password', formData.password);

      // Debug: Log what we're sending
      console.log('Sending form-encoded login request with:', {
        username: formData.email,
        password: '***' // Don't log actual password
      });

      const response = await fetch('http://localhost:9000/auth/cookie/login', {
        method: 'POST',
        headers: {
          'accept': 'application/json',
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        credentials: 'include', // Include cookies for CookieTransport
        body: formBody.toString(),
      });

      console.log('Login response status:', response.status);

      if (response.ok) {
        // Login successful
        // Note: fastapi-users cookie login returns 204 No Content (no body)
        console.log('Login successful - cookie set');
        
        // Notify useAuth hook to refresh authentication status
        // window.dispatchEvent(new Event('auth:refresh'));
        
        // Wait a moment for the auth state to update before navigating
         navigate('/dashboard', { replace: true });
      } else {
        // Only try to parse JSON on error responses
        const contentType = response.headers.get('content-type');
        let errorData = { detail: 'Login failed' };
        
        if (contentType && contentType.includes('application/json')) {
          try {
            errorData = await response.json();
          } catch (e) {
            console.error('Failed to parse error response:', e);
          }
        }
        
        console.log('Login error response:', errorData);
        
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
          setError(formatError(errorData.detail) || 'Login failed');
        }
      }
    } catch (error) {
      console.error('Login network error:', error);
      setError('Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleSignup = async (formData) => {
    setLoading(true);
    setError(null);
    setFieldErrors({});

    try {
      const response = await fetch('http://localhost:9000/auth/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include', // Include cookies
        body: JSON.stringify(formData),
      });

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
