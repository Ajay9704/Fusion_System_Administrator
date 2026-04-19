/**
 * Enterprise-Level User Service
 * Handles all user-related operations with proper validation and error handling
 */

import apiClient from './api';
import { showErrorNotification, showSuccessNotification } from '../utils/errorHandler';

// User Creation with Enterprise-Grade Validation
export const createStudent = async (studentData) => {
  try {
    const response = await apiClient.post('/users/add-student/', studentData);
    return response.data;
  } catch (error) {
    // Enhanced error handling for student creation
    if (error.response?.status === 400) {
      const validationErrors = error.response.data?.validation_errors || {};
      const errorMessages = Object.entries(validationErrors).map(([field, errors]) => {
        const fieldName = field.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
        const errorList = Array.isArray(errors) ? errors.join(', ') : errors;
        return `${fieldName}: ${errorList}`;
      });

      if (errorMessages.length > 0) {
        error.userMessage = errorMessages.join('\n');
      }
    }
    throw error;
  }
};

export const createFaculty = async (facultyData) => {
  try {
    const response = await apiClient.post('/users/add-faculty/', facultyData);
    return response.data;
  } catch (error) {
    // Enhanced error handling for faculty creation
    if (error.response?.status === 400) {
      const validationErrors = error.response.data?.validation_errors || {};
      const errorMessages = Object.entries(validationErrors).map(([field, errors]) => {
        const fieldName = field.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
        const errorList = Array.isArray(errors) ? errors.join(', ') : errors;
        return `${fieldName}: ${errorList}`;
      });

      if (errorMessages.length > 0) {
        error.userMessage = errorMessages.join('\n');
      }
    }
    throw error;
  }
};

export const createStaff = async (staffData) => {
  try {
    const response = await apiClient.post('/users/add-staff/', staffData);
    return response.data;
  } catch (error) {
    // Enhanced error handling for staff creation
    if (error.response?.status === 400) {
      const validationErrors = error.response.data?.validation_errors || {};
      const errorMessages = Object.entries(validationErrors).map(([field, errors]) => {
        const fieldName = field.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
        const errorList = Array.isArray(errors) ? errors.join(', ') : errors;
        return `${fieldName}: ${errorList}`;
      });

      if (errorMessages.length > 0) {
        error.userMessage = errorMessages.join('\n');
      }
    }
    throw error;
  }
};

// Bulk Upload with Enterprise-Grade Error Handling
export const bulkUploadUsers = async (formData) => {
  try {
    const response = await apiClient.post('/users/import/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  } catch (error) {
    // Enhanced error handling for bulk upload
    if (error.response?.data?.skipped_users_csv) {
      error.userMessage = 'Some users were skipped. Download the skipped users file for details.';
    }
    throw error;
  }
};

// Archive and Restore Operations
export const archiveUser = async (username) => {
  try {
    const response = await apiClient.post(`/users/${username}/archive/`);
    showSuccessNotification(`User ${username} has been archived successfully`);
    return response.data;
  } catch (error) {
    if (error.response?.status === 403) {
      error.userMessage = 'User must be inactive for at least 30 days before archival.';
    } else if (error.response?.status === 404) {
      error.userMessage = 'User not found or already archived.';
    }
    throw error;
  }
};

export const restoreUser = async (username) => {
  try {
    const response = await apiClient.post(`/users/${username}/restore/`);
    showSuccessNotification(`User ${username} has been restored successfully`);
    return response.data;
  } catch (error) {
    if (error.response?.status === 403) {
      error.userMessage = 'You do not have permission to restore this user.';
    } else if (error.response?.status === 404) {
      error.userMessage = 'User not found or already active.';
    }
    throw error;
  }
};

// User Search and Filtering
export const searchUsers = async (params) => {
  try {
    const response = await apiClient.get('/users/', { params });
    return response.data;
  } catch (error) {
    throw error;
  }
};

export const fetchUsersByType = async (userType) => {
  try {
    const response = await apiClient.get(`/users/?user_type=${userType}`);
    return response.data;
  } catch (error) {
    throw error;
  }
};

// Password Reset with Enterprise Security
export const resetPassword = async (username, passwordData) => {
  try {
    const response = await apiClient.post('/users/reset_password/', {
      username,
      ...passwordData
    });
    showSuccessNotification(`Password reset successfully for ${username}`);
    return response.data;
  } catch (error) {
    if (error.response?.status === 403) {
      error.userMessage = 'You do not have permission to reset this user\'s password.';
    } else if (error.response?.status === 404) {
      error.userMessage = 'User not found.';
    }
    throw error;
  }
};

// User Deletion with Proper Validation
export const deleteUser = async (username, reason) => {
  try {
    const response = await apiClient.delete('/users/', {
      data: { username, reason }
    });
    showSuccessNotification(`User ${username} has been deleted successfully`);
    return response.data;
  } catch (error) {
    if (error.response?.status === 403) {
      error.userMessage = 'Cannot delete user with active roles or recent activity.';
    } else if (error.response?.status === 404) {
      error.userMessage = 'User not found.';
    }
    throw error;
  }
};

// Export functionality
export const exportUsers = async (params) => {
  try {
    const response = await apiClient.get('/users/export/', {
      params,
      responseType: 'blob'
    });

    // Create download link
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `users_export_${new Date().toISOString()}.csv`);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);

    showSuccessNotification('User data exported successfully');
    return true;
  } catch (error) {
    showErrorNotification(error, 'Export Failed');
    return false;
  }
};

export default {
  createStudent,
  createFaculty,
  createStaff,
  bulkUploadUsers,
  archiveUser,
  restoreUser,
  searchUsers,
  fetchUsersByType,
  resetPassword,
  deleteUser,
  exportUsers
};
