#!/usr/bin/env python
import os
import sys
import django

sys.path.append('C:\\Users\\Yadav\\OneDrive\\Documents\\work\\backup\\Fusion_System_Administrator\\Backend\\backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from api.models import AuthUser, EmergencyAccessRequest

# Test the model method
user = AuthUser.objects.first()
print(f"Testing with user: {user.username}")

# Create a test request
from api.services import EmergencyAccessService

role_id = 1  # Use existing role
duration = 60
reason = "Testing API endpoint functionality"

try:
    request = EmergencyAccessService.create_request(user, role_id, duration, reason)
    print(f"Created request: {request.id}")

    # Test the is_active method
    print(f"Request status: {request.status}")
    print(f"Is active: {request.is_active()}")

    # Clean up
    request.delete()
    print("Test passed - API should work now")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
