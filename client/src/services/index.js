/**
 * Enterprise Services Index
 * Central export point for all services with backward compatibility
 */

// Legacy exports (for backward compatibility)
export { default as apiClient } from './api';
export * from './userService';
export * from './roleService';
export * from './mailService';
export { default as authService } from './authServices';

// New enterprise services
export * from './base';
export * from './api';

// Unified service object
import { apiService, cacheService, errorService } from './base';
import { userService, roleService, departmentService } from './api';

export default {
  // Legacy naming (backward compatibility)
  apiClient: apiService,
  cache: cacheService,
  error: errorService,
  // New enterprise services
  api: apiService,
  user: userService,
  role: roleService,
  department: departmentService,
};
