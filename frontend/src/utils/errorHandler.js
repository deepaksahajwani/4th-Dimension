/**
 * Utility function to format error messages from API responses
 * Handles both simple string errors and Pydantic validation error arrays
 */
export const formatErrorMessage = (error, defaultMessage = 'An error occurred') => {
  if (!error.response) {
    return error.message || defaultMessage;
  }

  const detail = error.response?.data?.detail;

  // If detail is a string, return it
  if (typeof detail === 'string') {
    return detail;
  }

  // If detail is an array (Pydantic validation errors)
  if (Array.isArray(detail)) {
    return detail
      .map(err => {
        if (typeof err === 'string') return err;
        if (err.msg) return `${err.loc?.join(' → ') || 'Field'}: ${err.msg}`;
        return JSON.stringify(err);
      })
      .join(', ');
  }

  // If detail is an object with a message
  if (detail && typeof detail === 'object') {
    if (detail.message) return detail.message;
    if (detail.msg) return detail.msg;
    // Try to extract useful information from the object
    return JSON.stringify(detail);
  }

  return defaultMessage;
};
