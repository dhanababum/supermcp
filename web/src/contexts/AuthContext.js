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

      // Check if login was successful (response might be a Response object or parsed data)
      // api.login now returns parsed data on error, or Response object on success
      if (response && (response.ok || response.success)) {
        // Wait for auth status to refresh
        await checkAuthStatus();
        return { success: true };
      }
      
      // If we got here, api.login might have thrown, or returned a non-ok response that wasn't caught
      // But api.js throws on error usually. 
      // If api.js returns a data object with error info (from the catch block in api.js? no it throws)
      
      // If we reached here without throwing, it means success?
      // api.js throws if !response.ok unless we handled it.
      // With my change to api.js, it will fall through to error handling if !response.ok.
      // So if it returns, it must be success (Response object).
      
      return { success: true };

    } catch (error) {
       // Use the error message from the API if available
       let errorMessage = error?.message || 'Login failed';
       
       // If the error message is a JSON string (from api.js throwing JSON.stringify(data.detail))
       try {
         const parsed = JSON.parse(errorMessage);
         if (parsed === 'LOGIN_BAD_CREDENTIALS') {
            errorMessage = 'Invalid email or password';
         } else if (typeof parsed === 'string') {
            errorMessage = parsed;
         }
       } catch (e) {
         // Not JSON, keep original
       }

       return { success: false, error: errorMessage };
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