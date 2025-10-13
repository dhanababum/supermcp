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
      console.log('Auth check already in progress, skipping...');
      return;
    }

    isCheckingRef.current = true;
    if (isMountedRef.current) setIsLoading(true);

    try {
      try {
        const result = await api.getMe();
        if (!result) {
          setIsAuthenticated(false);
          setUser(null);
          setIsLoading(false);
          return;
        } else {
          setIsAuthenticated(true);
          setUser(result);
          setIsLoading(false);
          console.log('result: Authenticated', result);
          return;
        }
      } catch (error) {
        console.log('error', error);
      }
      // console.log('result', result);
      // If you want to short-circuit when no cookies exist, uncomment:
        
      

      // Defensive handling for different api implementations:
      // - api.getMe() might throw on 401
      // - or it might return { ok: true, data: user } / { ok: false, error }
      // const result = await api.getMe();

      // If api.getMe returns an object with ok/data:
      
    } catch (err) {
      console.warn('Auth verification failed:', err?.message ?? err);
      if (isMountedRef.current) {
        setIsAuthenticated(false);
        setUser(null);
      }
    } finally {
      isCheckingRef.current = false;
      if (isMountedRef.current) setIsLoading(false);
    }
  }, []);

  // Check auth on mount
  useEffect(() => {
    checkAuthStatus();
  }, [checkAuthStatus]);

  const login = useCallback(async (credentials) => {
    try {
      if (isMountedRef.current) setIsLoading(true);

      const response = await api.login(credentials);

      // If response uses ok flag:
      if (response && typeof response === 'object' && 'ok' in response) {
        if (response.ok) {
          await checkAuthStatus();
          return { success: true };
        } else {
          return { success: false, error: response.error ?? 'Login failed' };
        }
      }

      // If login throws on error, we won't reach here on failure.
      // If it returns something else, assume success and re-check.
      await checkAuthStatus();
      return { success: true };
    } catch (error) {
      console.error('Login error:', error);
      return { success: false, error: error?.message ?? 'Network error' };
    } finally {
      if (isMountedRef.current) setIsLoading(false);
    }
  }, [checkAuthStatus]);

  const logout = useCallback(async () => {
    try {
      if (isMountedRef.current) setIsLoading(true);
      // call API; don't rely on it always succeeding
      await api.logout();
    } catch (err) {
      console.warn('Logout API call failed:', err);
    } finally {
      if (isMountedRef.current) {
        setIsAuthenticated(false);
        setUser(null);
        setIsLoading(false);
      }
    }
  }, []);

  // Listen for external auth refresh events (e.g. broadcast channel, other tab)
  useEffect(() => {
    const handleAuthRefresh = async () => {
      console.log('Auth refresh event received');
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