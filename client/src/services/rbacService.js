/**
 * RBAC API Service
 *
 * Handles all API calls to the RBAC backend endpoints
 */

import apiClient from './api';

/**
 * Fetch all roles assigned to a user
 */
export async function getUserRoles(username) {
  try {
    const response = await apiClient.get(`/rbac/roles/?username=${encodeURIComponent(username)}`);
    return response.data;
  } catch (error) {
    console.error('Error fetching user roles:', error);
    throw error;
  }
}

/**
 * Assign a role to a user
 */
export async function assignRole(username, roleName, startDate = null, endDate = null) {
  try {
    const payload = {
      username,
      role_name: roleName,
    };

    if (startDate) payload.start_date = startDate;
    if (endDate) payload.end_date = endDate;

    const response = await apiClient.post('/rbac/roles/assign/', payload);
    return response.data;
  } catch (error) {
    console.error('Error assigning role:', error);
    throw error;
  }
}

/**
 * Remove a role from a user
 */
export async function removeRole(username, roleName) {
  try {
    const response = await apiClient.delete('/rbac/roles/remove/', {
      data: {
        username,
        role_name: roleName,
      },
    });
    return response.data;
  } catch (error) {
    console.error('Error removing role:', error);
    throw error;
  }
}

/**
 * Replace all user roles with new roles
 */
export async function replaceUserRoles(username, roleNames, startDate = null, endDate = null) {
  try {
    const payload = {
      username,
      roles: roleNames,
    };

    if (startDate) payload.start_date = startDate;
    if (endDate) payload.end_date = endDate;

    const response = await apiClient.put('/rbac/roles/replace/', payload);
    return response.data;
  } catch (error) {
    console.error('Error replacing roles:', error);
    throw error;
  }
}

/**
 * Get user status (blocked/unblocked)
 */
export async function getUserStatus(username) {
  try {
    const response = await apiClient.get(`/rbac/users/status/?username=${encodeURIComponent(username)}`);
    return response.data;
  } catch (error) {
    console.error('Error fetching user status:', error);
    throw error;
  }
}

/**
 * Block a user
 */
export async function blockUser(username, reason) {
  try {
    const response = await apiClient.post('/rbac/users/block/', {
      username,
      reason,
    });
    return response.data;
  } catch (error) {
    console.error('Error blocking user:', error);
    throw error;
  }
}

/**
 * Unblock a user
 */
export async function unblockUser(username) {
  try {
    const response = await apiClient.post('/rbac/users/unblock/', {
      username,
    });
    return response.data;
  } catch (error) {
    console.error('Error unblocking user:', error);
    throw error;
  }
}

/**
 * Get all blocked users
 */
export async function getBlockedUsers() {
  try {
    const response = await apiClient.get('/rbac/users/blocked/');
    return response.data;
  } catch (error) {
    console.error('Error fetching blocked users:', error);
    throw error;
  }
}

/**
 * Check if user can access system
 */
export async function checkUserAccess(username) {
  try {
    const response = await apiClient.get(`/rbac/users/check-access/?username=${encodeURIComponent(username)}`);
    return response.data;
  } catch (error) {
    console.error('Error checking user access:', error);
    throw error;
  }
}

/**
 * Get role conflict configuration
 */
export async function getRoleConflicts() {
  try {
    const response = await apiClient.get('/rbac/config/conflicts/');
    return response.data;
  } catch (error) {
    console.error('Error fetching role conflicts:', error);
    throw error;
  }
}

/**
 * Get role eligibility configuration
 */
export async function getRoleEligibility() {
  try {
    const response = await apiClient.get('/rbac/config/eligibility/');
    return response.data;
  } catch (error) {
    console.error('Error fetching role eligibility:', error);
    throw error;
  }
}
