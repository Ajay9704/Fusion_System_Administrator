/**
 * Enterprise Error Service
 * Centralized error handling, logging, and user notification
 */

class ErrorService {
  constructor() {
    this.errorHandlers = new Map();
    this.setupDefaultHandlers();
  }

  setupDefaultHandlers() {
    // Network error handler
    this.registerHandler('NETWORK_ERROR', (error) => ({
      message: 'Unable to connect to server. Please check your internet connection.',
      userMessage: 'Network connection failed. Please try again.',
      severity: 'error',
      actionRequired: true,
    }));

    // Authentication error handler
    this.registerHandler('AUTH_ERROR', (error) => ({
      message: 'Authentication failed. Please login again.',
      userMessage: 'Session expired. Please login to continue.',
      severity: 'warning',
      actionRequired: true,
      action: () => {
        localStorage.clear();
        window.location.href = '/login';
      },
    }));

    // Permission error handler
    this.registerHandler('PERMISSION_ERROR', (error) => ({
      message: 'You do not have permission to perform this action.',
      userMessage: 'Access denied. You do not have sufficient permissions.',
      severity: 'error',
      actionRequired: false,
    }));

    // Validation error handler
    this.registerHandler('VALIDATION_ERROR', (error) => ({
      message: 'Invalid data provided.',
      userMessage: error.details?.message || 'Please check your input and try again.',
      severity: 'warning',
      actionRequired: true,
      details: error.details,
    }));

    // Server error handler
    this.registerHandler('SERVER_ERROR', (error) => ({
      message: 'Server error occurred.',
      userMessage: 'Something went wrong on our end. Please try again later.',
      severity: 'error',
      actionRequired: false,
    }));
  }

  registerHandler(errorType, handler) {
    this.errorHandlers.set(errorType, handler);
  }

  classifyError(error) {
    if (error.code === 'NETWORK_ERROR') {
      return 'NETWORK_ERROR';
    }

    if (error.status === 401) {
      return 'AUTH_ERROR';
    }

    if (error.status === 403) {
      return 'PERMISSION_ERROR';
    }

    if (error.status === 400) {
      return 'VALIDATION_ERROR';
    }

    if (error.status >= 500) {
      return 'SERVER_ERROR';
    }

    return 'UNKNOWN_ERROR';
  }

  handle(error, context = {}) {
    const errorType = this.classifyError(error);
    const handler = this.errorHandlers.get(errorType);

    if (handler) {
      const errorInfo = handler(error);

      // Log error for monitoring
      this.logError(error, errorType, context);

      // Execute action if required
      if (errorInfo.actionRequired && errorInfo.action) {
        errorInfo.action();
      }

      return {
        ...errorInfo,
        type: errorType,
        timestamp: new Date().toISOString(),
        context,
      };
    }

    // Default error handling
    return {
      type: 'UNKNOWN_ERROR',
      message: error.message || 'An unknown error occurred',
      userMessage: 'Something went wrong. Please try again.',
      severity: 'error',
      actionRequired: false,
      timestamp: new Date().toISOString(),
      context,
    };
  }

  logError(error, errorType, context) {
    // In production, send to error tracking service
    const errorLog = {
      type: errorType,
      message: error.message,
      status: error.status,
      stack: error.stack,
      context: {
        ...context,
        url: window.location.href,
        userAgent: navigator.userAgent,
        timestamp: new Date().toISOString(),
      },
    };

    console.error('[ErrorService]', errorLog);

    // In development, show detailed error info
    if (import.meta.env.DEV) {
      console.error('Error Details:', {
        original: error,
        handled: errorLog,
      });
    }
  }

  // Convenience methods for specific error types
  isNetworkError(error) {
    return this.classifyError(error) === 'NETWORK_ERROR';
  }

  isAuthError(error) {
    return this.classifyError(error) === 'AUTH_ERROR';
  }

  isPermissionError(error) {
    return this.classifyError(error) === 'PERMISSION_ERROR';
  }

  isValidationError(error) {
    return this.classifyError(error) === 'VALIDATION_ERROR';
  }

  isServerError(error) {
    return this.classifyError(error) === 'SERVER_ERROR';
  }
}

// Export singleton instance
const errorService = new ErrorService();
export default errorService;
