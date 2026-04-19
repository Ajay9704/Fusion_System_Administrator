/**
 * Console utility for development-only logging
 * In production, all console methods are no-ops to prevent technical details from leaking
 */

const isDevelopment = import.meta.env.MODE === 'development';

const consoleUtils = {
  log: isDevelopment ? console.log : () => {},
  error: isDevelopment ? console.error : () => {},
  warn: isDevelopment ? console.warn : () => {},
  info: isDevelopment ? console.info : () => {},
  debug: isDevelopment ? console.debug : () => {},

  // Grouping utilities
  group: isDevelopment ? console.group : () => {},
  groupEnd: isDevelopment ? console.groupEnd : () => {},
  groupCollapsed: isDevelopment ? console.groupCollapsed : () => {},

  // Enhanced logging with context
  logWithContext: (message, context = {}) => {
    if (isDevelopment) {
      console.log(`🔍 ${message}`, context);
    }
  },

  errorWithContext: (message, error = {}) => {
    if (isDevelopment) {
      console.error(`❌ ${message}`, error);
    }
  },

  warnWithContext: (message, context = {}) => {
    if (isDevelopment) {
      console.warn(`⚠️ ${message}`, context);
    }
  },

  // Performance logging
  logPerformance: (operation, startTime) => {
    if (isDevelopment) {
      const duration = performance.now() - startTime;
      console.log(`⏱️ ${operation} completed in ${duration.toFixed(2)}ms`);
    }
  },

  // API logging (detailed in development only)
  logApiError: (error) => {
    if (isDevelopment) {
      console.error('❌ API Error Details:', {
        url: error.config?.url,
        method: error.config?.method,
        status: error.response?.status,
        statusText: error.response?.statusText,
        data: error.response?.data,
        message: error.message,
      });
    }
  },

  logApiSuccess: (url, status) => {
    if (isDevelopment) {
      console.log(`✅ API Success: ${url} (${status})`);
    }
  }
};

export default consoleUtils;
