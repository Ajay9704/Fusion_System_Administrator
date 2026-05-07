"""
Centralized Error Handling System
Provides standardized, human-friendly error messages for system administrators.
"""

from rest_framework import status


class ErrorCodes:
    """Standardized error codes for tracking and debugging"""
    # Authentication Errors (AUTH_*)
    AUTH_INVALID_CREDENTIALS = "AUTH_001"
    AUTH_ACCOUNT_DISABLED = "AUTH_002"
    AUTH_TOKEN_EXPIRED = "AUTH_003"
    AUTH_TOKEN_INVALID = "AUTH_004"
    AUTH_UNAUTHORIZED = "AUTH_005"
    
    # Validation Errors (VAL_*)
    VAL_MISSING_REQUIRED_FIELD = "VAL_001"
    VAL_INVALID_EMAIL_FORMAT = "VAL_002"
    VAL_INVALID_DATA_FORMAT = "VAL_003"
    VAL_DUPLICATE_ENTRY = "VAL_004"
    VAL_INVALID_ROLE = "VAL_005"
    VAL_INVALID_DEPARTMENT = "VAL_006"
    
    # Database Errors (DB_*)
    DB_RECORD_NOT_FOUND = "DB_001"
    DB_DUPLICATE_KEY = "DB_002"
    DB_CONSTRAINT_VIOLATION = "DB_003"
    DB_CONNECTION_ERROR = "DB_004"
    
    # System Errors (SYS_*)
    SYS_INTERNAL_ERROR = "SYS_001"
    SYS_SERVICE_UNAVAILABLE = "SYS_002"
    SYS_EXTERNAL_SERVICE_ERROR = "SYS_003"
    
    # Business Logic Errors (BIZ_*)
    BIZ_INVALID_OPERATION = "BIZ_001"
    BIZ_ROLE_CONFLICT = "BIZ_002"
    BIZ_INVALID_STATE_TRANSITION = "BIZ_003"


class ErrorMessageBuilder:
    """Builds human-friendly error messages with actionable solutions"""
    
    @staticmethod
    def authentication_error(code, message, solution=None):
        return {
            "error": {
                "code": code,
                "type": "Authentication Error",
                "message": message,
                "solution": solution or "Please verify your credentials and try again.",
                "severity": "HIGH"
            }
        }
    
    @staticmethod
    def validation_error(code, message, field=None, solution=None):
        error = {
            "error": {
                "code": code,
                "type": "Validation Error",
                "message": message,
                "solution": solution or "Please check the input data and correct the errors.",
                "severity": "MEDIUM"
            }
        }
        if field:
            error["error"]["field"] = field
        return error
    
    @staticmethod
    def database_error(code, message, solution=None):
        return {
            "error": {
                "code": code,
                "type": "Database Error",
                "message": message,
                "solution": solution or "Please contact system administrator if this issue persists.",
                "severity": "HIGH"
            }
        }
    
    @staticmethod
    def system_error(code, message, solution=None):
        return {
            "error": {
                "code": code,
                "type": "System Error",
                "message": message,
                "solution": solution or "Please contact system administrator immediately.",
                "severity": "CRITICAL"
            }
        }
    
    @staticmethod
    def business_error(code, message, solution=None):
        return {
            "error": {
                "code": code,
                "type": "Business Rule Violation",
                "message": message,
                "solution": solution or "Please review the business rules and try again.",
                "severity": "MEDIUM"
            }
        }


class AuditMessageBuilder:
    """Builds human-friendly audit log descriptions"""
    
    @staticmethod
    def user_created(username, user_type):
        return f"New {user_type} account created for user '{username}'. Credentials sent to registered email."
    
    @staticmethod
    def user_updated(username, changes):
        return f"User '{username}' profile updated. Changes: {', '.join(changes)}."
    
    @staticmethod
    def user_deleted(username):
        return f"User '{username}' account deleted from system."
    
    @staticmethod
    def password_reset(username, reset_by):
        return f"Password reset for user '{username}' by {reset_by}."
    
    @staticmethod
    def role_assigned(username, role):
        return f"Role '{role}' assigned to user '{username}'."
    
    @staticmethod
    def role_removed(username, role):
        return f"Role '{role}' removed from user '{username}'."
    
    @staticmethod
    def login_success(username):
        return f"User '{username}' logged in successfully."
    
    @staticmethod
    def login_failed(username, reason):
        return f"Failed login attempt for '{username}'. Reason: {reason}."
    
    @staticmethod
    def bulk_operation(operation_type, success_count, failed_count):
        return f"Bulk {operation_type} completed. Success: {success_count}, Failed: {failed_count}."


class LogMessageBuilder:
    """Builds standardized console log messages for developers"""
    
    @staticmethod
    def info(component, message):
        return f"[INFO] [{component}] {message}"
    
    @staticmethod
    def warning(component, message, action_required=None):
        msg = f"[WARNING] [{component}] {message}"
        if action_required:
            msg += f" | Action Required: {action_required}"
        return msg
    
    @staticmethod
    def error(component, message, exception=None):
        msg = f"[ERROR] [{component}] {message}"
        if exception:
            msg += f" | Exception: {str(exception)}"
        return msg
    
    @staticmethod
    def success(component, message):
        return f"[SUCCESS] [{component}] {message}"
