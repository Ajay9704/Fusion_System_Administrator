"""
Integration Event System - Notification Triggers
This module provides event triggers for cross-module integration.
Other modules can listen to these events or trigger them as needed.

INTEGRATION GUIDE:
- Other modules can connect to these signals to receive notifications
- Events are triggered for all critical operations
- Each event includes relevant data for notification purposes
"""

from django.dispatch import Signal

# ============================================================================
# USER MANAGEMENT EVENTS
# ============================================================================

# Triggered when a user is created (student, faculty, staff)
user_created = Signal()
user_created.__doc__ = """
Provides: user, user_type, created_by
Trigger: When any new user account is created
Usage: Other modules can listen to send welcome emails, setup profiles, etc.
"""

# Triggered when a user is archived (deactivated)
user_archived = Signal()
user_archived.__doc__ = """
Provides: user, user_type, archived_by, archived_at, reason
Trigger: When a user account is archived/deactivated
Usage: Notify relevant departments, revoke access, cleanup resources
"""

# Triggered when a user is restored (reactivated)
user_restored = Signal()
user_restored.__doc__ = """
Provides: user, user_type, restored_by, restored_at
Trigger: When a previously archived user is restored
Usage: Restore access, notify departments, re-enable services
"""

# Triggered when user roles are updated
user_roles_updated = Signal()
user_roles_updated.__doc__ = """
Provides: user, old_roles, new_roles, updated_by
Trigger: When user's designations/roles are modified
Usage: Update permissions, notify user, audit logging
"""

# Triggered when user password is reset
user_password_reset = Signal()
user_password_reset.__doc__ = """
Provides: user, reset_by, reset_method
Trigger: When user password is reset
Usage: Send password reset notification, security alert
"""

# ============================================================================
# EMERGENCY ACCESS EVENTS
# ============================================================================

# Triggered when emergency access is requested
emergency_access_requested = Signal()
emergency_access_requested.__doc__ = """
Provides: emergency_request, requester, requested_role, reason, duration
Trigger: When a new emergency access request is submitted
Usage: Notify admins for approval, log request, send alerts
"""

# Triggered when emergency access is approved
emergency_access_approved = Signal()
emergency_access_approved.__doc__ = """
Provides: emergency_request, requester, approver, approved_role, reason
Trigger: When admin approves an emergency access request
Usage: Notify requester, grant temporary permissions, log action
"""

# Triggered when emergency access is denied
emergency_access_denied = Signal()
emergency_access_denied.__doc__ = """
Provides: emergency_request, requester, reviewer, denial_reason
Trigger: When admin denies an emergency access request
Usage: Notify requester of denial, log action
"""

# Triggered when emergency access is activated
emergency_access_activated = Signal()
emergency_access_activated.__doc__ = """
Provides: emergency_request, requester, activated_role, expires_at
Trigger: When requester activates their approved emergency access
Usage: Grant role permissions, start timer, notify relevant systems
"""

# Triggered when emergency access is revoked
emergency_access_revoked = Signal()
emergency_access_revoked.__doc__ = """
Provides: emergency_request, requester, revoked_by, reason
Trigger: When emergency access is manually revoked
Usage: Remove permissions, notify user, log revocation
"""

# Triggered when emergency access expires
emergency_access_expired = Signal()
emergency_access_expired.__doc__ = """
Provides: emergency_request, requester, expired_role
Trigger: When emergency access automatically expires (time-based)
Usage: Auto-remove permissions, notify user, cleanup
"""

# ============================================================================
# DEPARTMENT MANAGEMENT EVENTS
# ============================================================================

# Triggered when a department is created
department_created = Signal()
department_created.__doc__ = """
Provides: department, parent_department, created_by
Trigger: When a new department is added
Usage: Update organization structure, notify admins
"""

# Triggered when a department is updated
department_updated = Signal()
department_updated.__doc__ = """
Provides: department, old_data, new_data, updated_by
Trigger: When department details are modified
Usage: Update references, notify affected users
"""

# Triggered when a department is deleted
department_deleted = Signal()
department_deleted.__doc__ = """
Provides: department, deleted_by, reason
Trigger: When a department is removed
Usage: Reassign users, cleanup references, notify admins
"""

# ============================================================================
# ROLE MANAGEMENT EVENTS
# ============================================================================

# Triggered when a new role/designation is created
role_created = Signal()
role_created.__doc__ = """
Provides: role, created_by, permissions
Trigger: When a new designation/role is created
Usage: Setup permissions, notify admins
"""

# Triggered when role permissions are modified
role_permissions_modified = Signal()
role_permissions_modified.__doc__ = """
Provides: role, old_permissions, new_permissions, modified_by
Trigger: When module access or permissions for a role change
Usage: Update user permissions, notify affected users
"""

# ============================================================================
# AUDIT & LOGGING EVENTS
# ============================================================================

# Triggered for critical security events
security_event = Signal()
security_event.__doc__ = """
Provides: event_type, user, details, severity, timestamp
Trigger: Security-related events (failed logins, unauthorized access, etc.)
Usage: Security monitoring, alert systems, incident response
"""

# Triggered when bulk operations are performed
bulk_operation_completed = Signal()
bulk_operation_completed.__doc__ = """
Provides: operation_type, total_count, success_count, failure_count, performed_by
Trigger: After bulk upload, bulk update, etc.
Usage: Send summary notifications, log results
"""


# ============================================================================
# HELPER FUNCTIONS TO TRIGGER EVENTS
# ============================================================================

def trigger_user_created(user, user_type, created_by=None):
    """Trigger user created event"""
    user_created.send(
        sender=user.__class__,
        user=user,
        user_type=user_type,
        created_by=created_by
    )


def trigger_user_archived(user, user_type, archived_by=None, reason=None):
    """Trigger user archived event"""
    from django.utils import timezone
    user_archived.send(
        sender=user.__class__,
        user=user,
        user_type=user_type,
        archived_by=archived_by,
        archived_at=timezone.now(),
        reason=reason
    )


def trigger_user_restored(user, user_type, restored_by=None):
    """Trigger user restored event"""
    from django.utils import timezone
    user_restored.send(
        sender=user.__class__,
        user=user,
        user_type=user_type,
        restored_by=restored_by,
        restored_at=timezone.now()
    )


def trigger_emergency_access_requested(emergency_request):
    """Trigger emergency access requested event"""
    emergency_access_requested.send(
        sender=emergency_request.__class__,
        emergency_request=emergency_request,
        requester=emergency_request.requester,
        requested_role=emergency_request.requested_role,
        reason=emergency_request.reason,
        duration=emergency_request.duration_hours
    )


def trigger_emergency_access_approved(emergency_request, approver):
    """Trigger emergency access approved event"""
    emergency_access_approved.send(
        sender=emergency_request.__class__,
        emergency_request=emergency_request,
        requester=emergency_request.requester,
        approver=approver,
        approved_role=emergency_request.requested_role,
        reason=emergency_request.approval_reason
    )


def trigger_emergency_access_denied(emergency_request, reviewer):
    """Trigger emergency access denied event"""
    emergency_access_denied.send(
        sender=emergency_request.__class__,
        emergency_request=emergency_request,
        requester=emergency_request.requester,
        reviewer=reviewer,
        denial_reason=emergency_request.approval_reason
    )


def trigger_emergency_access_activated(emergency_request):
    """Trigger emergency access activated event"""
    emergency_access_activated.send(
        sender=emergency_request.__class__,
        emergency_request=emergency_request,
        requester=emergency_request.requester,
        activated_role=emergency_request.requested_role,
        expires_at=emergency_request.expires_at
    )


def trigger_emergency_access_revoked(emergency_request, revoked_by, reason=None):
    """Trigger emergency access revoked event"""
    emergency_access_revoked.send(
        sender=emergency_request.__class__,
        emergency_request=emergency_request,
        requester=emergency_request.requester,
        revoked_by=revoked_by,
        reason=reason
    )


def trigger_department_created(department, created_by=None):
    """Trigger department created event"""
    department_created.send(
        sender=department.__class__,
        department=department,
        parent_department=department.parent_department if hasattr(department, 'parent_department') else None,
        created_by=created_by
    )


def trigger_department_updated(department, old_data, new_data, updated_by=None):
    """Trigger department updated event"""
    department_updated.send(
        sender=department.__class__,
        department=department,
        old_data=old_data,
        new_data=new_data,
        updated_by=updated_by
    )


def trigger_department_deleted(department, deleted_by=None, reason=None):
    """Trigger department deleted event"""
    department_deleted.send(
        sender=department.__class__,
        department=department,
        deleted_by=deleted_by,
        reason=reason
    )
