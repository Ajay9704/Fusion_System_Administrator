"""
EXAMPLE INTEGRATION - Notification Module
==========================================
This is an EXAMPLE of how other modules should integrate with the event system.
Copy this file to your module and customize the receiver functions.

SETUP INSTRUCTIONS:
1. Copy this file to your module (e.g., notification_app/signals.py)
2. Customize the receiver functions with your actual logic
3. Import this file in your module's apps.py ready() method
"""

from django.dispatch import receiver
from django.utils import timezone
import logging

# Import all available signals
from api.integration_events import (
    # User events
    user_created,
    user_archived,
    user_restored,
    user_roles_updated,
    user_password_reset,
    
    # Emergency access events
    emergency_access_requested,
    emergency_access_approved,
    emergency_access_denied,
    emergency_access_activated,
    emergency_access_revoked,
    emergency_access_expired,
    
    # Department events
    department_created,
    department_updated,
    department_deleted,
    
    # Other events
    security_event,
    bulk_operation_completed
)

logger = logging.getLogger(__name__)


# ============================================================================
# USER MANAGEMENT RECEIVERS
# ============================================================================

@receiver(user_created)
def notify_user_created(sender, **kwargs):
    """
    Send welcome notification when new user is created
    CUSTOMIZE: Replace with your actual notification logic
    """
    user = kwargs.get('user')
    user_type = kwargs.get('user_type')
    created_by = kwargs.get('created_by')
    
    # TODO: IMPLEMENT YOUR NOTIFICATION LOGIC
    # Example implementations:
    
    # 1. Send welcome email
    # send_email(
    #     to=user.email,
    #     subject='Welcome to the System!',
    #     template='welcome_email.html',
    #     context={'user': user, 'user_type': user_type}
    # )
    
    # 2. Create in-app notification
    # Notification.objects.create(
    #     recipient=user,
    #     type='welcome',
    #     title='Welcome!',
    #     message=f'Your {user_type} account has been created successfully.'
    # )
    
    # 3. Send to external notification service
    # requests.post('https://notification-service/api/send', json={
    #     'type': 'user_created',
    #     'user': user.username,
    #     'email': user.email
    # })
    
    logger.info(f"[NOTIFICATION] User created: {user.username} ({user_type})")


@receiver(user_archived)
def notify_user_archived(sender, **kwargs):
    """
    Notify when user is archived
    CUSTOMIZE: Replace with your actual logic
    """
    user = kwargs.get('user')
    user_type = kwargs.get('user_type')
    archived_by = kwargs.get('archived_by')
    archived_at = kwargs.get('archived_at')
    reason = kwargs.get('reason')
    
    # TODO: IMPLEMENT YOUR NOTIFICATION LOGIC
    # Example:
    # - Send email to user about archival
    # - Notify department head
    # - Create admin notification
    # - Trigger cleanup in other systems
    
    logger.info(f"[NOTIFICATION] User archived: {user.username}")


@receiver(user_restored)
def notify_user_restored(sender, **kwargs):
    """
    Notify when user is restored
    CUSTOMIZE: Replace with your actual logic
    """
    user = kwargs.get('user')
    user_type = kwargs.get('user_type')
    restored_by = kwargs.get('restored_by')
    restored_at = kwargs.get('restored_at')
    
    # TODO: IMPLEMENT YOUR NOTIFICATION LOGIC
    logger.info(f"[NOTIFICATION] User restored: {user.username}")


# ============================================================================
# EMERGENCY ACCESS RECEIVERS (HIGH PRIORITY)
# ============================================================================

@receiver(emergency_access_requested)
def notify_emergency_requested(sender, **kwargs):
    """
    URGENT: Notify admins about new emergency access request
    CUSTOMIZE: Replace with your actual urgent notification logic
    """
    emergency_request = kwargs.get('emergency_request')
    requester = kwargs.get('requester')
    requested_role = kwargs.get('requested_role')
    reason = kwargs.get('reason')
    duration = kwargs.get('duration')
    
    # TODO: IMPLEMENT URGENT NOTIFICATION
    # Example:
    
    # 1. Send SMS to all admins
    # SMSService.send_to_all_admins(
    #     f"URGENT: {requester.username} requests emergency {requested_role.full_name}"
    # )
    
    # 2. Send push notification
    # PushNotification.send_to_role(
    #     role='admin',
    #     title='Emergency Access Request',
    #     body=f'{requester.username} needs {requested_role.full_name} access'
    # )
    
    # 3. Create high-priority notification
    # Notification.objects.create(
    #     recipient__is_staff=True,  # All admins
    #     type='emergency_request',
    #     priority='urgent',
    #     title='Emergency Access Requested',
    #     message=f'{requester.username} requests {requested_role.full_name} for {duration}h'
    # )
    
    # 4. Send email to admins
    # admins = AuthUser.objects.filter(is_staff=True)
    # for admin in admins:
    #     send_email(
    #         to=admin.email,
    #         subject='URGENT: Emergency Access Request',
    #         template='emergency_request.html',
    #         context={
    #             'requester': requester,
    #             'role': requested_role,
    #             'reason': reason,
    #             'duration': duration
    #         }
    #     )
    
    logger.warning(
        f"[URGENT NOTIFICATION] Emergency access requested: "
        f"{requester.username} -> {requested_role.full_name}"
    )


@receiver(emergency_access_approved)
def notify_emergency_approved(sender, **kwargs):
    """
    Notify requester about approval
    CUSTOMIZE: Replace with your actual logic
    """
    emergency_request = kwargs.get('emergency_request')
    requester = kwargs.get('requester')
    approver = kwargs.get('approver')
    approved_role = kwargs.get('approved_role')
    reason = kwargs.get('reason')
    
    # TODO: IMPLEMENT NOTIFICATION
    # Example:
    # - Send email to requester
    # - Create in-app notification
    # - Send SMS
    
    logger.info(
        f"[NOTIFICATION] Emergency access approved: "
        f"{requester.username} by {approver.username}"
    )


@receiver(emergency_access_denied)
def notify_emergency_denied(sender, **kwargs):
    """
    Notify requester about denial
    CUSTOMIZE: Replace with your actual logic
    """
    emergency_request = kwargs.get('emergency_request')
    requester = kwargs.get('requester')
    reviewer = kwargs.get('reviewer')
    denial_reason = kwargs.get('denial_reason')
    
    # TODO: IMPLEMENT NOTIFICATION
    logger.info(
        f"[NOTIFICATION] Emergency access denied: "
        f"{requester.username} by {reviewer.username}"
    )


@receiver(emergency_access_activated)
def notify_emergency_activated(sender, **kwargs):
    """
    CRITICAL: Notify about active emergency access
    CUSTOMIZE: Replace with your actual logic
    """
    emergency_request = kwargs.get('emergency_request')
    requester = kwargs.get('requester')
    activated_role = kwargs.get('activated_role')
    expires_at = kwargs.get('expires_at')
    
    # TODO: IMPLEMENT CRITICAL NOTIFICATION
    # Example:
    # - Notify security team immediately
    # - Log in security monitoring system
    # - Schedule expiration reminder
    
    logger.critical(
        f"[CRITICAL NOTIFICATION] Emergency access ACTIVATED: "
        f"{requester.username} -> {activated_role.full_name} "
        f"(expires: {expires_at})"
    )


@receiver(emergency_access_revoked)
def notify_emergency_revoked(sender, **kwargs):
    """
    HIGH: Notify about revoked access
    CUSTOMIZE: Replace with your actual logic
    """
    emergency_request = kwargs.get('emergency_request')
    requester = kwargs.get('requester')
    revoked_by = kwargs.get('revoked_by')
    reason = kwargs.get('reason')
    
    # TODO: IMPLEMENT NOTIFICATION
    logger.warning(
        f"[NOTIFICATION] Emergency access revoked: "
        f"{requester.username} by {revoked_by.username}"
    )


@receiver(emergency_access_expired)
def notify_emergency_expired(sender, **kwargs):
    """
    Notify about automatic expiration
    CUSTOMIZE: Replace with your actual logic
    """
    emergency_request = kwargs.get('emergency_request')
    requester = kwargs.get('requester')
    expired_role = kwargs.get('expired_role')
    
    # TODO: IMPLEMENT NOTIFICATION
    # Example:
    # - Notify user their access has expired
    # - Send summary to admins
    
    logger.info(
        f"[NOTIFICATION] Emergency access expired: "
        f"{requester.username} -> {expired_role.full_name}"
    )


# ============================================================================
# DEPARTMENT MANAGEMENT RECEIVERS
# ============================================================================

@receiver(department_created)
def notify_department_created(sender, **kwargs):
    """Notify about new department"""
    department = kwargs.get('department')
    parent_department = kwargs.get('parent_department')
    created_by = kwargs.get('created_by')
    
    # TODO: IMPLEMENT NOTIFICATION
    logger.info(f"[NOTIFICATION] Department created: {department.name}")


@receiver(department_updated)
def notify_department_updated(sender, **kwargs):
    """Notify about department changes"""
    department = kwargs.get('department')
    old_data = kwargs.get('old_data')
    new_data = kwargs.get('new_data')
    updated_by = kwargs.get('updated_by')
    
    # TODO: IMPLEMENT NOTIFICATION
    logger.info(f"[NOTIFICATION] Department updated: {department.name}")


@receiver(department_deleted)
def notify_department_deleted(sender, **kwargs):
    """Notify about department deletion"""
    department = kwargs.get('department')
    deleted_by = kwargs.get('deleted_by')
    reason = kwargs.get('reason')
    
    # TODO: IMPLEMENT NOTIFICATION
    logger.info(f"[NOTIFICATION] Department deleted: {department.name}")


# ============================================================================
# HOW TO ACTIVATE THIS MODULE
# ============================================================================
"""
STEP 1: Save this file in your module (e.g., notification_app/signals.py)

STEP 2: Edit your module's apps.py:

```python
from django.apps import AppConfig

class NotificationAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'notification_app'
    
    def ready(self):
        # Import signals to register them
        import notification_app.signals  # noqa: F401
```

STEP 3: Make sure your module is in INSTALLED_APPS in settings.py:

```python
INSTALLED_APPS = [
    # ... other apps
    'notification_app',
    # ...
]
```

STEP 4: Replace the TODO sections with your actual notification logic.

STEP 5: Test by performing operations in the System Admin module.
"""
