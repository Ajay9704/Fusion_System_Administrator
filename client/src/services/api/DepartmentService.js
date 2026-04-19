/**
 * Enterprise Department Service
 * Handles all department related operations
 */

import apiService from '../base/ApiService';
import cacheService from '../base/CacheService';
import errorService from '../base/ErrorService';
import { departmentTransformer, departmentListTransformer } from '../../utils/transformers/departmentTransformers';

class DepartmentService {
  /**
   * Get all academic departments
   */
  async getAllAcademicDepartments(useCache = true) {
    const cacheKey = 'departments:academic';

    // Check cache first
    if (useCache && cacheService.has(cacheKey)) {
      return {
        success: true,
        data: cacheService.get(cacheKey),
        cached: true,
      };
    }

    try {
      const response = await apiService.get('/departments/');
      const transformedData = departmentListTransformer(response.data);

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
        action: 'getAllAcademicDepartments',
      });

      return {
        success: false,
        error: handledError,
      };
    }
  }

  /**
   * Get all departments (including administrative)
   */
  async getAllDepartments(useCache = true) {
    const cacheKey = 'departments:all';

    // Check cache first
    if (useCache && cacheService.has(cacheKey)) {
      return {
        success: true,
        data: cacheService.get(cacheKey),
        cached: true,
      };
    }

    try {
      const response = await apiService.get('/departments/all/');
      const transformedData = departmentListTransformer(response.data);

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
        action: 'getAllDepartments',
      });

      return {
        success: false,
        error: handledError,
      };
    }
  }

  /**
   * Get departments by programme
   */
  async getDepartmentsByProgramme(programme) {
    const cacheKey = cacheService.constructor.generateKey('departments-by-programme', { programme });

    try {
      const response = await apiService.get(`/departments/by-programme/?programme=${programme}`);
      const transformedData = departmentListTransformer(response.data);

      // Cache the result
      cacheService.set(cacheKey, transformedData);

      return {
        success: true,
        data: transformedData,
      };
    } catch (error) {
      const handledError = errorService.handle(error, {
        action: 'getDepartmentsByProgramme',
        programme,
      });

      return {
        success: false,
        error: handledError,
      };
    }
  }

  /**
   * Get departments with hierarchy
   */
  async getDepartmentsWithHierarchy() {
    const cacheKey = 'departments:hierarchy';

    try {
      const response = await apiService.get('/departments/hierarchy/');

      // Cache the result
      cacheService.set(cacheKey, response.data);

      return {
        success: true,
        data: response.data,
      };
    } catch (error) {
      const handledError = errorService.handle(error, {
        action: 'getDepartmentsWithHierarchy',
      });

      return {
        success: false,
        error: handledError,
      };
    }
  }

  /**
   * Get department tree structure
   */
  async getDepartmentTree() {
    const cacheKey = 'departments:tree';

    try {
      const response = await apiService.get('/departments/tree/');

      // Cache the result
      cacheService.set(cacheKey, response.data);

      return {
        success: true,
        data: response.data,
      };
    } catch (error) {
      const handledError = errorService.handle(error, {
        action: 'getDepartmentTree',
      });

      return {
        success: false,
        error: handledError,
      };
    }
  }

  /**
   * Create new department
   */
  async createDepartment(departmentData) {
    try {
      const response = await apiService.post('/departments/create/', departmentData);

      // Clear departments cache
      cacheService.delete('departments:*');

      return {
        success: true,
        data: departmentTransformer(response.data),
        message: 'Department created successfully',
      };
    } catch (error) {
      const handledError = errorService.handle(error, {
        action: 'createDepartment',
      });

      return {
        success: false,
        error: handledError,
      };
    }
  }

  /**
   * Update department
   */
  async updateDepartment(departmentId, departmentData) {
    try {
      const response = await apiService.put(`/departments/${departmentId}/update/`, departmentData);

      // Clear departments cache
      cacheService.delete('departments:*');

      return {
        success: true,
        data: departmentTransformer(response.data),
        message: 'Department updated successfully',
      };
    } catch (error) {
      const handledError = errorService.handle(error, {
        action: 'updateDepartment',
        departmentId,
      });

      return {
        success: false,
        error: handledError,
      };
    }
  }

  /**
   * Delete department
   */
  async deleteDepartment(departmentId) {
    try {
      const response = await apiService.delete(`/departments/${departmentId}/delete/`);

      // Clear departments cache
      cacheService.delete('departments:*');

      return {
        success: true,
        data: response.data,
        message: 'Department deleted successfully',
      };
    } catch (error) {
      const handledError = errorService.handle(error, {
        action: 'deleteDepartment',
        departmentId,
      });

      return {
        success: false,
        error: handledError,
      };
    }
  }
}

// Export singleton instance
const departmentService = new DepartmentService();
export default departmentService;