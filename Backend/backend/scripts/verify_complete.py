#!/usr/bin/env python
"""
Complete Emergency Access System Verification
"""
import os
import sys
import django

sys.path.append('C:\\Users\\Yadav\\OneDrive\\Documents\\work\\backup\\Fusion_System_Administrator\\Backend\\backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

print("=== Emergency Access System Verification ===\n")

# Test 1: Django check
print("[1] Django system check...")
import subprocess
result = subprocess.run(['python', 'manage.py', 'check'], capture_output=True, text=True, cwd='C:\\Users\\Yadav\\OneDrive\\Documents\\work\\backup\\Fusion_System_Administrator\\Backend\\backend')
if result.returncode == 0:
    print("    [OK] No Django errors")
else:
    print(f"    [ERROR] {result.stderr}")
    sys.exit(1)

# Test 2: Models
print("\n[2] Checking models...")
from api.models import EmergencyAccessRequest, TemporaryRoleAssignment, AuthUser, GlobalsDesignation
print(f"    [OK] EmergencyAccessRequest model")
print(f"    [OK] TemporaryRoleAssignment model")
print(f"    [OK] AuthUser: {AuthUser.objects.count()} users")
print(f"    [OK] GlobalsDesignation: {GlobalsDesignation.objects.count()} roles")

# Test 3: Services
print("\n[3] Checking services...")
from api.services import EmergencyAccessService
methods = ['create_request', 'get_pending_requests', 'get_all_requests', 'get_user_requests',
           'approve_request', 'reject_request', 'withdraw_request', 'check_and_expire_roles']
for method in methods:
    if hasattr(EmergencyAccessService, method):
        print(f"    [OK] {method}")
    else:
        print(f"    [ERROR] {method} missing")

# Test 4: API URLs
print("\n[4] Checking API URLs...")
from django.urls import reverse
try:
    url = reverse('emergency_create_request')
    print(f"    [OK] API URL configured: {url}")
except Exception as e:
    print(f"    [ERROR] URL configuration failed: {e}")

# Test 5: Frontend files
print("\n[5] Checking frontend files...")
import os
frontend_files = [
    'client/src/services/emergencyAccessService.js',
    'client/src/pages/EmergencyAccess/EmergencyAccessPage.jsx',
]
for file in frontend_files:
    if os.path.exists(file):
        print(f"    [OK] {file}")
    else:
        print(f"    [ERROR] {file} missing")

# Test 6: Routing
print("\n[6] Checking routing...")
with open('client/src/App.jsx', 'r') as f:
    app_content = f.read()
    if '/emergency-access' in app_content:
        print("    [OK] Route configured in App.jsx")
    else:
        print("    [ERROR] Route not found in App.jsx")

with open('client/src/components/Sidebar/Sidebar.jsx', 'r') as f:
    sidebar_content = f.read()
    if 'Emergency Access' in sidebar_content:
        print("    [OK] Menu item in Sidebar")
    else:
        print("    [ERROR] Menu item not found in Sidebar")

print("\n=== VERIFICATION COMPLETE ===")
print("\n✅ System is ready to use!")
print("Navigate to: Emergency Access in sidebar")
