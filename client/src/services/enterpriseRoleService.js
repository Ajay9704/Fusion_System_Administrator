/**
 * Enterprise-Level Role Management Service
 * Handles all role-related operations with proper validation
 */

import apiClient from './api';
import { showErrorNotification, showSuccessNotification } from '../utils/errorHandler';
import { PROGRAMME_DEPARTMENT_MAPPING } from '../utils/constants';

// Get User Roles with Enterprise Validation
export const getUserRoles = async (username) => {
  try {
    const response = await apiClient.get(`/get-user-roles-by-username/?username=${username}`);

    if (!response.data?.user) {
      throw new Error('User not found');
    }

    return {
      user: response.data.user,
      roles: response.data.roles || []
    };
  } catch (error) {
    if (error.response?.status === 404) {
      error.userMessage = `User "${username}" not found in the system.`;
    } else if (error.message) {
      error.userMessage = error.message;
    } else {
      error.userMessage = 'Failed to fetch user roles. Please try again.';
    }
    throw error;
  }
};

// Update User Roles with Comprehensive Validation
export const updateUserRoles = async (username, roleNames, userDetails = null) => {
  try {
    // Get user details if not provided
    if (!userDetails) {
      const userData = await getUserRoles(username);
      userDetails = userData.user;
    }

    // Validate role eligibility based on user type
    if (userDetails?.user_type) {
      const userType = userDetails.user_type;

      const facultyOnlyRoles = [
        'Professor', 'Associate Professor', 'Assistant Professor',
        'HOD', 'Dean', 'Director', 'Head of Department',
        'Associate Dean', 'Assistant Dean', 'Professor Emeritus'
      ];

      const staffOnlyRoles = [
        'Registrar', 'Assistant Registrar', 'Deputy Registrar',
        'Section Officer', 'Assistant Section Officer',
        'Clerk', 'Assistant', 'Peon', 'Driver'
      ];

      const invalidRoles = [];

      roleNames.forEach(roleName => {
        if (facultyOnlyRoles.includes(roleName) && userType !== 'faculty') {
          invalidRoles.push(`${roleName} (faculty only)`);
        }
        if (staffOnlyRoles.includes(roleName) && userType !== 'staff') {
          invalidRoles.push(`${roleName} (staff only)`);
        }
      });

      if (invalidRoles.length > 0) {
        const error = new Error(`Role eligibility validation failed`);
        error.userMessage = `The following roles cannot be assigned to ${userType}:\n${invalidRoles.join('\n')}`;
        error.validationErrors = invalidRoles;
        throw error;
      }
    }

    // Check for role conflicts
    const conflicts = checkRoleConflicts(roleNames);
    if (conflicts.length > 0) {
      const error = new Error('Role conflict detected');
      error.userMessage = `The following role conflicts exist:\n${conflicts.join('\n')}\n\nDo you want to proceed anyway?`;
      error.conflicts = conflicts;
      throw error;
    }

    // Proceed with update
    const response = await apiClient.put('/update-user-roles/', {
      username: username,
      roles: roleNames
    });

    showSuccessNotification(`Roles updated successfully for ${username}`);
    return response.data;
  } catch (error) {
    if (error.response?.status === 403) {
      error.userMessage = error.response.data?.error || 'Role assignment denied. Check eligibility requirements.';
    } else if (error.response?.status === 409) {
      error.userMessage = error.response.data?.error || 'Role conflict detected. Some roles cannot be assigned together.';
    } else if (!error.userMessage) {
      error.userMessage = 'Failed to update user roles. Please try again.';
    }
    throw error;
  }
};

// Check for role conflicts
const checkRoleConflicts = (roleNames) => {
  const conflictRules = {
    'Director': ['Dean', 'HOD', 'Head of Department', 'Registrar'],
    'Dean': ['Director'],
    'Registrar': ['Director', 'Dean'],
    'HOD': ['Director', 'Registrar'],
    'Head of Department': ['Director', 'Registrar'],
    'Professor': ['Associate Professor', 'Assistant Professor'],
    'Associate Professor': ['Professor', 'Assistant Professor'],
    'Professor Emeritus': ['Professor', 'Associate Professor', 'Assistant Professor']
  };

  const conflicts = [];

  roleNames.forEach(roleName => {
    if (conflictRules[roleName]) {
      conflictRules[roleName].forEach(conflictingRole => {
        if (roleNames.includes(conflictingRole)) {
          conflicts.push(`${roleName} conflicts with ${conflictingRole}`);
        }
      });
    }
  });

  return conflicts;
};

// Get Available Roles for User
export const getAvailableRoles = async () => {
  try {
    const response = await apiClient.get('/view-roles/');
    return response.data;
  } catch (error) {
    showErrorNotification(error, 'Failed to fetch available roles');
    throw error;
  }
};

// Switch Active Role
export const switchRole = async (roleId) => {
  try {
    const response = await apiClient.post('/roles/switch/', {
      role_id: parseInt(roleId)
    });

    // Update localStorage
    localStorage.setItem('activeRoleId', String(roleId));

    showSuccessNotification(`Role switched successfully`);
    return response.data;
  } catch (error) {
    if (error.response?.status === 403) {
      error.userMessage = 'You do not have permission to switch to this role.';
    } else if (error.response?.status === 404) {
      error.userMessage = 'Role not found or not available for your account.';
    }
    throw error;
  }
};

// Get Current Active Role
export const getActiveRole = async () => {
  try {
    const response = await apiClient.get('/roles/active/');
    return response.data;
  } catch (error) {
    // Return null if no active role (not an error condition)
    return null;
  }
};

// Get All Available Roles for Switching
export const getSwitchableRoles = async () => {
  try {
    const response = await apiClient.get('/roles/available/');
    return response.data.roles || [];
  } catch (error) {
    showErrorNotification(error, 'Failed to fetch available roles');
    return [];
  }
};

// Create Custom Role
export const createCustomRole = async (roleData) => {
  try {
    const response = await apiClient.post('/create-role/', roleData);
    showSuccessNotification(`Role "${roleData.name}" created successfully`);
    return response.data;
  } catch (error) {
    if (error.response?.status === 400) {
      error.userMessage = 'Role data is invalid. Please check all required fields.';
    } else if (error.response?.status === 409) {
      error.userMessage = 'A role with this name already exists.';
    }
    throw error;
  }
};

// Update Role
export const updateRole = async (roleId, roleData) => {
  try {
    const response = await apiClient.put('/modify-role/', {
      role_id: roleId,
      ...roleData
    });
    showSuccessNotification(`Role updated successfully`);
    return response.data;
  } catch (error) {
    if (error.response?.status === 404) {
      error.userMessage = 'Role not found.';
    }
    throw error;
  }
};

// Get Role Module Access
export const getRoleModuleAccess = async (roleId) => {
  try {
    const response = await apiClient.get('/get-module-access/', {
      params: { role_id: roleId }
    });
    return response.data;
  } catch (error) {
    throw error;
  }
};

// Update Role Module Access
export const updateRoleModuleAccess = async (roleId, moduleAccess) => {
  try {
    const response = await apiClient.post('/modify-roleaccess/', {
      role_id: roleId,
      module_access: moduleAccess
    });
    showSuccessNotification('Module access updated successfully');
    return response.data;
  } catch (error) {
    if (error.response?.status === 403) {
      error.userMessage = 'You do not have permission to modify role access.';
    } else if (error.response?.status === 404) {
      error.userMessage = 'Role not found.';
    }
    throw error;
  }
};

export default {
  getUserRoles,
  updateUserRoles,
  getAvailableRoles,
  switchRole,
  getActiveRole,
  getSwitchableRoles,
  createCustomRole,
  updateRole,
  getRoleModuleAccess,
  updateRoleModuleAccess
};
