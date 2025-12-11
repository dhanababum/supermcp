// Utility functions for handling and formatting errors

/**
 * Formats an error object or array into a user-friendly string
 * @param {any} error - The error to format
 * @returns {string} - Formatted error message
 */
export const formatError = (error) => {
  if (!error) return '';
  
  // Handle string errors
  if (typeof error === 'string') {
    return error;
  }
  
  // Handle array of errors
  if (Array.isArray(error)) {
    const errorMessages = error.map(err => {
      if (typeof err === 'string') return err;
      if (typeof err === 'object') {
        return err.msg || err.message || err.detail || JSON.stringify(err);
      }
      return String(err);
    });
    
    // Remove duplicates and filter out empty messages
    const uniqueMessages = [...new Set(errorMessages.filter(msg => msg && msg.trim()))];
    
    // If all messages are the same, show just one
    if (uniqueMessages.length === 1) {
      return uniqueMessages[0];
    }
    
    // If multiple different messages, join them
    return uniqueMessages.join(', ');
  }
  
  // Handle object errors
  if (typeof error === 'object') {
    // Check for common error message properties
    return error.msg || 
           error.message || 
           error.detail || 
           error.error || 
           error.description ||
           JSON.stringify(error);
  }
  
  // Fallback to string conversion
  return String(error);
};

/**
 * Extracts error messages from API response errors
 * @param {Response} response - The fetch response object
 * @returns {Promise<string>} - Formatted error message
 */
export const extractApiError = async (response) => {
  try {
    const errorData = await response.json();
    return formatError(errorData.detail || errorData.error || errorData);
  } catch (e) {
    return `HTTP ${response.status}: ${response.statusText}`;
  }
};

/**
 * Handles different types of validation errors
 * @param {any} validationError - Validation error from form or API
 * @returns {string} - Formatted validation error message
 */
export const formatValidationError = (validationError) => {
  if (!validationError) return '';
  
  // Handle Pydantic validation errors (FastAPI format)
  if (Array.isArray(validationError)) {
    return validationError.map(err => {
      if (typeof err === 'object' && err.msg) {
        const location = err.loc ? err.loc.join('.') : '';
        return location ? `${location}: ${err.msg}` : err.msg;
      }
      return formatError(err);
    }).join(', ');
  }
  
  return formatError(validationError);
};

/**
 * Extracts field-specific validation errors from FastAPI response
 * @param {any} errorResponse - The error response from FastAPI
 * @returns {object} - Object with field names as keys and error messages as values
 */
export const extractFieldErrors = (errorResponse) => {
  const fieldErrors = {};
  
  if (!errorResponse || !errorResponse.detail) {
    return fieldErrors;
  }
  
  // Handle array of validation errors (FastAPI format)
  if (Array.isArray(errorResponse.detail)) {
    errorResponse.detail.forEach((error) => {
      if (typeof error === 'object' && error.loc && error.msg) {
        // Extract field name from location array (skip 'body' if present)
        const fieldName = error.loc[error.loc.length - 1];
        if (fieldName && fieldName !== 'body') {
          fieldErrors[fieldName] = error.msg;
        }
      }
    });
  }
  
  return fieldErrors;
};

/**
 * Maps FastAPI field names to form field names
 * @param {string} apiFieldName - Field name from API
 * @returns {string} - Corresponding form field name
 */
export const mapApiFieldToFormField = (apiFieldName) => {
  const fieldMapping = {
    'username': 'email', // FastAPI form-based uses 'username' but our form uses 'email'
    'email': 'email',    // JSON endpoint uses 'email'
    'password': 'password',
    'confirmPassword': 'confirmPassword'
  };
  
  return fieldMapping[apiFieldName] || apiFieldName;
};

/**
 * Creates a standardized error object for consistent handling
 * @param {any} error - The original error
 * @param {string} context - Context where the error occurred
 * @returns {object} - Standardized error object
 */
export const createStandardError = (error, context = '') => {
  const message = formatError(error);
  return {
    message,
    context,
    timestamp: new Date().toISOString(),
    originalError: error
  };
};
