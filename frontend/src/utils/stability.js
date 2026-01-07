/**
 * Core Stability Utilities
 * Centralized error handling, auth validation, and data loading utilities
 */

import axios from 'axios';
import { toast } from 'sonner';

const API = process.env.REACT_APP_BACKEND_URL + '/api';
const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

/**
 * Check if user is authenticated
 * Returns true if valid auth exists, false otherwise
 */
export const isAuthenticated = () => {
  const token = localStorage.getItem('token');
  const useCookieAuth = localStorage.getItem('use_cookie_auth');
  return !!(token || useCookieAuth);
};

/**
 * Get current auth token
 */
export const getAuthToken = () => {
  return localStorage.getItem('token');
};

/**
 * Get auth headers for API calls
 */
export const getAuthHeaders = () => {
  const token = localStorage.getItem('token');
  return token ? { Authorization: `Bearer ${token}` } : {};
};

/**
 * Clear all auth data and redirect to login
 */
export const clearAuthAndRedirect = (message = 'Session expired. Please login again.') => {
  localStorage.removeItem('token');
  localStorage.removeItem('user');
  localStorage.removeItem('use_cookie_auth');
  toast.error(message);
  window.location.href = '/login';
};

/**
 * Safe API call wrapper with consistent error handling
 * @param {Function} apiCall - The API call function to execute
 * @param {Object} options - Options for error handling
 * @returns {Object} { data, error, success }
 */
export const safeApiCall = async (apiCall, options = {}) => {
  const {
    showErrorToast = true,
    errorMessage = 'An error occurred',
    onAuthError = null,
    retryOnFail = false,
  } = options;

  try {
    const response = await apiCall();
    return { data: response.data, error: null, success: true };
  } catch (error) {
    console.error('API Error:', error);
    
    // Handle authentication errors
    if (error.response?.status === 401) {
      if (onAuthError) {
        onAuthError();
      } else {
        clearAuthAndRedirect();
      }
      return { data: null, error: 'Authentication required', success: false };
    }
    
    // Handle other errors
    const errorDetail = error.response?.data?.detail || error.message || errorMessage;
    
    if (showErrorToast) {
      toast.error(errorDetail);
    }
    
    return { data: null, error: errorDetail, success: false };
  }
};

/**
 * Safe file download with proper error handling
 * @param {string} url - The file URL to download
 * @param {string} filename - The filename for the download
 * @param {Object} options - Download options
 */
export const safeFileDownload = async (url, filename, options = {}) => {
  const { showProgress = true } = options;
  
  try {
    // Ensure URL is absolute
    const fullUrl = url.startsWith('http') ? url : `${BACKEND_URL}${url}`;
    
    const token = getAuthToken();
    const headers = token ? { Authorization: `Bearer ${token}` } : {};
    
    const response = await axios.get(fullUrl, {
      headers,
      responseType: 'blob',
      withCredentials: localStorage.getItem('use_cookie_auth') ? true : false,
    });
    
    // Validate response
    if (!response.data || response.data.size === 0) {
      throw new Error('Empty file received');
    }
    
    // Check if response is an error (API might return JSON error)
    if (response.data.type === 'application/json') {
      const text = await response.data.text();
      const errorData = JSON.parse(text);
      throw new Error(errorData.detail || 'Download failed');
    }
    
    // Create download link
    const blob = new Blob([response.data], { type: response.headers['content-type'] || 'application/octet-stream' });
    const downloadUrl = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(downloadUrl);
    
    return { success: true, error: null };
  } catch (error) {
    console.error('Download error:', error);
    
    if (error.response?.status === 401) {
      clearAuthAndRedirect('Please login to download files');
      return { success: false, error: 'Authentication required' };
    }
    
    if (error.response?.status === 404) {
      toast.error('File not found');
      return { success: false, error: 'File not found' };
    }
    
    toast.error(error.message || 'Download failed. Please try again.');
    return { success: false, error: error.message };
  }
};

/**
 * Open file in new tab with auth
 * @param {string} url - The file URL to open
 */
export const openFileInNewTab = async (url) => {
  try {
    const fullUrl = url.startsWith('http') ? url : `${BACKEND_URL}${url}`;
    
    // For direct file access, we can open the URL directly
    // The browser will handle the file viewing
    window.open(fullUrl, '_blank');
    return { success: true };
  } catch (error) {
    console.error('Error opening file:', error);
    toast.error('Could not open file');
    return { success: false, error: error.message };
  }
};

/**
 * Ensure array - always returns an array even if input is null/undefined
 */
export const ensureArray = (value) => {
  if (Array.isArray(value)) return value;
  if (value === null || value === undefined) return [];
  return [value];
};

/**
 * Ensure object - always returns an object even if input is null/undefined
 */
export const ensureObject = (value, defaultValue = {}) => {
  if (value && typeof value === 'object' && !Array.isArray(value)) return value;
  return defaultValue;
};

/**
 * Safe JSON parse with fallback
 */
export const safeJsonParse = (jsonString, fallback = null) => {
  try {
    return JSON.parse(jsonString);
  } catch (e) {
    console.error('JSON parse error:', e);
    return fallback;
  }
};

/**
 * Format date safely
 */
export const safeFormatDate = (dateValue, options = {}) => {
  if (!dateValue) return 'N/A';
  
  try {
    const date = new Date(dateValue);
    if (isNaN(date.getTime())) return 'Invalid date';
    
    const defaultOptions = {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
      ...options
    };
    
    return date.toLocaleDateString('en-IN', defaultOptions);
  } catch (e) {
    console.error('Date format error:', e);
    return 'Invalid date';
  }
};

/**
 * Loading state component
 */
export const LoadingState = ({ message = 'Loading...' }) => (
  <div className="flex flex-col items-center justify-center h-64">
    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-orange-600 mb-4"></div>
    <p className="text-slate-600">{message}</p>
  </div>
);

/**
 * Error state component
 */
export const ErrorState = ({ message = 'Something went wrong', onRetry = null }) => (
  <div className="flex flex-col items-center justify-center h-64 text-center px-4">
    <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mb-4">
      <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
      </svg>
    </div>
    <p className="text-slate-900 font-medium mb-2">Error</p>
    <p className="text-slate-600 mb-4">{message}</p>
    {onRetry && (
      <button 
        onClick={onRetry}
        className="px-4 py-2 bg-orange-500 text-white rounded-lg hover:bg-orange-600 transition-colors"
      >
        Try Again
      </button>
    )}
  </div>
);

/**
 * Empty state component
 */
export const EmptyState = ({ icon = null, title = 'No data', message = '', action = null }) => (
  <div className="flex flex-col items-center justify-center h-64 text-center px-4">
    {icon && <div className="mb-4">{icon}</div>}
    <p className="text-slate-900 font-medium mb-1">{title}</p>
    {message && <p className="text-slate-600 text-sm mb-4">{message}</p>}
    {action}
  </div>
);

export default {
  isAuthenticated,
  getAuthToken,
  getAuthHeaders,
  clearAuthAndRedirect,
  safeApiCall,
  safeFileDownload,
  openFileInNewTab,
  ensureArray,
  ensureObject,
  safeJsonParse,
  safeFormatDate,
  LoadingState,
  ErrorState,
  EmptyState,
};
