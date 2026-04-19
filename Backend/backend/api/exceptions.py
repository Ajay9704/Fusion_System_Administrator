"""
Custom exception handlers for System Admin module
Provides user-friendly error messages and proper error logging
"""
import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings

# Configure logger
logger = logging.getLogger('system_admin')


def custom_exception_handler(exc, context):
    """
    Custom exception handler that returns user-friendly error messages
    Error Handling: Provides structured error responses instead of raw stack traces
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)

    # Get the request and view from context
    request = context.get('request')
    view = context.get('view')
    
    # Log the error for debugging
    if response is None:
        logger.error(f"Unhandled exception in {view.__class__.__name__}: {str(exc)}", exc_info=True)
        return Response(
            {
                'error': 'Internal Server Error',
                'message': 'An unexpected error occurred. Please contact the administrator.',
                'status_code': status.HTTP_500_INTERNAL_SERVER_ERROR
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    # Customize the error response based on exception type
    if response is not None:
        error_data = {
            'error': get_error_title(response.status_code),
            'message': format_error_message(response.data, response.status_code),
            'status_code': response.status_code
        }
        
        # Add validation errors if present
        if response.status_code == status.HTTP_400_BAD_REQUEST:
            if isinstance(response.data, dict):
                error_data['details'] = format_validation_errors(response.data)
        
        # Log client errors at warning level, server errors at error level
        if response.status_code >= 500:
            logger.error(f"Server error in {view.__class__.__name__}: {error_data['message']}")
        else:
            logger.warning(f"Client error in {view.__class__.__name__}: {error_data['message']}")
        
        response.data = error_data
    
    return response


def get_error_title(status_code):
    """Get a user-friendly error title based on status code"""
    error_titles = {
        400: 'Bad Request',
        401: 'Authentication Required',
        403: 'Permission Denied',
        404: 'Resource Not Found',
        405: 'Method Not Allowed',
        409: 'Conflict',
        429: 'Too Many Requests',
        500: 'Internal Server Error',
        502: 'Bad Gateway',
        503: 'Service Unavailable',
    }
    return error_titles.get(status_code, 'Error')


def format_error_message(data, status_code):
    """Format error message based on status code"""
    if status_code == status.HTTP_400_BAD_REQUEST:
        if isinstance(data, dict):
            if 'error' in data:
                return data['error']
            return 'Invalid request. Please check your input and try again.'
        return str(data)
    
    elif status_code == status.HTTP_401_UNAUTHORIZED:
        return 'Authentication credentials were not provided or are invalid.'
    
    elif status_code == status.HTTP_403_FORBIDDEN:
        return 'You do not have permission to perform this action.'
    
    elif status_code == status.HTTP_404_NOT_FOUND:
        return 'The requested resource was not found.'
    
    elif status_code == status.HTTP_409_CONFLICT:
        if isinstance(data, dict) and 'error' in data:
            return data['error']
        return 'This operation conflicts with existing data.'
    
    elif status_code == status.HTTP_429_TOO_MANY_REQUESTS:
        return 'Too many requests. Please try again later.'
    
    elif status_code >= 500:
        return 'A server error occurred. Please contact the administrator.'
    
    return str(data)


def format_validation_errors(data):
    """Format validation errors into a user-friendly structure"""
    if not isinstance(data, dict):
        return None
    
    errors = {}
    for field, messages in data.items():
        if field in ['error', 'message', 'status_code', 'details']:
            continue
        
        if isinstance(messages, list):
            errors[field] = ' '.join(str(msg) for msg in messages)
        elif isinstance(messages, dict):
            # Nested serializer errors
            errors[field] = format_validation_errors(messages)
        else:
            errors[field] = str(messages)
    
    return errors if errors else None


class BusinessRuleViolationError(Exception):
    """Custom exception for business rule violations"""
    def __init__(self, message, rule_id=None):
        self.message = message
        self.rule_id = rule_id
        super().__init__(self.message)


class DataIntegrityError(Exception):
    """Custom exception for data integrity violations"""
    def __init__(self, message, details=None):
        self.message = message
        self.details = details
        super().__init__(self.message)


class SecurityViolationError(Exception):
    """Custom exception for security violations"""
    def __init__(self, message, violation_type=None):
        self.message = message
        self.violation_type = violation_type
        super().__init__(self.message)
