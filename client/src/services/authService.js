import apiClient from './api';

/**
 * Auth Service - Handles all authentication-related API calls
 * Centralizes communication with backend auth endpoints
 */

/**
 * Change password for authenticated user
 * @param {Object} passwordData - Password change data
 * @param {string} passwordData.current_password - Current password
 * @param {string} passwordData.new_password - New password
 * @returns {Promise<Object>} Success message
 */
export const changePassword = async (passwordData) => {
  const response = await apiClient.post('/auth/change-password/', passwordData);
  return response.data;
};

/**
 * Get current authenticated user information
 * @returns {Promise<Object>} User data
 */
export const getCurrentUser = async () => {
  const response = await apiClient.get('/auth/me/');
  return response.data;
};

/**
 * Login user
 * @param {Object} credentials - Login credentials
 * @param {string} credentials.username - Username or email
 * @param {string} credentials.password - Password
 * @returns {Promise<Object>} Auth tokens and user data
 */
export const login = async (credentials) => {
  const response = await apiClient.post('/auth/login/', credentials);
  return response.data;
};

/**
 * Logout current user
 * @returns {Promise<Object>} Success message
 */
export const logout = async () => {
  const response = await apiClient.post('/auth/logout/');
  return response.data;
};
