// Cookie utility functions for managing authentication cookies

export const cookieUtils = {
  // Set a cookie with proper attributes
  set: (name, value, options = {}) => {
    const {
      expires = 7, // days
      path = '/',
      domain = window.location.hostname,
      secure = window.location.protocol === 'https:',
      sameSite = 'Lax'
    } = options;

    let cookieString = `${name}=${encodeURIComponent(value)}`;
    
    if (expires) {
      const date = new Date();
      date.setTime(date.getTime() + (expires * 24 * 60 * 60 * 1000));
      cookieString += `; expires=${date.toUTCString()}`;
    }
    
    cookieString += `; path=${path}`;
    cookieString += `; domain=${domain}`;
    
    if (secure) {
      cookieString += '; secure';
    }
    
    cookieString += `; samesite=${sameSite}`;
    
    document.cookie = cookieString;
  },

  // Get a cookie value
  get: (name) => {
    const nameEQ = name + "=";
    const ca = document.cookie.split(';');
    
    for (let i = 0; i < ca.length; i++) {
      let c = ca[i];
      while (c.charAt(0) === ' ') c = c.substring(1, c.length);
      if (c.indexOf(nameEQ) === 0) {
        return decodeURIComponent(c.substring(nameEQ.length, c.length));
      }
    }
    return null;
  },

  // Remove a cookie
  remove: (name, options = {}) => {
    const { path = '/', domain = window.location.hostname } = options;
    
    document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=${path}; domain=${domain}`;
  },

  // Check if cookies are enabled
  areEnabled: () => {
    try {
      const testCookie = 'test_cookie_enabled';
      this.set(testCookie, 'test');
      const enabled = this.get(testCookie) === 'test';
      this.remove(testCookie);
      return enabled;
    } catch (e) {
      return false;
    }
  },

  // Get all cookies as an object
  getAll: () => {
    const cookies = {};
    const ca = document.cookie.split(';');
    
    for (let i = 0; i < ca.length; i++) {
      let c = ca[i];
      while (c.charAt(0) === ' ') c = c.substring(1, c.length);
      const eqPos = c.indexOf('=');
      if (eqPos > 0) {
        const name = c.substring(0, eqPos);
        const value = decodeURIComponent(c.substring(eqPos + 1));
        cookies[name] = value;
      }
    }
    return cookies;
  }
};

// Authentication cookie helpers
export const authCookies = {
  // Check if user has authentication cookies
  hasAuthCookies: () => {
    const cookies = cookieUtils.getAll();
    // Check for common authentication cookie names
    // 'auth_cookie' is the cookie name set in api/users.py CookieTransport
    return !!(
      cookies.auth_cookie || 
      cookies.access_token || 
      cookies.session_id || 
      cookies.auth_token || 
      cookies.fastapi_users
    );
  },

  // Clear all authentication-related cookies
  clearAuth: () => {
    const authCookieNames = [
      'auth_cookie',      // Cookie name from api/users.py
      'access_token', 
      'session_id', 
      'auth_token', 
      'fastapi_users'
    ];
    authCookieNames.forEach(name => {
      cookieUtils.remove(name);
    });
  },

  // Get authentication token if available
  getAuthToken: () => {
    return (
      cookieUtils.get('auth_cookie') ||  // Cookie name from api/users.py
      cookieUtils.get('access_token') || 
      cookieUtils.get('auth_token')
    );
  }
};
