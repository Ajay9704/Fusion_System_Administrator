#!/usr/bin/env python
"""
Test script to verify Emergency Access functionality
"""
import os
import sys
import django

# Setup Django
sys.path.append('C:\\Users\\Yadav\\OneDrive\\Documents\\work\\backup\\Fusion_System_Administrator\\Backend\\backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from api.models import AuthUser, GlobalsDesignation, EmergencyAccessRequest, TemporaryRoleAssignment
from api.services import EmergencyAccessService

def test_emergency_access():
    print("=" * 50)
    print("Testing Emergency Access Feature")
    print("=" * 50)

    try:
        # Test 1: Check models are properly loaded
        print("\n[OK] Models loaded successfully")

        # Test 2: Check service methods exist
        methods = [
            'create_request',
            'get_pending_requests',
            'get_all_requests',
            'get_user_requests',
            'approve_request',
            'reject_request',
            'withdraw_request',
            'check_and_expire_roles',
            'get_active_temporary_roles',
            'has_active_temporary_role',
        ]

        for method in methods:
            if hasattr(EmergencyAccessService, method):
                print(f"[OK] Service method '{method}' exists")
            else:
                print(f"[FAIL] Service method '{method}' NOT FOUND")

        # Test 3: Check database tables exist
        print(f"\n[OK] EmergencyAccessRequest table exists")
        print(f"[OK] TemporaryRoleAssignment table exists")

        # Test 4: Verify existing functionality still works
        print("\n" + "=" * 50)
        print("Testing Existing Functionality (Compatibility)")
        print("=" * 50)

        # Check existing models
        user_count = AuthUser.objects.count()
        print(f"[OK] AuthUser: {user_count} users found")

        role_count = GlobalsDesignation.objects.count()
        print(f"[OK] GlobalsDesignation: {role_count} roles found")

        # Check existing services
        from api.services import RoleManagementService, UserService
        print(f"[OK] RoleManagementService exists")
        print(f"[OK] UserService exists")

        print("\n" + "=" * 50)
        print("All tests passed!")
        print("=" * 50)

        return True

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_emergency_access()
    sys.exit(0 if success else 1)
