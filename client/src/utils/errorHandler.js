/**
 * Enterprise-grade error handling utilities
 * Provides user-friendly error messages for all API errors
 * Enhanced with field-specific validation and detailed error analysis
 * Follows ERP industry standards for error messaging
 */

import {
  getStandardErrorMessage,
  parseBackendError,
  formatValidationErrorsForUser,
  FIELD_LABELS,
  NOTIFICATION_CONFIG
} from './erpMessages';

/**
 * Get user-friendly field label
 */
function getFieldLabel(fieldName) {
    return FIELD_LABELS[fieldName] || fieldName.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
}

/**
 * Get user-friendly error message from API error response
 * Enhanced to handle validation errors with field-specific messages
 * Now uses ERP-standard error templates for consistency
 */
export const getErrorMessage = (error) => {
    if (!error) return 'An unknown error occurred';

    // Use the new ERP standard error parser
    const parsedError = parseBackendError(error);

    // Format the error message for display
    if (parsedError.details && parsedError.details.length > 0) {
        // We have detailed validation errors
        let message = parsedError.message + '\n\n';

        parsedError.details.forEach((detail, index) => {
          if (detail.type === 'field') {
            message += `\n• ${detail.field}: ${detail.message}`;
          } else {
            message += `\n• ${detail.message}`;
          }
        });

        if (parsedError.suggestion) {
          message += `\n\n💡 ${parsedError.suggestion}`;
        }

        return message;
    }

    // Simple error message
    let message = parsedError.message;
    if (parsedError.suggestion) {
        message += `\n\n💡 ${parsedError.suggestion}`;
    }

    return message;
};

/**
 * Format validation errors into user-friendly messages
 */
function formatValidationErrors(validationErrors) {
    if (!validationErrors || typeof validationErrors !== 'object') {
        return 'Please correct the errors in the form and try again.';
    }

    let message = 'Please fix the following issues:\n\n';

    Object.entries(validationErrors).forEach(([field, error]) => {
        const fieldLabel = getFieldLabel(field);
        const errorText = Array.isArray(error) ? error.join(', ') : error;

        // Special handling for specific error types
        if (field === 'non_field_errors') {
            message += `• ${errorText}\n`;
        } else if (field === 'missing_fields') {
            const missingFields = Array.isArray(error) ? error : [error];
            message += `• Missing required fields: ${missingFields.map(f => getFieldLabel(f)).join(', ')}\n`;
        } else {
            message += `• ${fieldLabel}: ${errorText}\n`;
        }
    });

    return message;
}

/**
 * Format backend error responses
 */
function formatBackendError(data, status) {
    let message = data.message || data.error || '';

    // Add suggestion if available
    if (data.suggestion) {
        message += `\n\n💡 Suggestion: ${data.suggestion}`;
    }

    // Add helpful context based on status code
    if (status === 401) {
        message = 'Session expired. Please login again.';
    } else if (status === 403) {
        message = `${data.error || 'Access denied'} - You don't have permission to perform this action.`;
        if (data.suggestion) {
            message += `\n\n💡 ${data.suggestion}`;
        }
    } else if (status === 404) {
        message = `${data.error || 'Not found'} - The requested resource was not found.`;
    } else if (status === 409) {
        message = `${data.error || 'Conflict'} - This conflicts with existing data.`;
        if (data.suggestion) {
            message += `\n\n💡 ${data.suggestion}`;
        }
    } else if (status === 429) {
        message = 'Too many attempts. Please wait a few minutes before trying again.';
    } else if (status === 500) {
        message = data.error || 'Server error. Please try again later or contact support if the problem persists.';
        if (data.details) {
            message += `\n\nDetails: ${data.details}`;
        }
    }

    return message;
}

/**
 * Get user-friendly HTTP error messages
 */
function getHTTPErrorMessage(status) {
    const messages = {
        400: 'Invalid request. Please check your input and try again.',
        401: 'Authentication required. Please login.',
        403: 'Access denied. You don\'t have permission to perform this action.',
        404: 'Resource not found. It may have been deleted or moved.',
        405: 'Method not allowed. This action is not supported.',
        409: 'Conflict. This action conflicts with existing data.',
        413: 'File too large. Please upload a smaller file.',
        429: 'Too many requests. Please wait before trying again.',
        500: 'Server error. Our team has been notified. Please try again later.',
        502: 'Server unavailable. Please check your connection and try again.',
        503: 'Service unavailable. This feature may be under maintenance.',
        504: 'Gateway timeout. The request took too long to process.',
    };

    return messages[status] || `HTTP Error ${status}. Please try again later.`;
}

/**
 * Show error notification with user-friendly message
 * Enhanced to show validation errors in a structured format
 */
export const showErrorNotification = (error, title = 'Error') => {
    const message = getErrorMessage(error);

    // Use ERP standard configuration
    const config = {
        title,
        message,
        color: 'red',
        autoClose: 15000, // 15 seconds for detailed errors
        styles: {
            description: {
                whiteSpace: 'pre-line',
                fontSize: '0.9rem'
            }
        }
    };

    // Import showNotification dynamically
    import('@mantine/notifications').then(({ showNotification }) => {
        showNotification(config);
    }).catch(() => {
        console.error(`${title}: ${message}`);
    });
};

/**
 * Show success notification
 */
export const showSuccessNotification = (message, title = 'Success') => {
    // Use ERP standard success configuration
    const config = {
        title: `✅ ${title}`,
        message,
        color: 'green',
        autoClose: 5000, // 5 seconds for success messages
        styles: {
            description: {
                fontWeight: 500
            }
        }
    };

    // Import showNotification dynamically
    import('@mantine/notifications').then(({ showNotification }) => {
        showNotification(config);
    }).catch(() => {
        console.log(`${title}: ${message}`);
    });
};

/**
 * Get validation error for specific field
 * Enhanced to work with both old and new error formats
 */
export const getFieldError = (error, fieldName) => {
    if (!error || !error.response || !error.response.data) {
        return null;
    }

    const data = error.response.data;

    // Check for new validation_errors format
    if (data.validation_errors && typeof data.validation_errors === 'object') {
        return data.validation_errors[fieldName] || null;
    }

    // Check for field-specific errors
    if (data.errors && typeof data.errors === 'object') {
        return data.errors[fieldName] || null;
    }

    // Check for validation errors format
    if (data[fieldName]) {
        return data[fieldName];
    }

    return null;
};

/**
 * Get all field errors from an error response
 * Returns an object mapping field names to error messages
 */
export const getAllFieldErrors = (error) => {
    if (!error || !error.response || !error.response.data) {
        return {};
    }

    const data = error.response.data;
    const fieldErrors = {};

    // Handle new validation_errors format
    if (data.validation_errors && typeof data.validation_errors === 'object') {
        Object.entries(data.validation_errors).forEach(([field, error]) => {
            if (field !== 'non_field_errors' && field !== 'missing_fields') {
                fieldErrors[field] = Array.isArray(error) ? error.join(' ') : error;
            }
        });
        return fieldErrors;
    }

    // Handle old errors format
    if (data.errors && typeof data.errors === 'object') {
        Object.entries(data.errors).forEach(([field, error]) => {
            if (typeof error === 'string' || Array.isArray(error)) {
                fieldErrors[field] = Array.isArray(error) ? error.join(' ') : error;
            }
        });
    }

    return fieldErrors;
};

/**
 * Check if error has field-specific errors
 */
export const hasFieldErrors = (error) => {
    if (!error || !error.response || !error.response.data) {
        return false;
    }

    const data = error.response.data;
    return !!(data.validation_errors || data.errors);
};

/**
 * Format bulk import error summary
 */
export const formatBulkImportErrors = (errors) => {
    if (!errors || errors.length === 0) {
        return null;
    }

    // Group errors by type
    const errorGroups = {};
    errors.forEach(err => {
        const type = err.error || 'UNKNOWN';
        if (!errorGroups[type]) {
            errorGroups[type] = [];
        }
        errorGroups[type].push(err);
    });

    // Create summary
    let summary = `Error Summary:\n`;
    Object.entries(errorGroups).forEach(([type, errs]) => {
        summary += `\n• ${type.replace(/_/g, ' ')}: ${errs.length} occurrence(s)`;

        // Show first few examples
        const examples = errs.slice(0, 2);
        if (examples.length > 0) {
            summary += `\n  Examples:`;
            examples.forEach(err => {
                summary += `\n  - Row ${err.row}: ${err.message}`;
            });
            if (errs.length > 2) {
                summary += `\n  ... and ${errs.length - 2} more`;
            }
        }
    });

    return summary;
};

/**
 * Get help text for common errors
 */
export const getErrorHelp = (error) => {
    if (!error) return null;

    const help = {
        'Network Error': 'Check your internet connection and try again.',
        'Session expired': 'Your session has expired. Please log in again to continue.',
        'Permission denied': 'You don\'t have access to this feature. Please contact your administrator.',
        'File too large': 'The file you\'re trying to upload is too large. Maximum size is 5MB.',
        'Too many requests': 'You\'re making requests too quickly. Please wait a moment and try again.',
        'Server error': 'Our servers are experiencing issues. Please try again in a few minutes.',
        'Duplicate User': 'This user already exists in the system. Please check the roll number or use a different one.',
        'Invalid department': 'The selected department is not valid. Please refresh the page and try again.',
        'Validation failed': 'Please check all form fields and correct any errors before submitting.'
    };

    // Check error response data first
    if (error.response && error.response.data) {
        const data = error.response.data;
        if (data.suggestion) {
            return data.suggestion;
        }
        if (data.error && help[data.error]) {
            return help[data.error];
        }
    }

    // Fallback to message-based matching
    if (error.message) {
        for (const [key, value] of Object.entries(help)) {
            if (error.message.includes(key)) {
                return value;
            }
        }
    }

    return null;
};

/**
 * Enhanced error logging for debugging (development only)
 */
export const logError = (error, context = '') => {
    if (process.env.NODE_ENV === 'development') {
        console.group(`❌ Error${context ? ` in ${context}` : ''}`);
        console.error('Error:', error);
        console.error('Response:', error.response);
        console.error('Message:', error.message);

        // Log validation errors specifically
        if (error.response && error.response.data) {
            console.error('Validation Errors:', error.response.data.validation_errors || error.response.data.errors);
        }

        console.groupEnd();
    }
};

/**
 * Parse API error response for structured error handling
 * Returns an object with error type, message, and field-specific errors
 */
export const parseApiError = (error) => {
    const parsed = {
        type: 'unknown',
        message: 'An unexpected error occurred',
        fieldErrors: {},
        suggestion: null,
        status: null
    };

    if (!error) {
        return parsed;
    }

    // Set status code
    if (error.response) {
        parsed.status = error.response.status;
    }

    // Parse error data
    if (error.response && error.response.data) {
        const data = error.response.data;

        // Set message
        parsed.message = data.message || data.error || data.detail || parsed.message;

        // Set suggestion
        if (data.suggestion) {
            parsed.suggestion = data.suggestion;
        }

        // Set field errors
        if (data.validation_errors) {
            parsed.fieldErrors = data.validation_errors;
            parsed.type = 'validation';
        } else if (data.errors) {
            parsed.fieldErrors = data.errors;
            parsed.type = 'validation';
        }

        // Determine error type from status
        if (parsed.status === 401) {
            parsed.type = 'authentication';
        } else if (parsed.status === 403) {
            parsed.type = 'authorization';
        } else if (parsed.status === 404) {
            parsed.type = 'not_found';
        } else if (parsed.status === 409) {
            parsed.type = 'conflict';
        } else if (parsed.status >= 500) {
            parsed.type = 'server';
        }
    } else if (error.code === 'ERR_NETWORK') {
        parsed.type = 'network';
        parsed.message = 'Network error. Please check your connection.';
    }

    return parsed;
};

export default {
    getErrorMessage,
    showErrorNotification,
    showSuccessNotification,
    getFieldError,
    getAllFieldErrors,
    hasFieldErrors,
    formatBulkImportErrors,
    getErrorHelp,
    logError,
    parseApiError,
};
