/**
 * Main Services Export
 * Provides unified access to all services in the application
 */

// Re-export everything from the services module
export * from './base';
export * from './api';

// Default export for convenience
import { apiService, cacheService, errorService } from './base';
import { userService, roleService, departmentService } from './api';

export default {
  api: apiService,
  cache: cacheService,
  error: errorService,
  user: userService,
  role: roleService,
  department: departmentService,
};
