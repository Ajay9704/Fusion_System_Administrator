"""
Signal Receivers - Example implementations for notification integration
Other modules should create similar receivers to handle events

HOW TO USE IN OTHER MODULES:
1. Create a signals.py file in your module
2. Import the signals from integration_events
3. Create receiver functions using @receiver decorator
4. Import this file in your module's apps.py ready() method
"""

from django.dispatch import receiver
from django.utils import timezone
import logging

from .integration_events import (
    user_created, user_archived, user_restored,
    emergency_access_requested, emergency_access_approved,
    emergency_access_denied, emergency_access_activated,
    emergency_access_revoked, emergency_access_expired,
    department_created, department_updated, department_deleted
)

logger = logging.getLogger(__name__)


# ============================================================================
# EXAMPLE: Notification Service Integration
# This shows how a notification module would listen to these events
# ============================================================================

@receiver(user_created)
def handle_user_created(sender, **kwargs):
    """
    Example: Send welcome notification when user is created
    OTHER MODULES: Replace this with your actual notification logic
    """
    user = kwargs.get('user')
    user_type = kwargs.get('user_type')
    created_by = kwargs.get('created_by')
    
    # TODO: IMPLEMENT IN NOTIFICATION MODULE
    # Example:
    # send_notification(
    #     recipient=user.email,
    #     type='welcome_email',
    #     context={
    #         'user': user,
    #         'user_type': user_type,
    #         'created_by': created_by
    #     }
    # )
    
    logger.info(f"USER_CREATED: {user.username} ({user_type}) created by {created_by}")


@receiver(user_archived)
def handle_user_archived(sender, **kwargs):
    """
    Example: Send archival notification
    OTHER MODULES: Replace with actual logic
    """
    user = kwargs.get('user')
    user_type = kwargs.get('user_type')
    archived_by = kwargs.get('archived_by')
    archived_at = kwargs.get('archived_at')
    reason = kwargs.get('reason')
    
    # TODO: IMPLEMENT IN NOTIFICATION MODULE
    # Example:
    # - Notify department head
    # - Send email to user about archival
    # - Trigger access revocation in other systems
    
    logger.info(f"USER_ARCHIVED: {user.username} ({user_type}) at {archived_at}")


@receiver(user_restored)
def handle_user_restored(sender, **kwargs):
    """
    Example: Send restoration notification
    OTHER MODULES: Replace with actual logic
    """
    user = kwargs.get('user')
    user_type = kwargs.get('user_type')
    restored_by = kwargs.get('restored_by')
    restored_at = kwargs.get('restored_at')
    
    # TODO: IMPLEMENT IN NOTIFICATION MODULE
    # Example:
    # - Restore user access in all systems
    # - Notify relevant departments
    # - Send email to user
    
    logger.info(f"USER_RESTORED: {user.username} ({user_type}) at {restored_at}")


@receiver(emergency_access_requested)
def handle_emergency_access_requested(sender, **kwargs):
    """
    Example: Notify admins about new emergency access request
    OTHER MODULES: Replace with actual notification logic
    """
    emergency_request = kwargs.get('emergency_request')
    requester = kwargs.get('requester')
    requested_role = kwargs.get('requested_role')
    reason = kwargs.get('reason')
    duration = kwargs.get('duration')
    
    # TODO: IMPLEMENT IN NOTIFICATION MODULE
    # Example:
    # - Send notification to all admins
    # - Create notification in notification center
    # - Send email/SMS to admins
    
    logger.info(
        f"EMERGENCY_ACCESS_REQUESTED: {requester.username} -> "
        f"{requested_role.full_name} ({duration}h)"
    )


@receiver(emergency_access_approved)
def handle_emergency_access_approved(sender, **kwargs):
    """
    Example: Notify requester about approval
    OTHER MODULES: Replace with actual logic
    """
    emergency_request = kwargs.get('emergency_request')
    requester = kwargs.get('requester')
    approver = kwargs.get('approver')
    approved_role = kwargs.get('approved_role')
    reason = kwargs.get('reason')
    
    # TODO: IMPLEMENT IN NOTIFICATION MODULE
    # Example:
    # - Notify requester via email/SMS/push notification
    # - Log approval in audit trail
    # - Update notification center
    
    logger.info(
        f"EMERGENCY_ACCESS_APPROVED: {requester.username} -> "
        f"{approved_role.full_name} by {approver.username}"
    )


@receiver(emergency_access_denied)
def handle_emergency_access_denied(sender, **kwargs):
    """
    Example: Notify requester about denial
    OTHER MODULES: Replace with actual logic
    """
    emergency_request = kwargs.get('emergency_request')
    requester = kwargs.get('requester')
    reviewer = kwargs.get('reviewer')
    denial_reason = kwargs.get('denial_reason')
    
    # TODO: IMPLEMENT IN NOTIFICATION MODULE
    # Example:
    # - Notify requester of denial with reason
    # - Log denial for audit purposes
    
    logger.info(
        f"EMERGENCY_ACCESS_DENIED: {requester.username} -> "
        f"by {reviewer.username}"
    )


@receiver(emergency_access_activated)
def handle_emergency_access_activated(sender, **kwargs):
    """
    Example: Notify about active emergency access
    OTHER MODULES: Replace with actual logic
    """
    emergency_request = kwargs.get('emergency_request')
    requester = kwargs.get('requester')
    activated_role = kwargs.get('activated_role')
    expires_at = kwargs.get('expires_at')
    
    # TODO: IMPLEMENT IN NOTIFICATION MODULE
    # Example:
    # - Notify security team
    # - Log activation with expiration time
    # - Send reminder before expiration
    
    logger.info(
        f"EMERGENCY_ACCESS_ACTIVATED: {requester.username} -> "
        f"{activated_role.full_name} (expires: {expires_at})"
    )


@receiver(emergency_access_revoked)
def handle_emergency_access_revoked(sender, **kwargs):
    """
    Example: Notify about revoked access
    OTHER MODULES: Replace with actual logic
    """
    emergency_request = kwargs.get('emergency_request')
    requester = kwargs.get('requester')
    revoked_by = kwargs.get('revoked_by')
    reason = kwargs.get('reason')
    
    # TODO: IMPLEMENT IN NOTIFICATION MODULE
    # Example:
    # - Notify requester immediately
    # - Alert security team
    # - Log revocation
    
    logger.info(
        f"EMERGENCY_ACCESS_REVOKED: {requester.username} -> "
        f"by {revoked_by.username}"
    )


@receiver(emergency_access_expired)
def handle_emergency_access_expired(sender, **kwargs):
    """
    Example: Handle automatic expiration
    OTHER MODULES: Replace with actual logic
    """
    emergency_request = kwargs.get('emergency_request')
    requester = kwargs.get('requester')
    expired_role = kwargs.get('expired_role')
    
    # TODO: IMPLEMENT IN NOTIFICATION MODULE
    # Example:
    # - Notify user that access has expired
    # - Send summary to admins
    # - Cleanup temporary permissions
    
    logger.info(
        f"EMERGENCY_ACCESS_EXPIRED: {requester.username} -> "
        f"{expired_role.full_name}"
    )


@receiver(department_created)
def handle_department_created(sender, **kwargs):
    """
    Example: Notify about new department
    OTHER MODULES: Replace with actual logic
    """
    department = kwargs.get('department')
    parent_department = kwargs.get('parent_department')
    created_by = kwargs.get('created_by')
    
    # TODO: IMPLEMENT IN NOTIFICATION MODULE
    logger.info(f"DEPARTMENT_CREATED: {department.name}")


@receiver(department_updated)
def handle_department_updated(sender, **kwargs):
    """
    Example: Notify about department changes
    OTHER MODULES: Replace with actual logic
    """
    department = kwargs.get('department')
    old_data = kwargs.get('old_data')
    new_data = kwargs.get('new_data')
    updated_by = kwargs.get('updated_by')
    
    # TODO: IMPLEMENT IN NOTIFICATION MODULE
    logger.info(f"DEPARTMENT_UPDATED: {department.name}")


@receiver(department_deleted)
def handle_department_deleted(sender, **kwargs):
    """
    Example: Notify about department deletion
    OTHER MODULES: Replace with actual logic
    """
    department = kwargs.get('department')
    deleted_by = kwargs.get('deleted_by')
    reason = kwargs.get('reason')
    
    # TODO: IMPLEMENT IN NOTIFICATION MODULE
    logger.info(f"DEPARTMENT_DELETED: {department.name}")


# ============================================================================
# HOW OTHER MODULES SHOULD IMPLEMENT RECEIVERS
# ============================================================================
"""
In your notification module (e.g., notification_app/signals.py):

from django.dispatch import receiver
from api.integration_events import user_created, user_archived

@receiver(user_created)
def send_welcome_notification(sender, **kwargs):
    user = kwargs.get('user')
    user_type = kwargs.get('user_type')
    
    # Your notification logic here
    Notification.objects.create(
        recipient=user,
        type='welcome',
        message=f'Welcome to the system! Your account has been created as {user_type}'
    )

In your notification module's apps.py:

from django.apps import AppConfig

class NotificationConfig(AppConfig):
    name = 'notification_app'
    
    def ready(self):
        import notification_app.signals  # noqa
"""
