import apiClient from './api';

/**
 * User Service - Handles all user-related API calls
 * Centralizes communication with backend user endpoints
 */

export const createUser = async (userData) => {
  const response = await apiClient.post('/users/add/', userData);
  return response.data;
};

export const createStudent = async (userData) => {
  const response = await apiClient.post('/users/add-student/', userData);
  return response.data;
};

export const createFaculty = async (userData) => {
  const response = await apiClient.post('/users/add-faculty/', userData);
  return response.data;
};

export const createStaff = async (userData) => {
  const response = await apiClient.post('/users/add-staff/', userData);
  return response.data;
};

export const resetPassword = async (userData) => {
  const response = await apiClient.post('/users/reset_password/', userData);
  return response.data;
};

export const bulkUploadUsers = async (formData) => {
  const response = await apiClient.post('/users/import/', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

export const downloadSampleCSV = async () => {
  const response = await apiClient.get('/download-sample-csv', {
    responseType: 'blob',
  });

  const blob = new Blob([response.data], { type: 'text/csv' });
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'sample.csv';
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(url);
};

export const fetchUsersByType = async (type) => {
  const response = await apiClient.get('/users', {
    params: { type },
  });
  return response.data;
};

export const deleteUser = async (userId) => {
  const response = await apiClient.delete(`/users/${userId}/`);
  return response.data;
};

export const updateUser = async (userId, userData) => {
  const response = await apiClient.put(`/users/${userId}/`, userData);
  return response.data;
};

/**
 * Get user roles by username (uses the updated endpoint with temporary role support)
 */
export const getUserRolesByUsername = async (username) => {
  const response = await apiClient.get(`/get-user-roles-by-username?username=${encodeURIComponent(username)}`);
  return response.data;
};
