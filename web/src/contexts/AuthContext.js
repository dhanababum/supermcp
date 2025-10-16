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
    console.log('🔍 Starting auth check...');
    
    // Prevent multiple simultaneous auth checks
    if (isCheckingRef.current) {
      console.log('⚠️ Auth check already in progress, skipping...');
      return;
    }

    isCheckingRef.current = true;
    setIsLoading(true);

    try {
      console.log('📡 Calling api.getMe()...');
      const result = await api.getMe();
      console.log('✅ api.getMe() result:', result);
      
      if (result) {
        setIsAuthenticated(true);
        setUser(result);
        console.log('✅ User authenticated:', result.email);
      } else {
        setIsAuthenticated(false);
        setUser(null);
        console.log('❌ No user data returned');
      }
    } catch (err) {
      console.warn('❌ Auth verification failed:', err?.message ?? err);
      setIsAuthenticated(false);
      setUser(null);
    } finally {
      isCheckingRef.current = false;
      setIsLoading(false);
      console.log('🏁 Auth check complete');
    }
  }, []);

  // Check auth on mount
  useEffect(() => {
    console.log('🚀 AuthProvider mounted - checking auth status');
    checkAuthStatus();
  }, [checkAuthStatus]);

  const login = useCallback(async (credentials) => {
    console.log('🔐 Login attempt...');
    try {
      setIsLoading(true);

      const response = await api.login(credentials);
      console.log('📡 Login response:', response);

      // Check if login was successful
      if (response && response.ok) {
        console.log('✅ Login successful - refreshing auth status');
        // Wait for auth status to refresh
        await checkAuthStatus();
        return { success: true };
      }

      // If response doesn't have 'ok' property, assume success and check auth
      if (!('ok' in response)) {
        console.log('✅ Login appears successful - refreshing auth status');
        await checkAuthStatus();
        return { success: true };
      }

      // Login failed
      console.log('❌ Login failed');
      return { success: false, error: 'Login failed' };
    } catch (error) {
      console.error('❌ Login error:', error);
      return { success: false, error: error?.message ?? 'Network error' };
    } finally {
      setIsLoading(false);
    }
  }, [checkAuthStatus]);

  const logout = useCallback(async () => {
    console.log('🚪 Logging out...');
    try {
      setIsLoading(true);
      await api.logout();
    } catch (err) {
      console.warn('⚠️ Logout API call failed:', err);
    } finally {
      setIsAuthenticated(false);
      setUser(null);
      setIsLoading(false);
      console.log('✅ Logged out');
    }
  }, []);

  // Listen for external auth refresh events
  useEffect(() => {
    const handleAuthRefresh = async () => {
      console.log('🔄 Auth refresh event received');
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

  // Debug logging
  console.log('📊 AuthProvider state:', { 
    isAuthenticated, 
    isLoading, 
    userEmail: user?.email || 'none' 
  });

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