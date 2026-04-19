/**
 * Enterprise User Service
 * Handles all user-related API operations with enterprise-grade error handling
 */

import apiService from '../base/ApiService';
import cacheService from '../base/CacheService';
import errorService from '../base/ErrorService';
import { userTransformer, userListTransformer } from '../../utils/transformers/userTransformers';

class UserService {
  /**
   * Create a new student
   */
  async createStudent(studentData) {
    try {
      const response = await apiService.post('/users/add-student/', studentData);

      // Clear related cache entries
      cacheService.delete('users:*');
      cacheService.delete('students:*');

      return {
        success: true,
        data: userTransformer(response.data),
        message: 'Student created successfully',
      };
    } catch (error) {
      const handledError = errorService.handle(error, {
        action: 'createStudent',
        entityType: 'student',
      });

      return {
        success: false,
        error: handledError,
      };
    }
  }

  /**
   * Create a new faculty member
   */
  async createFaculty(facultyData) {
    try {
      const response = await apiService.post('/users/add-faculty/', facultyData);

      // Clear related cache entries
      cacheService.delete('users:*');
      cacheService.delete('faculty:*');

      return {
        success: true,
        data: userTransformer(response.data),
        message: 'Faculty created successfully',
      };
    } catch (error) {
      const handledError = errorService.handle(error, {
        action: 'createFaculty',
        entityType: 'faculty',
      });

      return {
        success: false,
        error: handledError,
      };
    }
  }

  /**
   * Create a new staff member
   */
  async createStaff(staffData) {
    try {
      const response = await apiService.post('/users/add-staff/', staffData);

      // Clear related cache entries
      cacheService.delete('users:*');
      cacheService.delete('staff:*');

      return {
        success: true,
        data: userTransformer(response.data),
        message: 'Staff created successfully',
      };
    } catch (error) {
      const handledError = errorService.handle(error, {
        action: 'createStaff',
        entityType: 'staff',
      });

      return {
        success: false,
        error: handledError,
      };
    }
  }

  /**
   * Reset user password
   */
  async resetPassword(resetData) {
    try {
      const response = await apiService.post('/users/reset_password/', resetData);

      return {
        success: true,
        data: response.data,
        message: 'Password reset successfully',
      };
    } catch (error) {
      const handledError = errorService.handle(error, {
        action: 'resetPassword',
      });

      return {
        success: false,
        error: handledError,
      };
    }
  }

  /**
   * Get users by type with caching
   */
  async getUsersByType(type, useCache = true) {
    const cacheKey = cacheService.constructor.generateKey('users-by-type', { type });

    // Check cache first
    if (useCache && cacheService.has(cacheKey)) {
      return {
        success: true,
        data: cacheService.get(cacheKey),
        cached: true,
      };
    }

    try {
      const response = await apiService.get(`/users?type=${type}`);
      const transformedData = userListTransformer(response.data);

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
        action: 'getUsersByType',
        type,
      });

      return {
        success: false,
        error: handledError,
      };
    }
  }

  /**
   * Get user by username
   */
  async getUserByUsername(username) {
    const cacheKey = cacheService.constructor.generateKey('user-by-username', { username });

    try {
      const response = await apiService.get(`/get-user-roles-by-username/?username=${username}`);
      const transformedData = userTransformer(response.data);

      // Cache the result
      cacheService.set(cacheKey, transformedData);

      return {
        success: true,
        data: transformedData,
      };
    } catch (error) {
      const handledError = errorService.handle(error, {
        action: 'getUserByUsername',
        username,
      });

      return {
        success: false,
        error: handledError,
      };
    }
  }

  /**
   * Archive user
   */
  async archiveUser(username) {
    try {
      const response = await apiService.put(`/users/${username}/archive/`);

      // Clear related cache entries
      cacheService.delete('users:*');
      cacheService.delete(`user-by-username:${username}`);

      return {
        success: true,
        data: response.data,
        message: 'User archived successfully',
      };
    } catch (error) {
      const handledError = errorService.handle(error, {
        action: 'archiveUser',
        username,
      });

      return {
        success: false,
        error: handledError,
      };
    }
  }

  /**
   * Restore user
   */
  async restoreUser(username) {
    try {
      const response = await apiService.put(`/users/${username}/restore/`);

      // Clear related cache entries
      cacheService.delete('users:*');
      cacheService.delete(`user-by-username:${username}`);

      return {
        success: true,
        data: response.data,
        message: 'User restored successfully',
      };
    } catch (error) {
      const handledError = errorService.handle(error, {
        action: 'restoreUser',
        username,
      });

      return {
        success: false,
        error: handledError,
      };
    }
  }

  /**
   * Bulk upload users with progress tracking
   */
  async bulkUploadUsers(formData, onProgress) {
    try {
      const response = await apiService.upload('/users/import/', formData, onProgress);

      // Clear related cache entries
      cacheService.delete('users:*');

      return {
        success: true,
        data: response.data,
        message: 'Users uploaded successfully',
      };
    } catch (error) {
      const handledError = errorService.handle(error, {
        action: 'bulkUploadUsers',
      });

      return {
        success: false,
        error: handledError,
      };
    }
  }

  /**
   * Download sample CSV
   */
  async downloadSampleCSV() {
    try {
      await apiService.download('/download-sample-csv', 'sample_users.csv');

      return {
        success: true,
        message: 'Sample CSV downloaded successfully',
      };
    } catch (error) {
      const handledError = errorService.handle(error, {
        action: 'downloadSampleCSV',
      });

      return {
        success: false,
        error: handledError,
      };
    }
  }
}

// Export singleton instance
const userService = new UserService();
export default userService;