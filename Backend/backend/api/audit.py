"""
Audit logging decorator and helper functions for tracking admin actions.
Enhanced with human-readable descriptions following ERP standards.
"""
from functools import wraps
from django.utils import timezone
from .models import AuditLog


# ERP-standard action descriptions mapping
ACTION_DESCRIPTIONS = {
    # User Management Actions
    'CREATE_STUDENT': 'Student Created',
    'UPDATE_STUDENT': 'Student Information Updated',
    'DELETE_STUDENT': 'Student Deleted',
    'ARCHIVE_STUDENT': 'Student Archived',
    'RESTORE_STUDENT': 'Student Account Restored',
    'RESET_PASSWORD': 'Password Reset Initiated',
    'CHANGE_PASSWORD': 'Password Changed',

    'CREATE_FACULTY': 'Faculty Member Created',
    'UPDATE_FACULTY': 'Faculty Information Updated',
    'DELETE_FACULTY': 'Faculty Member Deleted',
    'ARCHIVE_FACULTY': 'Faculty Archived',
    'RESTORE_FACULTY': 'Faculty Account Restored',

    'CREATE_STAFF': 'Staff Member Created',
    'UPDATE_STAFF': 'Staff Information Updated',
    'DELETE_STAFF': 'Staff Member Deleted',
    'ARCHIVE_STAFF': 'Staff Archived',
    'RESTORE_STAFF': 'Staff Account Restored',

    # Role Management Actions
    'CREATE_ROLE': 'Role Created',
    'UPDATE_ROLE': 'Role Updated',
    'DELETE_ROLE': 'Role Deleted',
    'ASSIGN_ROLE': 'Role Assigned',
    'REMOVE_ROLE': 'Role Removed',
    'UPDATE_USER_ROLES': 'User Roles Updated',

    # System Actions
    'BULK_UPLOAD': 'Bulk User Upload',
    'DATA_EXPORT': 'Data Exported',
    'SETTINGS_CHANGE': 'System Settings Changed',
    'LOGIN': 'User Login',
    'LOGOUT': 'User Logout',
    'FAILED_LOGIN': 'Failed Login Attempt',

    # Emergency Access
    'EMERGENCY_ACCESS_GRANTED': 'Emergency Access Granted',
    'EMERGENCY_ACCESS_REVOKED': 'Emergency Access Revoked',
    'HANDOVER_DOCUMENTATION': 'Emergency Access Handover',
}


def get_human_readable_action(action, model_name=None, details=None):
    """
    Generate human-readable action descriptions following ERP standards.

    Args:
        action: The action code (e.g., 'CREATE_STUDENT')
        model_name: Optional model name for context
        details: Optional dictionary with additional context

    Returns:
        Human-readable description string
    """
    base_description = ACTION_DESCRIPTIONS.get(action, action.replace('_', ' ').title())

    # Add model context if available
    if model_name:
        model_display = {
            'AuthUser': 'User Account',
            'Student': 'Student Profile',
            'GlobalsFaculty': 'Faculty Member',
            'Staff': 'Staff Member',
            'GlobalsDesignation': 'Role/Designation',
            'GlobalsHoldsdesignation': 'Role Assignment'
        }.get(model_name, model_name)
        base_description = f"{base_description} - {model_display}"

    # Add specific details based on action type
    if details:
        if action == 'UPDATE_USER_ROLES' and 'roles' in details:
            role_count = len(details['roles']) if isinstance(details['roles'], list) else 1
            base_description += f" ({role_count} role{'s' if role_count > 1 else ''} assigned)"

        if action in ['CREATE_STUDENT', 'CREATE_FACULTY', 'CREATE_STAFF'] and 'username' in details:
            base_description += f" - Username: {details['username']}"

        if action == 'RESET_PASSWORD' and 'username' in details:
            base_description += f" - Password reset sent to {details['username']}"

        if action == 'ARCHIVE_' + '_'.join(action.split('_')[1:]) and 'username' in details:
            base_description += f" - User: {details['username']}"

    return base_description


def get_status_emoji(status):
    """Return emoji for status"""
    return {
        'SUCCESS': '✅',
        'FAILED': '❌',
        'PENDING': '⏳',
        'WARNING': '⚠️'
    }.get(status, '📝')


def audit_log(action, model_name=None, include_response=False):
    """
    Enhanced decorator to log admin actions automatically with human-readable descriptions.

    Usage:
        @audit_log(action='CREATE_USER', model_name='AuthUser')
        def create_user(request):
            ...

    Args:
        action: The action being performed (e.g., 'CREATE_USER', 'UPDATE_ROLE')
        model_name: The model being affected (e.g., 'AuthUser', 'GlobalsDesignation')
        include_response: Whether to include response data in logs
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Execute the view function
            response = view_func(request, *args, **kwargs)

            # Determine if the action was successful
            status_code = response.status_code if hasattr(response, 'status_code') else 200
            is_success = status_code < 400

            # Get user from request
            user = None
            if hasattr(request, 'user') and request.user.is_authenticated:
                user = request.user
            elif hasattr(request, 'data') and 'username' in request.data:
                # Try to get user by username from request data
                from .models import AuthUser
                try:
                    user = AuthUser.objects.get(username=request.data.get('username'))
                except:
                    pass

            # Create enhanced audit log entry
            try:
                # Generate human-readable description
                description = get_human_readable_action(
                    action=action,
                    model_name=model_name,
                    details=request.data if hasattr(request, 'data') else None
                )

                # Add status information
                status = 'SUCCESS' if is_success else 'FAILED'
                status_emoji = get_status_emoji(status)
                description = f"{status_emoji} {description}"

                # Add timestamp context
                timestamp_str = timezone.now().strftime('%Y-%m-%d %H:%M:%S')

                # Add additional context for failed operations
                if not is_success:
                    description += f" | HTTP {status_code}"
                    if hasattr(response, 'data') and isinstance(response.data, dict):
                        error_msg = response.data.get('error') or response.data.get('message', '')
                        if error_msg:
                            description += f" | Error: {error_msg}"

                # Add user context
                if user:
                    username = getattr(user, 'username', 'Unknown')
                    description += f" | Performed by: {username}"

                # Add IP address for security tracking
                ip_address = get_client_ip(request)
                if ip_address:
                    description += f" | IP: {ip_address}"

                AuditLog.objects.create(
                    user=user,
                    action=action,
                    model_name=model_name,
                    description=description,
                    ip_address=ip_address,
                    user_agent=get_user_agent(request),
                    reason=request.data.get('reason', '') if hasattr(request, 'data') else '',
                    status=status
                )
            except Exception as e:
                # Don't let audit logging failures break the actual operation
                print(f"Audit logging failed: {e}")

            return response
        return wrapper
    return decorator


def create_audit_log(user=None, action='', model_name=None, object_id=None,
                     description='', reason='', status='SUCCESS', ip_address=None, user_agent=None):
    """
    Helper function to create audit log entries manually.

    Usage:
        create_audit_log(
            user=request.user,
            action='UPDATE_ROLE',
            model_name='GlobalsDesignation',
            object_id=role_id,
            description=f"Updated role {role_name}",
            reason=request.data.get('reason', ''),
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request)
        )
    """
    try:
        AuditLog.objects.create(
            user=user,
            action=action,
            model_name=model_name,
            object_id=str(object_id) if object_id else None,
            description=description,
            reason=reason,
            status=status,
            ip_address=ip_address,
            user_agent=user_agent
        )
    except Exception as e:
        print(f"Audit logging failed: {e}")


def get_client_ip(request):
    """Get client IP address from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_user_agent(request):
    """Get user agent from request."""
    return request.META.get('HTTP_USER_AGENT', 'Unknown')[:255]  # Limit length


def log_failed_login(username_or_email, reason, ip_address, user_agent):
    """
    Log failed login attempts for security monitoring.

    Args:
        username_or_email: The username or email used in login attempt
        reason: Why the login failed (e.g., 'Invalid password', 'Account disabled')
        ip_address: IP address of the attempt
        user_agent: User agent string
    """
    try:
        AuditLog.objects.create(
            user=None,  # No user object for failed logins
            action='FAILED_LOGIN',
            model_name='AuthUser',
            description=f"Failed login attempt for '{username_or_email}'. Reason: {reason}",
            ip_address=ip_address,
            user_agent=user_agent,
            reason=f"Login attempt: {username_or_email}",
            status='FAILED'
        )
    except Exception as e:
        print(f"Failed to log failed login attempt: {e}")


def log_security_event(event_type, description, user=None, ip_address=None,
                       user_agent=None, details=None):
    """
    Log security-related events for monitoring and auditing.

    Args:
        event_type: Type of security event (e.g., 'PERMISSION_CHANGE', 'ROLE_CONFLICT')
        description: Human-readable description
        user: User object if applicable
        ip_address: IP address
        user_agent: User agent string
        details: Additional details as JSON string
    """
    try:
        AuditLog.objects.create(
            user=user,
            action=f'SECURITY_{event_type}',
            model_name='SecurityEvent',
            description=description,
            ip_address=ip_address,
            reason=details or '',
            status='SUCCESS' if user else 'FAILED'
        )
    except Exception as e:
        print(f"Failed to log security event: {e}")
