/**
 * Enterprise Role Service
 * Handles all role and designation related operations
 */

import apiService from '../base/ApiService';
import cacheService from '../base/CacheService';
import errorService from '../base/ErrorService';
import { roleTransformer, roleListTransformer } from '../../utils/transformers/roleTransformers';

class RoleService {
  /**
   * Get all roles/designations
   */
  async getAllRoles(useCache = true) {
    const cacheKey = 'roles:all';

    // Check cache first
    if (useCache && cacheService.has(cacheKey)) {
      return {
        success: true,
        data: cacheService.get(cacheKey),
        cached: true,
      };
    }

    try {
      const response = await apiService.get('/view-roles/');
      const transformedData = roleListTransformer(response.data);

      // Cache the result
      if (useCache) {
        cacheService.set(cacheKey, transformedData);
      }

      return {
        success: true,
        data: transformedData,
        cached: false,
      };
    } catch (error) {
      const handledError = errorService.handle(error, {
        action: 'getAllRoles',
      });

      return {
        success: false,
        error: handledError,
      };
    }
  }

  /**
   * Get roles by category
   */
  async getRolesByCategory(category, basic = true) {
    const cacheKey = cacheService.constructor.generateKey('roles-by-category', { category, basic });

    try {
      const response = await apiService.post('/view-designations/', { category, basic });
      const transformedData = roleListTransformer(response.data);

      // Cache the result
      cacheService.set(cacheKey, transformedData);

      return {
        success: true,
        data: transformedData,
      };
    } catch (error) {
      const handledError = errorService.handle(error, {
        action: 'getRolesByCategory',
        category,
        basic,
      });

      return {
        success: false,
        error: handledError,
      };
    }
  }

  /**
   * Get available roles for a user
   */
  async getAvailableRoles(username) {
    const cacheKey = cacheService.constructor.generateKey('available-roles', { username });

    try {
      const response = await apiService.post('/roles/available/', { username });
      const transformedData = roleListTransformer(response.data);

      // Cache the result
      cacheService.set(cacheKey, transformedData);

      return {
        success: true,
        data: transformedData,
      };
    } catch (error) {
      const handledError = errorService.handle(error, {
        action: 'getAvailableRoles',
        username,
      });

      return {
        success: false,
        error: handledError,
      };
    }
  }

  /**
   * Create new role/designation
   */
  async createRole(roleData) {
    try {
      const response = await apiService.post('/create-role/', roleData);

      // Clear roles cache
      cacheService.delete('roles:*');

      return {
        success: true,
        data: roleTransformer(response.data),
        message: 'Role created successfully',
      };
    } catch (error) {
      const handledError = errorService.handle(error, {
        action: 'createRole',
      });

      return {
        success: false,
        error: handledError,
      };
    }
  }

  /**
   * Update user roles
   */
  async updateUserRoles(username, roles) {
    try {
      const response = await apiService.put('/update-user-roles/', {
        username,
        roles,
      });

      // Clear related cache entries
      cacheService.delete('roles:*');
      cacheService.delete(`user-roles:${username}`);

      return {
        success: true,
        data: response.data,
        message: 'User roles updated successfully',
      };
    } catch (error) {
      const handledError = errorService.handle(error, {
        action: 'updateUserRoles',
        username,
        roles,
      });

      return {
        success: false,
        error: handledError,
      };
    }
  }

  /**
   * Get user roles by username
   */
  async getUserRoles(username) {
    const cacheKey = cacheService.constructor.generateKey('user-roles', { username });

    try {
      const response = await apiService.get(`/get-user-roles-by-username/?username=${username}`);
      const transformedData = {
        user: response.data.user,
        roles: roleListTransformer(response.data.roles),
      };

      // Cache the result
      cacheService.set(cacheKey, transformedData);

      return {
        success: true,
        data: transformedData,
      };
    } catch (error) {
      const handledError = errorService.handle(error, {
        action: 'getUserRoles',
        username,
      });

      return {
        success: false,
        error: handledError,
      };
    }
  }

  /**
   * Switch active role
   */
  async switchRole(username, designationId) {
    try {
      const response = await apiService.post('/roles/switch/', {
        username,
        designation_id: designationId,
      });

      // Clear related cache entries
      cacheService.delete(`user-roles:${username}`);
      cacheService.delete(`current-role:${username}`);

      return {
        success: true,
        data: response.data,
        message: 'Role switched successfully',
      };
    } catch (error) {
      const handledError = errorService.handle(error, {
        action: 'switchRole',
        username,
        designationId,
      });

      return {
        success: false,
        error: handledError,
      };
    }
  }

  /**
   * Get current active role
   */
  async getCurrentActiveRole(username) {
    const cacheKey = cacheService.constructor.generateKey('current-role', { username });

    try {
      const response = await apiService.post('/roles/active/', { username });
      const transformedData = roleTransformer(response.data);

      // Cache the result
      cacheService.set(cacheKey, transformedData);

      return {
        success: true,
        data: transformedData,
      };
    } catch (error) {
      const handledError = errorService.handle(error, {
        action: 'getCurrentActiveRole',
        username,
      });

      return {
        success: false,
        error: handledError,
      };
    }
  }

  /**
   * Get module access for role
   */
  async getModuleAccess(designation) {
    const cacheKey = cacheService.constructor.generateKey('module-access', { designation });

    try {
      const response = await apiService.get(`/get-module-access/?designation=${designation}`);

      // Cache the result
      cacheService.set(cacheKey, response.data);

      return {
        success: true,
        data: response.data,
      };
    } catch (error) {
      const handledError = errorService.handle(error, {
        action: 'getModuleAccess',
        designation,
      });

      return {
        success: false,
        error: handledError,
      };
    }
  }
}

// Export singleton instance
const roleService = new RoleService();
export default roleService;