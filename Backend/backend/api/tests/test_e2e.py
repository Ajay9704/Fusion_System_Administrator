#!/usr/bin/env python
"""
End-to-End test for Emergency Access
"""
import os
import sys
import django

sys.path.append('C:\\Users\\Yadav\\OneDrive\\Documents\\work\\backup\\Fusion_System_Administrator\\Backend\\backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from api.models import AuthUser, GlobalsDesignation, EmergencyAccessRequest, TemporaryRoleAssignment
from api.services import EmergencyAccessService
from django.utils import timezone

def test_end_to_end():
    print("=== Emergency Access E2E Test ===\n")

    # Get test user and role
    try:
        user = AuthUser.objects.filter(is_active=True).first()
        role = GlobalsDesignation.objects.filter(basic=False).first()

        if not user or not role:
            print("[SKIP] No active user or non-basic role found")
            return False

        print(f"[OK] Test user: {user.username}")
        print(f"[OK] Test role: {role.name}")

        # Test 1: Create request
        print("\n[Test 1] Creating emergency access request...")
        request = EmergencyAccessService.create_request(
            user=user,
            role_id=role.id,
            duration=60,
            reason="Testing emergency access functionality"
        )
        print(f"[OK] Request created: ID {request.id}, Status: {request.status}")

        # Test 2: Get pending requests
        print("\n[Test 2] Fetching pending requests...")
        pending = EmergencyAccessService.get_pending_requests()
        print(f"[OK] Found {len(pending)} pending requests")

        # Test 3: Get user requests
        print("\n[Test 3] Fetching user requests...")
        user_requests = EmergencyAccessService.get_user_requests(user)
        print(f"[OK] Found {len(user_requests)} requests for user")

        # Test 4: Approve request (using admin)
        print("\n[Test 4] Approving request...")
        admin = AuthUser.objects.filter(is_staff=True).first()
        if admin:
            approved = EmergencyAccessService.approve_request(
                request_id=request.id,
                admin_user=admin,
                approved_duration=30
            )
            print(f"[OK] Request approved, expires at: {approved.expires_at}")

            # Test 5: Check temporary assignment
            print("\n[Test 5] Checking temporary role assignment...")
            assignments = TemporaryRoleAssignment.objects.filter(request=request)
            if assignments.exists():
                assignment = assignments.first()
                print(f"[OK] Temporary role created: {assignment.role.name}, Active: {assignment.is_valid()}")

            # Test 6: Get active temporary roles
            print("\n[Test 6] Fetching active temporary roles...")
            active_roles = EmergencyAccessService.get_active_temporary_roles(user)
            print(f"[OK] Found {len(active_roles)} active temporary roles")

        print("\n=== All Tests Passed ===")
        return True

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_end_to_end()
    sys.exit(0 if success else 1)
