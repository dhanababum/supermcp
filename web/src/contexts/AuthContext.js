import React, { createContext, useContext, useState, useCallback, useRef, useEffect } from 'react';
import { authCookies } from '../services/cookies';
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
      console.log('Checking auth status, cookies present:', authCookies.hasAuthCookies && authCookies.hasAuthCookies());

      // If you want to short-circuit when no cookies exist, uncomment:
      // if (!authCookies.hasAuthCookies()) {
      //   if (isMountedRef.current) {
      //     setIsAuthenticated(false);
      //     setUser(null);
      //     setIsLoading(false);
      //   }
      //   return;
      // }

      // Defensive handling for different api implementations:
      // - api.getMe() might throw on 401
      // - or it might return { ok: true, data: user } / { ok: false, error }
      const result = await api.getMe();

      // If api.getMe returns an object with ok/data:
      if (result && typeof result === 'object' && 'ok' in result) {
        if (result.ok) {
          if (isMountedRef.current) {
            setUser(result.data ?? null);
            setIsAuthenticated(true);
          }
        } else {
          // failed validation
          if (isMountedRef.current) {
            setIsAuthenticated(false);
            setUser(null);
            authCookies.clearAuth();
          }
        }
      } else {
        // If it returns user directly (or throws), treat result as user
        if (result) {
          if (isMountedRef.current) {
            setUser(result);
            setIsAuthenticated(true);
          }
        } else {
          if (isMountedRef.current) {
            setIsAuthenticated(false);
            setUser(null);
            authCookies.clearAuth();
          }
        }
      }
    } catch (err) {
      console.warn('Auth verification failed:', err?.message ?? err);
      if (isMountedRef.current) {
        setIsAuthenticated(false);
        setUser(null);
        try { authCookies.clearAuth(); } catch (e) { /* ignore */ }
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
        try { authCookies.clearAuth(); } catch (e) { /* ignore */ }
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

  const value = {
    isAuthenticated,
    isLoading,
    user,
    login,
    logout,
    checkAuthStatus,
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