"""
Audit logging decorator and helper functions for tracking admin actions.
"""
from functools import wraps
from django.utils import timezone
from .models import AuditLog


def audit_log(action, model_name=None, include_response=False):
    """
    Decorator to log admin actions automatically.

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

            # Create audit log entry
            try:
                description = f"{action} - Status: {status_code}"

                # Log request method and path
                if hasattr(request, 'method'):
                    description += f" | Method: {request.method}"
                if hasattr(request, 'path'):
                    description += f" | Path: {request.path}"

                # Log key information from request
                if hasattr(request, 'data') and request.data:
                    # Log key information from request
                    if 'username' in request.data:
                        description += f" | Target Username: {request.data.get('username')}"
                    if 'name' in request.data:
                        description += f" | Name: {request.data.get('name')}"
                    if 'reason' in request.data:
                        description += f" | Reason: {request.data.get('reason')}"
                    if 'roles' in request.data:
                        description += f" | Roles: {request.data.get('roles')}"

                # Log response data if requested
                if include_response and hasattr(response, 'data'):
                    description += f" | Response: {str(response.data)[:200]}"

                # Get reason safely
                reason = ''
                try:
                    if hasattr(request, 'data') and request.data:
                        reason = request.data.get('reason', '')
                except:
                    reason = ''

                AuditLog.objects.create(
                    user=user,
                    action=action,
                    model_name=model_name,
                    description=description,
                    ip_address=get_client_ip(request),
                    user_agent=get_user_agent(request),
                    reason=reason,
                    status='SUCCESS' if is_success else 'FAILED'
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
