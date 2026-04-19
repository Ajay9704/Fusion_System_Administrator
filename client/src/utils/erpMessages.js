/**
 * Enterprise ERP Standard Error Messages and Notification System
 * Provides human-readable, actionable error messages for all scenarios
 */

/**
 * ERP-standard error message templates
 */
const ERROR_TEMPLATES = {
  // Authentication & Authorization
  AUTH_REQUIRED: {
    title: "Authentication Required",
    message: "Please log in to continue",
    suggestion: "Your session may have expired. Please log in again."
  },
  SESSION_EXPIRED: {
    title: "Session Expired",
    message: "Your session has expired due to inactivity",
    suggestion: "Please log in again to continue."
  },
  INVALID_CREDENTIALS: {
    title: "Invalid Login Credentials",
    message: "The username or password you entered is incorrect",
    suggestion: "Please check your credentials and try again. If you continue to have issues, contact the administrator."
  },
  ACCOUNT_LOCKED: {
    title: "Account Temporarily Locked",
    message: "Your account has been locked due to multiple failed login attempts",
    suggestion: "Please wait 15 minutes and try again, or contact the administrator to unlock your account."
  },
  PERMISSION_DENIED: {
    title: "Access Denied",
    message: "You don't have permission to perform this action",
    suggestion: "This action requires specific permissions. If you believe you should have access, please contact your administrator."
  },

  // User Management
  USER_EXISTS: {
    title: "User Already Exists",
    message: "A user with this information already exists in the system",
    suggestion: "Please verify the user details and try a different username or check if the user already exists."
  },
  USER_NOT_FOUND: {
    title: "User Not Found",
    message: "The requested user could not be found in the system",
    suggestion: "The user may have been deleted or archived. Please verify the user information."
  },
  MISSING_REQUIRED_FIELDS: {
    title: "Required Information Missing",
    message: "Please fill in all required fields marked with *",
    suggestion: "All required fields must be completed before proceeding."
  },
  INVALID_EMAIL_FORMAT: {
    title: "Invalid Email Address",
    message: "The email address format is not valid",
    suggestion: "Please enter a valid email address (e.g., user@example.com)."
  },
  INVALID_PHONE_FORMAT: {
    title: "Invalid Phone Number",
    message: "The phone number format is not valid",
    suggestion: "Please enter a valid phone number (e.g., +91 9876543210 or 9876543210)."
  },
  PASSWORD_TOO_WEAK: {
    title: "Password Not Strong Enough",
    message: "Your password must be stronger for security",
    suggestion: "Password must contain at least 8 characters, including uppercase, lowercase, numbers, and special characters."
  },

  // Programme & Department Constraints
  INVALID_PROGRAMME_DEPARTMENT: {
    title: "Invalid Programme-Department Combination",
    message: "The selected department is not offered in the chosen programme",
    suggestion: "Please select a different department or programme. Some departments are specific to certain programmes."
  },
  DEPARTMENT_NOT_AVAILABLE: {
    title: "Department Not Available",
    message: "The selected department is not available for this programme",
    suggestion: "Please choose from the available departments shown in the dropdown."
  },

  // Role Management
  ROLE_NOT_ELIGIBLE: {
    title: "Role Not Eligible",
    message: "This role cannot be assigned to the selected user type",
    suggestion: "Certain roles are restricted to specific user types (faculty, staff, or students)."
  },
  CONFLICTING_ROLES: {
    title: "Role Conflict Detected",
    message: "The selected roles cannot be assigned together",
    suggestion: "Please remove conflicting roles before proceeding. Some roles are mutually exclusive."
  },
  ROLE_HIERARCHY_VIOLATION: {
    title: "Role Hierarchy Violation",
    message: "This role assignment violates organizational hierarchy rules",
    suggestion: "Higher-level roles cannot be assigned alongside lower-level roles in the same category."
  },
  STUDENT_ROLE_RESTRICTION: {
    title: "Student Role Restriction",
    message: "Professional roles cannot be assigned to students",
    suggestion: "Students can only have student-specific roles. Professional roles are for faculty and staff."
  },

  // Data Operations
  INVALID_DATA_FORMAT: {
    title: "Invalid Data Format",
    message: "The data format is not valid for this field",
    suggestion: "Please check the format and try again. Refer to the field help text for the expected format."
  },
  DATA_TOO_LARGE: {
    title: "File Too Large",
    message: "The file you're trying to upload exceeds the maximum allowed size",
    suggestion: "Maximum file size is 5MB. Please compress your file or contact the administrator for assistance."
  },
  INVALID_FILE_TYPE: {
    title: "Invalid File Type",
    message: "Only CSV files are allowed for bulk upload",
    suggestion: "Please upload a CSV file. You can download a sample template to see the expected format."
  },
  BULK_UPLOAD_ERRORS: {
    title: "Bulk Upload Completed with Errors",
    message: "Some users could not be created due to validation errors",
    suggestion: "Please review the error details, correct the data in your CSV file, and try again."
  },

  // System Errors
  NETWORK_ERROR: {
    title: "Network Connection Error",
    message: "Unable to connect to the server",
    suggestion: "Please check your internet connection and try again. If the problem persists, contact IT support."
  },
  SERVER_ERROR: {
    title: "Server Error",
    message: "The server encountered an unexpected error",
    suggestion: "Our technical team has been notified. Please try again in a few minutes, or contact support if the problem continues."
  },
  DATABASE_ERROR: {
    title: "Database Error",
    message: "Unable to complete the operation due to a database issue",
    suggestion: "Please try again. If the problem persists, contact the database administrator."
  },
  MAINTENANCE_MODE: {
    title: "System Under Maintenance",
    message: "The system is currently under maintenance for upgrades",
    suggestion: "Please try again later. We apologize for the inconvenience."
  },

  // Validation Errors
  VALIDATION_FAILED: {
    title: "Validation Failed",
    message: "Please correct the highlighted errors and try again",
    suggestion: "Review the error details below and fix the issues before submitting."
  },
  DUPLICATE_ENTRY: {
    title: "Duplicate Entry",
    message: "This record already exists in the system",
    suggestion: "Please check for duplicates or use a unique identifier."
  },
  REFERENCE_ERROR: {
    title: "Referenced Data Not Found",
    message: "A related record could not be found",
    suggestion: "Please ensure all referenced records exist before proceeding."
  },

  // Archive & Restore
  USER_ARCHIVED: {
    title: "User Successfully Archived",
    message: "The user has been archived and is no longer active",
    suggestion: "Archived users can be restored from the Archive section."
  },
  USER_RESTORED: {
    title: "User Successfully Restored",
    message: "The user has been restored and is now active",
    suggestion: "The user can now access the system with their previous credentials."
  },

  // Emergency Access
  EMERGENCY_ACCESS_REQUESTED: {
    title: "Emergency Access Requested",
    message: "An emergency access request has been submitted",
    suggestion: "The request will be reviewed by an administrator. You'll be notified once approved."
  },
  EMERGENCY_ACCESS_APPROVED: {
    title: "Emergency Access Approved",
    message: "Emergency access has been granted",
    suggestion: "You can now perform the required actions. All activities are being logged."
  },
  EMERGENCY_ACCESS_REVOKED: {
    title: "Emergency Access Revoked",
    message: "Emergency access has been revoked",
    suggestion: "Your emergency access period has ended. Regular access permissions have been restored."
  },

  // Import/Export
  EXPORT_SUCCESSFUL: {
    title: "Data Export Successful",
    message: "Your data has been exported successfully",
    suggestion: "The file has been downloaded to your computer."
  },
  IMPORT_SUCCESSFUL: {
    title: "Data Import Successful",
    message: "Your data has been imported successfully",
    suggestion: "Please review the import summary to see what was created."
  },
  PARTIAL_IMPORT_SUCCESS: {
    title: "Partial Import Completed",
    message: "Some records were imported successfully, but others failed",
    suggestion: "Please review the error details and re-import the failed records."
  }
};

/**
 * Get standardized error message from error code or template
 */
export const getStandardErrorMessage = (errorKey, customDetails = {}) => {
  const template = ERROR_TEMPLATES[errorKey] || {
    title: 'Error',
    message: 'An unexpected error occurred',
    suggestion: 'Please try again or contact support if the problem persists.'
  };

  // Add custom details to the message
  let message = template.message;
  if (customDetails.fieldName) {
    message = message.replace('this field', customDetails.fieldName);
  }
  if (customDetails.value) {
    message = message.replace('{value}', customDetails.value);
  }
  if (customDetails.count) {
    message = message.replace('{count}', customDetails.count);
  }

  return {
    title: template.title,
    message,
    suggestion: template.suggestion,
    errorKey: errorKey
  };
};

/**
 * ERP-standard notification configuration
 */
export const NOTIFICATION_CONFIG = {
  // Success notifications
  success: {
    color: 'green',
    autoClose: 5000, // 5 seconds
    icon: '✅',
    position: 'top-right'
  },

  // Error notifications
  error: {
    color: 'red',
    autoClose: 15000, // 15 seconds for detailed errors
    icon: '❌',
    position: 'top-right'
  },

  // Warning notifications
  warning: {
    color: 'orange',
    autoClose: 10000, // 10 seconds
    icon: '⚠️',
    position: 'top-right'
  },

  // Info notifications
  info: {
    color: 'blue',
    autoClose: 7000, // 7 seconds
    icon: 'ℹ️',
    position: 'top-right'
  },

  // Critical notifications (require attention)
  critical: {
    color: 'red',
    autoClose: 30000, // 30 seconds
    icon: '🚨',
    position: 'top-center',
    withCloseButton: true
  }
};

/**
 * Show ERP-standard notification
 */
export const showStandardNotification = (type, config) => {
  const notificationConfig = NOTIFICATION_CONFIG[type] || NOTIFICATION_CONFIG.info;

  return {
    ...notificationConfig,
    ...config,
    title: config.title || notificationConfig.icon + ' ' + (notificationConfig.title || 'Notification'),
    message: config.message,
    color: config.color || notificationConfig.color,
    autoClose: config.autoClose || notificationConfig.autoClose
  };
};

/**
 * Get user-friendly field labels for error messages
 */
export const FIELD_LABELS = {
  username: 'Username',
  roll_number: 'Roll Number',
  first_name: 'First Name',
  last_name: 'Last Name',
  email: 'Email Address',
  personal_email: 'Personal Email',
  phone: 'Phone Number',
  date_of_birth: 'Date of Birth',
  sex: 'Gender',
  programme: 'Programme',
  batch: 'Batch Year',
  department: 'Department',
  designation: 'Designation',
  category: 'Category',
  address: 'Address',
  title: 'Title'
};

/**
 * Format validation errors for user display
 */
export const formatValidationErrorsForUser = (validationErrors) => {
  if (!validationErrors || typeof validationErrors !== 'object') {
    return null;
  }

  const formattedErrors = [];
  const fieldLabels = FIELD_LABELS;

  Object.entries(validationErrors).forEach(([field, error]) => {
    if (field === 'non_field_errors' || field === 'missing_fields') {
      // These are general errors
      if (Array.isArray(error)) {
        formattedErrors.push({ type: 'general', message: error.join(', ') });
      } else {
        formattedErrors.push({ type: 'general', message: String(error) });
      }
    } else {
      // Field-specific errors
      const fieldLabel = fieldLabels[field] || field.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
      const errorMessage = Array.isArray(error) ? error.join(', ') : String(error);
      formattedErrors.push({
        type: 'field',
        field: fieldLabel,
        message: errorMessage
      });
    }
  });

  return formattedErrors;
};

/**
 * Get human-readable action status for audit logs
 */
export const getActionStatusDisplay = (status) => {
  const statusConfig = {
    'SUCCESS': { label: 'Completed', color: 'green', icon: '✅' },
    'FAILED': { label: 'Failed', color: 'red', icon: '❌' },
    'PENDING': { label: 'In Progress', color: 'blue', icon: '⏳' },
    'WARNING': { label: 'Warning', color: 'orange', icon: '⚠️' }
  };

  return statusConfig[status] || statusConfig['PENDING'];
};

/**
 * Parse backend error and return standardized error message
 */
export const parseBackendError = (error) => {
  if (!error || !error.response) {
    return getStandardErrorMessage('NETWORK_ERROR');
  }

  const { data, status } = error.response;

  // Handle specific error codes
  if (status === 401) {
    return getStandardErrorMessage('SESSION_EXPIRED');
  }

  if (status === 403) {
    return getStandardErrorMessage('PERMISSION_DENIED');
  }

  if (status === 404) {
    return getStandardErrorMessage('USER_NOT_FOUND');
  }

  if (status === 409) {
    return getStandardErrorMessage('DUPLICATE_ENTRY');
  }

  if (status === 413) {
    return getStandardErrorMessage('DATA_TOO_LARGE');
  }

  if (status === 422) {
    return getStandardErrorMessage('VALIDATION_FAILED');
  }

  // Handle backend error responses
  if (data) {
    if (data.error === 'Duplicate User') {
      return getStandardErrorMessage('USER_EXISTS');
    }

    if (data.error === 'Validation failed' || data.validation_errors) {
      const customDetails = {};
      if (data.validation_errors) {
        const formattedErrors = formatValidationErrorsForUser(data.validation_errors);
        return {
          ...getStandardErrorMessage('VALIDATION_FAILED'),
          details: formattedErrors
        };
      }
    }

    if (data.message) {
      return {
        title: data.error || 'Error',
        message: data.message,
        suggestion: data.suggestion || 'Please try again.',
        details: data.details
      };
    }
  }

  // Default fallback
  return getStandardErrorMessage('SERVER_ERROR');
};

export default {
  ERROR_TEMPLATES,
  getStandardErrorMessage,
  showStandardNotification,
  formatValidationErrorsForUser,
  getActionStatusDisplay,
  parseBackendError,
  FIELD_LABELS,
  NOTIFICATION_CONFIG
};