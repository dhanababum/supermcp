// Global fetch configuration for consistent cookie handling

// Store original fetch
const originalFetch = window.fetch;

// Override fetch to include credentials by default
window.fetch = async (url, options = {}) => {
  // Ensure credentials are included for same-origin requests
  const defaultOptions = {
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  };

  // Merge with provided options
  const mergedOptions = {
    ...defaultOptions,
    ...options,
    headers: {
      ...defaultOptions.headers,
      ...options.headers,
    },
  };

  try {
    const response = await originalFetch(url, mergedOptions);
    
    // Handle 401 responses globally
    if (response.status === 401 && !url.includes('/auth/')) {
      // Only redirect if not already on auth page
      if (!window.location.pathname.includes('/auth/')) {
        console.warn('Unauthorized request, redirecting to login');
        window.location.href = '/auth/login';
      }
    }
    
    return response;
  } catch (error) {
    console.error('Fetch error:', error);
    throw error;
  }
};

// Export the configured fetch
export default window.fetch;
