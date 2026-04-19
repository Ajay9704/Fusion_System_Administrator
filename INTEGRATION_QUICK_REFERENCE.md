# Integration Quick Reference

## 🚀 Quick Start (3 Steps)

### 1. Import Signals
```python
from api.integration_events import user_created, emergency_access_requested
```

### 2. Create Receiver
```python
from django.dispatch import receiver

@receiver(user_created)
def my_handler(sender, **kwargs):
    user = kwargs.get('user')
    # Your logic here
```

### 3. Register in apps.py
```python
def ready(self):
    import your_module.signals  # noqa
```

---

## 📋 Available Events

### User Events
| Signal | When | Priority |
|--------|------|----------|
| `user_created` | New user account | Low |
| `user_archived` | User deactivated | Medium |
| `user_restored` | User reactivated | Medium |

### Emergency Events ⚠️
| Signal | When | Priority |
|--------|------|----------|
| `emergency_access_requested` | New request | **HIGH** |
| `emergency_access_approved` | Request approved | High |
| `emergency_access_denied` | Request denied | Medium |
| `emergency_access_activated` | Access starts | **CRITICAL** |
| `emergency_access_revoked` | Access removed | **HIGH** |
| `emergency_access_expired` | Auto-expired | High |

### Department Events
| Signal | When | Priority |
|--------|------|----------|
| `department_created` | New dept | Low |
| `department_updated` | Dept changed | Low |
| `department_deleted` | Dept removed | Medium |

---

## 📦 What Data You Get

### User Events
```python
user = kwargs.get('user')              # AuthUser object
user_type = kwargs.get('user_type')    # 'student', 'faculty', 'staff'
archived_by = kwargs.get('archived_by') # Admin who did it
reason = kwargs.get('reason')           # Why
```

### Emergency Events
```python
requester = kwargs.get('requester')           # Who requested
approver = kwargs.get('approver')             # Who approved
requested_role = kwargs.get('requested_role') # Role object
reason = kwargs.get('reason')                  # Why
duration = kwargs.get('duration')              # Hours
expires_at = kwargs.get('expires_at')          # When expires
```

---

## ✅ Best Practices

### DO ✓
```python
@receiver(user_created)
def handler(sender, **kwargs):
    try:
        # Your notification logic
        send_notification(kwargs.get('user'))
    except Exception as e:
        logger.error(f"Notification failed: {e}")
```

### DON'T ✗
```python
@receiver(user_created)
def handler(sender, **kwargs):
    # Don't raise exceptions - breaks the main flow!
    raise Exception("Something went wrong")
    
    # Don't do slow synchronous operations
    time.sleep(10)  # BAD!
```

---

## 🧪 Testing

```python
from api.integration_events import trigger_user_created

def test_notification():
    trigger_user_created(
        user=test_user,
        user_type='student',
        created_by=admin_user
    )
    # Check if notification was sent
```

---

## 📁 File Structure

```
your_module/
├── __init__.py
├── apps.py          # Register signals here
├── signals.py       # Your receivers
└── ...
```

---

## 🔍 Debugging

### Check if signals are connected
```python
from api.integration_events import user_created
print(user_created.receivers)
```

### Enable logging
```python
LOGGING = {
    'loggers': {
        'api.integration_events': {
            'level': 'DEBUG',
        },
    },
}
```

---

## 📚 Full Documentation

See `INTEGRATION_TRIGGERS_GUIDE.md` for complete details.

---

## 🆘 Need Help?

1. Check `integration_example.py` for working examples
2. Review signal definitions in `integration_events.py`
3. Check logs for trigger execution
4. Read full documentation in `INTEGRATION_TRIGGERS_GUIDE.md`
