/**
 * Emergency Access API Service
 *
 * Handles all API calls to the Emergency Access backend endpoints
 */

import apiClient from './api';

/**
 * Create a new emergency access request
 */
export async function createEmergencyRequest(roleId, duration, reason) {
  try {
    const response = await apiClient.post('/emergency-access/requests/create/', {
      role_id: roleId,
      requested_duration: duration,
      reason: reason,
    });
    return response.data;
  } catch (error) {
    console.error('Error creating emergency access request:', error);
    throw error;
  }
}

/**
 * Get current user's emergency access requests
 */
export async function getMyEmergencyRequests() {
  try {
    const response = await apiClient.get('/emergency-access/requests/my/');
    return response.data;
  } catch (error) {
    console.error('Error fetching emergency access requests:', error);
    throw error;
  }
}

/**
 * Get all emergency access requests (admin)
 */
export async function getAllEmergencyRequests(limit = 100) {
  try {
    const response = await apiClient.get(`/emergency-access/requests/all/?limit=${limit}`);
    return response.data;
  } catch (error) {
    console.error('Error fetching emergency access requests:', error);
    throw error;
  }
}

/**
 * Get pending emergency access requests (admin)
 */
export async function getPendingEmergencyRequests() {
  try {
    const response = await apiClient.get('/emergency-access/requests/pending/');
    return response.data;
  } catch (error) {
    console.error('Error fetching pending requests:', error);
    throw error;
  }
}

/**
 * Get emergency access request details
 */
export async function getEmergencyRequestDetail(requestId) {
  try {
    const response = await apiClient.get(`/emergency-access/requests/${requestId}/`);
    return response.data;
  } catch (error) {
    console.error('Error fetching request details:', error);
    throw error;
  }
}

/**
 * Approve an emergency access request (admin)
 */
export async function approveEmergencyRequest(requestId, approvedDuration, durationReason) {
  try {
    const response = await apiClient.put(`/emergency-access/requests/${requestId}/approve/`, {
      approved_duration: approvedDuration,
      duration_modified_reason: durationReason,
    });
    return response.data;
  } catch (error) {
    console.error('Error approving emergency access request:', error);
    throw error;
  }
}

/**
 * Reject an emergency access request (admin)
 */
export async function rejectEmergencyRequest(requestId, rejectionReason) {
  try {
    const response = await apiClient.put(`/emergency-access/requests/${requestId}/reject/`, {
      rejection_reason: rejectionReason,
    });
    return response.data;
  } catch (error) {
    console.error('Error rejecting emergency access request:', error);
    throw error;
  }
}

/**
 * Withdraw an emergency access request (user)
 */
export async function withdrawEmergencyRequest(requestId, revocationReason) {
  try {
    const response = await apiClient.put(`/emergency-access/requests/${requestId}/withdraw/`, {
      revocation_reason: revocationReason,
    });
    return response.data;
  } catch (error) {
    console.error('Error withdrawing emergency access request:', error);
    throw error;
  }
}

/**
 * Get current user's active temporary roles
 */
export async function getMyActiveTemporaryRoles() {
  try {
    const response = await apiClient.get('/emergency-access/my-temporary-roles/');
    return response.data;
  } catch (error) {
    console.error('Error fetching active temporary roles:', error);
    throw error;
  }
}
