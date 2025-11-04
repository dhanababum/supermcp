import React, { createContext, useContext, useState, useCallback, useRef, useEffect } from 'react';
import { api } from '../services/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(null); // null = unknown, true/false = known
  const [isLoading, setIsLoading] = useState(true);
  const [user, setUser] = useState(null);

  // Guards
  const isCheckingRef = useRef(false);
  const isMountedRef = useRef(true);

  useEffect(() => {
    // track mounted state to avoid setting state after unmount
    isMountedRef.current = true;
    return () => { isMountedRef.current = false; };
  }, []);

  const checkAuthStatus = useCallback(async () => {
    
    // Prevent multiple simultaneous auth checks
    if (isCheckingRef.current) {
      return;
    }

    isCheckingRef.current = true;
    setIsLoading(true);

    try {
      const result = await api.getMe();
      
      if (result) {
        setIsAuthenticated(true);
        setUser(result);
      } else {
        setIsAuthenticated(false);
        setUser(null);
      }
    } catch (err) {
      setIsAuthenticated(false);
      setUser(null);
    } finally {
      isCheckingRef.current = false;
      setIsLoading(false);
    }
  }, []);

  // Check auth on mount
  useEffect(() => {
    checkAuthStatus();
  }, [checkAuthStatus]);

  const login = useCallback(async (credentials) => {
    try {
      setIsLoading(true);

      const response = await api.login(credentials);

      // Check if login was successful
      if (response && response.ok) {
        // Wait for auth status to refresh
        await checkAuthStatus();
        return { success: true };
      }

      // If response doesn't have 'ok' property, assume success and check auth
      if (!('ok' in response)) {
        await checkAuthStatus();
        return { success: true };
      }

      // Login failed
      return { success: false, error: 'Login failed' };
    } catch (error) {
      return { success: false, error: error?.message ?? 'Network error' };
    } finally {
      setIsLoading(false);
    }
  }, [checkAuthStatus]);

  const logout = useCallback(async () => {
    try {
      setIsLoading(true);
      await api.logout();
    } catch (err) {
    } finally {
      setIsAuthenticated(false);
      setUser(null);
      setIsLoading(false);
    }
  }, []);

  // Listen for external auth refresh events
  useEffect(() => {
    const handleAuthRefresh = async () => {
      await checkAuthStatus();
    };

    window.addEventListener('auth:refresh', handleAuthRefresh);
    return () => window.removeEventListener('auth:refresh', handleAuthRefresh);
  }, [checkAuthStatus]);

  // Role-based helper functions
  const isSuperuser = useCallback(() => {
    return user?.is_superuser === true;
  }, [user]);

  const hasRole = useCallback((role) => {
    if (role === 'superuser') return isSuperuser();
    return false;
  }, [isSuperuser]);


  const value = {
    isAuthenticated,
    isLoading,
    user,
    login,
    logout,
    checkAuthStatus,
    isSuperuser,
    hasRole,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within an AuthProvider');
  return context;
};