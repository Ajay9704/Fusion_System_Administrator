#!/usr/bin/env python
import os
import sys
import django

sys.path.append('C:\\Users\\Yadav\\OneDrive\\Documents\\work\\backup\\Fusion_System_Administrator\\Backend\\backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from api.models import AuthUser
from api.services import EmergencyAccessService

user = AuthUser.objects.first()
print(f"Testing with user: {user.username}")

try:
    requests = EmergencyAccessService.get_user_requests(user)
    print(f"SUCCESS: Got {requests.count()} requests")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
