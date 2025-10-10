import { useState, useEffect, useCallback, useRef } from 'react';
import { api } from '../services/api';
import { authCookies } from '../services/cookies';

export const useAuth = () => {
  const [isAuthenticated, setIsAuthenticated] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [user, setUser] = useState(null);
  const isCheckingRef = useRef(false); // Prevent multiple simultaneous checks

  const login = useCallback(async (credentials) => {
    try {
      setIsLoading(true);
      
      const response = await fetch('http://localhost:9000/auth/login', {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(credentials),
      });

      if (response.ok) {
        // await checkAuthStatus();
        return { success: true };
      } else {
        const error = await response.json();
        return { success: false, error: error.detail || 'Login failed' };
      }
    } catch (error) {
      console.error('Login error:', error);
      return { success: false, error: 'Network error' };
    } finally {
      setIsLoading(false);
    }
  }, []);

  const logout = useCallback(async () => {
    try {
      setIsLoading(true);
      
      // Call logout endpoint
      await api.logout();
    } catch (error) {
      console.warn('Logout API call failed:', error);
    } finally {
      // Clear local state and cookies regardless of API call result
      setIsAuthenticated(false);
      setUser(null);
      authCookies.clearAuth();
      setIsLoading(false);
    }
  }, []);

 
  return {
    isAuthenticated,
    isLoading,
    user,
    login,
    logout,
    // checkAuthStatus,
  };
};
