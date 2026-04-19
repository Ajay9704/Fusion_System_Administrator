# Integration Trigger Points - Complete Guide

## Overview

This document describes all notification and event trigger points implemented in the System Admin module. These triggers enable seamless integration with other modules (Notification Service, Email Service, Audit Service, etc.).

## Architecture

The integration uses Django signals to provide a clean, decoupled event system:

```
Operation → Trigger Point → Signal → Receiver (Other Modules)
```

**Key Benefits:**
- ✅ Decoupled architecture - modules don't need to know about each other
- ✅ Easy to extend - just add new receivers
- ✅ Fail-safe - trigger failures don't break main operations
- ✅ Complete audit trail - all events are logged

---

## Available Trigger Points

### 1. User Management Events

#### `user_created`
**When:** New user account is created (student, faculty, staff)

**Data Provided:**
- `user`: The AuthUser object
- `user_type`: 'student', 'faculty', or 'staff'
- `created_by`: Admin who created the user

**Use Cases:**
- Send welcome email
- Setup user profile in other systems
- Notify department heads
- Initialize user preferences

**Example Integration:**
```python
from api.integration_events import user_created

@receiver(user_created)
def send_welcome_email(sender, **kwargs):
    user = kwargs.get('user')
    user_type = kwargs.get('user_type')
    
    # Send welcome notification
    NotificationService.send(
        to=user.email,
        type='welcome',
        context={'user': user, 'type': user_type}
    )
```

---

#### `user_archived`
**When:** User account is deactivated/archived

**Data Provided:**
- `user`: The AuthUser object
- `user_type`: Type of user
- `archived_by`: Admin who archived
- `archived_at`: Timestamp
- `reason`: Reason for archival

**Use Cases:**
- Revoke access from all systems
- Notify department heads
- Send archival confirmation email
- Cleanup user resources
- Update directory listings

**Example Integration:**
```python
from api.integration_events import user_archived

@receiver(user_archived)
def handle_user_archival(sender, **kwargs):
    user = kwargs.get('user')
    
    # Revoke all system access
    AccessManager.revoke_all(user)
    
    # Notify relevant parties
    NotificationService.send_to_admins(
        message=f"User {user.username} has been archived"
    )
```

---

#### `user_restored`
**When:** Previously archived user is reactivated

**Data Provided:**
- `user`: The AuthUser object
- `user_type`: Type of user
- `restored_by`: Admin who restored
- `restored_at`: Timestamp

**Use Cases:**
- Restore system access
- Notify department heads
- Send restoration confirmation
- Reactivate services

---

### 2. Emergency Access Events

#### `emergency_access_requested`
**When:** User submits emergency access request

**Data Provided:**
- `emergency_request`: The EmergencyAccess object
- `requester`: User requesting access
- `requested_role`: Role being requested
- `reason`: Justification provided
- `duration`: Hours requested

**Use Cases:**
- **URGENT**: Notify all admins immediately
- Create notification in admin dashboard
- Send SMS/email alerts
- Log in security monitoring system

**Example Integration:**
```python
from api.integration_events import emergency_access_requested

@receiver(emergency_access_requested)
def alert_admins(sender, **kwargs):
    requester = kwargs.get('requester')
    role = kwargs.get('requested_role')
    reason = kwargs.get('reason')
    
    # Send urgent notification to all admins
    AdminNotificationService.send_urgent(
        title="Emergency Access Requested",
        message=f"{requester.username} requests {role.full_name}",
        details={
            'reason': reason,
            'requester_email': requester.email
        }
    )
```

---

#### `emergency_access_approved`
**When:** Admin approves emergency access request

**Data Provided:**
- `emergency_request`: The EmergencyAccess object
- `requester`: User who requested
- `approver`: Admin who approved
- `approved_role`: Role that was approved
- `reason`: Approval reason/notes

**Use Cases:**
- Notify requester of approval
- Log approval in audit system
- Prepare role activation
- Update security logs

---

#### `emergency_access_denied`
**When:** Admin denies emergency access request

**Data Provided:**
- `emergency_request`: The EmergencyAccess object
- `requester`: User who requested
- `reviewer`: Admin who denied
- `denial_reason`: Reason for denial

**Use Cases:**
- Notify requester of denial with reason
- Log denial for compliance
- Track denial patterns

---

#### `emergency_access_activated`
**When:** Requester activates their approved emergency access

**Data Provided:**
- `emergency_request`: The EmergencyAccess object
- `requester`: User activating access
- `activated_role`: Role being activated
- `expires_at`: When access will expire

**Use Cases:**
- **CRITICAL**: Grant role permissions immediately
- Start expiration timer
- Notify security team
- Log activation with timestamp
- Send reminder before expiration

**Example Integration:**
```python
from api.integration_events import emergency_access_activated

@receiver(emergency_access_activated)
def monitor_emergency_access(sender, **kwargs):
    requester = kwargs.get('requester')
    role = kwargs.get('activated_role')
    expires_at = kwargs.get('expires_at')
    
    # Log in security monitoring
    SecurityMonitor.log(
        event='emergency_access_active',
        user=requester,
        role=role,
        expires=expires_at
    )
    
    # Schedule expiration reminder
    Scheduler.send_reminder(
        when=expires_at - timedelta(hours=2),
        to=requester.email,
        message=f"Emergency access expires in 2 hours"
    )
```

---

#### `emergency_access_revoked`
**When:** Emergency access is manually revoked before expiration

**Data Provided:**
- `emergency_request`: The EmergencyAccess object
- `requester`: User whose access was revoked
- `revoked_by`: Admin/user who revoked
- `reason`: Reason for revocation

**Use Cases:**
- **IMMEDIATE**: Remove role permissions
- Notify requester
- Alert security team
- Log revocation

---

#### `emergency_access_expired`
**When:** Emergency access automatically expires (time-based)

**Data Provided:**
- `emergency_request`: The EmergencyAccess object
- `requester`: User whose access expired
- `expired_role`: Role that was removed

**Use Cases:**
- Auto-remove permissions
- Notify user of expiration
- Send summary to admins
- Cleanup temporary data

---

### 3. Department Management Events

#### `department_created`
**When:** New department is added

**Data Provided:**
- `department`: The department object
- `parent_department`: Parent if any
- `created_by`: Admin who created

**Use Cases:**
- Update organization chart
- Notify affected users
- Setup department resources

---

#### `department_updated`
**When:** Department details are modified

**Data Provided:**
- `department`: The department object
- `old_data`: Previous values
- `new_data`: New values
- `updated_by`: Admin who updated

**Use Cases:**
- Update references in other systems
- Notify department members
- Log changes

---

#### `department_deleted`
**When:** Department is removed

**Data Provided:**
- `department`: The department object
- `deleted_by`: Admin who deleted
- `reason`: Reason for deletion

**Use Cases:**
- Reassign users to other departments
- Update organization structure
- Notify affected parties

---

## Implementation Guide for Other Modules

### Step 1: Create Signal Receivers

In your module (e.g., `notification_module/signals.py`):

```python
from django.dispatch import receiver
from api.integration_events import (
    user_created, user_archived,
    emergency_access_requested, emergency_access_approved
)

@receiver(user_created)
def handle_user_created(sender, **kwargs):
    user = kwargs.get('user')
    # Your notification logic here
    pass

@receiver(emergency_access_requested)
def handle_emergency_request(sender, **kwargs):
    requester = kwargs.get('requester')
    # Your urgent notification logic here
    pass
```

### Step 2: Register Signals

In your module's `apps.py`:

```python
from django.apps import AppConfig

class NotificationModuleConfig(AppConfig):
    name = 'notification_module'
    
    def ready(self):
        # Import signals to register them
        import notification_module.signals  # noqa
```

### Step 3: Add to INSTALLED_APPS

In your `settings.py`:

```python
INSTALLED_APPS = [
    # ...
    'notification_module',
    # ...
]
```

---

## Frontend Integration

### Real-time Notifications

For real-time updates, the frontend can poll or use WebSockets:

```javascript
// Example: Poll for new emergency requests
useEffect(() => {
  const interval = setInterval(async () => {
    const response = await api.get('/emergency-access/requests/', {
      params: { view: 'all-requests', status: 'PENDING' }
    });
    
    if (response.data.requests.length > 0) {
      showNotification({
        title: 'New Emergency Access Request',
        message: `${response.data.requests.length} pending request(s)`,
        color: 'red'
      });
    }
  }, 30000); // Check every 30 seconds
  
  return () => clearInterval(interval);
}, []);
```

### Notification Display

Create a notification component that listens to different event types:

```javascript
const EventNotificationHandler = () => {
  const handleUserArchived = (userData) => {
    showNotification({
      title: 'User Archived',
      message: `${userData.username} has been archived`,
      color: 'orange'
    });
  };

  const handleEmergencyApproved = (data) => {
    showNotification({
      title: 'Emergency Access Approved',
      message: `Request approved by ${data.approver}`,
      color: 'green'
    });
  };

  // ... more handlers
};
```

---

## Error Handling

All trigger points are wrapped in try-except blocks:

```python
try:
    trigger_user_archived(user=user, ...)
except Exception as e:
    # Log but don't fail the operation
    print(f"[INTEGRATION EVENT] Trigger failed: {e}")
```

**This ensures:**
- Main operations always succeed
- Notification failures don't block user actions
- Errors are logged for debugging

---

## Testing Integration

### Test Signal Reception

```python
from api.integration_events import user_created

def test_user_created_signal():
    received_data = {}
    
    @receiver(user_created)
    def test_receiver(sender, **kwargs):
        received_data.update(kwargs)
    
    # Trigger the signal
    trigger_user_created(user=test_user, user_type='student')
    
    assert received_data['user'] == test_user
    assert received_data['user_type'] == 'student'
```

---

## Monitoring & Debugging

### View Active Signals

```python
from api.integration_events import user_created

# See all connected receivers
print(user_created.receivers)
```

### Enable Debug Logging

In `settings.py`:

```python
LOGGING = {
    'version': 1,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'api.integration_events': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

---

## Best Practices

1. **Keep Receivers Fast**: Don't block on slow operations
2. **Use Async for Heavy Tasks**: Send emails/tasks to queue
3. **Handle Errors Gracefully**: Don't let receiver failures break flows
4. **Log Everything**: Track all events for audit purposes
5. **Test Thoroughly**: Test signal reception in isolation

---

## Quick Reference

| Event | When Triggered | Priority | Key Data |
|-------|---------------|----------|----------|
| `user_created` | New user created | Low | user, user_type |
| `user_archived` | User deactivated | Medium | user, reason |
| `user_restored` | User reactivated | Medium | user, restored_by |
| `emergency_access_requested` | Emergency request | **HIGH** | requester, role, reason |
| `emergency_access_approved` | Request approved | High | requester, approver |
| `emergency_access_denied` | Request denied | Medium | requester, reason |
| `emergency_access_activated` | Access activated | **CRITICAL** | requester, expires_at |
| `emergency_access_revoked` | Access revoked | **HIGH** | requester, reason |
| `emergency_access_expired` | Auto-expiration | High | requester, role |
| `department_created` | New department | Low | department |
| `department_updated` | Dept modified | Low | old/new data |
| `department_deleted` | Dept removed | Medium | department, reason |

---

## Support

For questions or issues with integration:
1. Check this documentation
2. Review `integration_events.py` for signal definitions
3. Review `signal_receivers.py` for example implementations
4. Check logs for trigger execution status

---

**Last Updated:** April 19, 2026  
**Version:** 1.0
