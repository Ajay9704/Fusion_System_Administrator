/**
 * Enterprise-Level Emergency Access Service
 * Handles all emergency access operations with proper validation and security
 */

import apiClient from './api';
import { showErrorNotification, showSuccessNotification } from '../utils/errorHandler';

// Create Emergency Access Request
export const createEmergencyAccessRequest = async (requestData) => {
  try {
    // Validate duration
    if (requestData.duration_hours > 168) {
      const error = new Error('Duration validation failed');
      error.userMessage = 'Maximum duration is 168 hours (7 days) for emergency access.';
      throw error;
    }

    if (requestData.duration_hours < 1) {
      const error = new Error('Duration validation failed');
      error.userMessage = 'Minimum duration is 1 hour for emergency access.';
      throw error;
    }

    // Validate role
    const availableRoles = await getAvailableRoles();
    const requestedRole = availableRoles.find(role => role.id === requestData.role_id);

    if (!requestedRole) {
      const error = new Error('Role not found');
      error.userMessage = 'The requested role is not available.';
      throw error;
    }

    const response = await apiClient.post('/emergency-access/request/', {
      role_id: requestData.role_id,
      reason: requestData.reason,
      duration_hours: requestData.duration_hours
    });

    showSuccessNotification('Emergency access request submitted successfully');
    return response.data;
  } catch (error) {
    if (error.response?.status === 403) {
      error.userMessage = 'You are not eligible to request emergency access for this role.';
    } else if (error.response?.status === 429) {
      error.userMessage = 'You have too many pending emergency access requests. Please wait for existing requests to be processed.';
    } else if (!error.userMessage) {
      error.userMessage = 'Failed to create emergency access request. Please try again.';
    }
    throw error;
  }
};

// Get Emergency Access Requests
export const getEmergencyAccessRequests = async (view = 'my-requests', status = 'PENDING') => {
  try {
    const response = await apiClient.get('/emergency-access/requests/', {
      params: {
        view: view,
        status: status
      }
    });
    return response.data.requests || [];
  } catch (error) {
    showErrorNotification(error, 'Failed to fetch emergency access requests');
    return [];
  }
};

// Get My Emergency Access Requests
export const getMyEmergencyRequests = async () => {
  return await getEmergencyAccessRequests('my-requests', 'ALL');
};

// Get All Emergency Requests (Admin)
export const getAllEmergencyRequests = async (status = 'PENDING') => {
  return await getEmergencyAccessRequests('all-requests', status);
};

// Get Emergency Request History (Admin)
export const getEmergencyRequestHistory = async () => {
  return await getEmergencyAccessRequests('all-requests', 'ALL');
};

// Approve/Deny Emergency Access Request
export const processEmergencyAccessRequest = async (requestId, action, reason = '') => {
  try {
    if (!['approve', 'deny'].includes(action)) {
      throw new Error('Invalid action. Must be "approve" or "deny".');
    }

    if (action === 'deny' && !reason) {
      const error = new Error('Reason required for denial');
      error.userMessage = 'Please provide a reason for denying this emergency access request.';
      throw error;
    }

    const response = await apiClient.post(`/emergency-access/${requestId}/approve/`, {
      action: action,
      reason: reason
    });

    showSuccessNotification(`Emergency access request ${action}ed successfully`);
    return response.data;
  } catch (error) {
    if (error.response?.status === 403) {
      error.userMessage = 'You do not have permission to process emergency access requests.';
    } else if (error.response?.status === 404) {
      error.userMessage = 'Emergency access request not found.';
    } else if (error.response?.status === 409) {
      error.userMessage = 'This request has already been processed.';
    } else if (!error.userMessage) {
      error.userMessage = `Failed to ${action} emergency access request. Please try again.`;
    }
    throw error;
  }
};

// Activate Emergency Access
export const activateEmergencyAccess = async (requestId) => {
  try {
    const response = await apiClient.post(`/emergency-access/${requestId}/activate/`);

    showSuccessNotification('Emergency access activated successfully');
    return response.data;
  } catch (error) {
    if (error.response?.status === 403) {
      error.userMessage = 'You do not have permission to activate this emergency access.';
    } else if (error.response?.status === 404) {
      error.userMessage = 'Emergency access request not found.';
    } else if (error.response?.status === 409) {
      error.userMessage = 'This emergency access cannot be activated. It may have expired or been revoked.';
    }
    throw error;
  }
};

// Revoke Emergency Access
export const revokeEmergencyAccess = async (requestId, reason = '') => {
  try {
    const response = await apiClient.post(`/emergency-access/${requestId}/revoke/`, {
      reason: reason
    });

    showSuccessNotification('Emergency access revoked successfully');
    return response.data;
  } catch (error) {
    if (error.response?.status === 403) {
      error.userMessage = 'You do not have permission to revoke this emergency access.';
    } else if (error.response?.status === 404) {
      error.userMessage = 'Emergency access request not found.';
    }
    throw error;
  }
};

// Get Available Roles for Emergency Access
export const getAvailableRoles = async () => {
  try {
    const response = await apiClient.get('/view-roles/');
    return response.data;
  } catch (error) {
    showErrorNotification(error, 'Failed to fetch available roles');
    return [];
  }
};

// Check Emergency Access Status
export const checkEmergencyAccessStatus = async () => {
  try {
    const response = await apiClient.get('/emergency-access/status/');
    return response.data;
  } catch (error) {
    // Return inactive status if endpoint fails
    return {
      hasEmergencyAccess: false,
      activeRequest: null
    };
  }
};

export default {
  createEmergencyAccessRequest,
  getEmergencyAccessRequests,
  getMyEmergencyRequests,
  getAllEmergencyRequests,
  getEmergencyRequestHistory,
  processEmergencyAccessRequest,
  activateEmergencyAccess,
  revokeEmergencyAccess,
  getAvailableRoles,
  checkEmergencyAccessStatus
};
