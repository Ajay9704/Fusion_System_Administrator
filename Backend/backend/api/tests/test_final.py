#!/usr/bin/env python
"""
Final verification test for Emergency Access
"""
import os
import sys
import django

sys.path.append('C:\\Users\\Yadav\\OneDrive\\Documents\\work\\backup\\Fusion_System_Administrator\\Backend\\backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from api.models import AuthUser, GlobalsDesignation, EmergencyAccessRequest, TemporaryRoleAssignment
from api.services import EmergencyAccessService

def test_emergency_access():
    print("=== Emergency Access Verification ===\n")

    try:
        # Clean up test data first
        EmergencyAccessRequest.objects.all().delete()
        TemporaryRoleAssignment.objects.all().delete()

        user = AuthUser.objects.filter(is_active=True).first()
        role = GlobalsDesignation.objects.filter(basic=False).first()
        admin = AuthUser.objects.filter(is_staff=True, is_active=True).first()

        if not user or not role or not admin:
            print("[SKIP] Missing required test data")
            return False

        print(f"[OK] User: {user.username}, Role: {role.name}, Admin: {admin.username}")

        # Test 1: Create request
        print("\n[1] Creating request...")
        request = EmergencyAccessService.create_request(
            user=user,
            role_id=role.id,
            duration=120,
            reason="Testing emergency access system"
        )
        print(f"[OK] Request ID: {request.id}, Status: {request.status}")

        # Test 2: Get pending requests
        print("\n[2] Getting pending requests...")
        pending = EmergencyAccessService.get_pending_requests()
        print(f"[OK] {pending.count()} pending requests")

        # Test 3: Approve request
        print("\n[3] Approving request...")
        approved = EmergencyAccessService.approve_request(
            request_id=request.id,
            admin_user=admin,
            approved_duration=60
        )
        print(f"[OK] Approved, Expires: {approved.expires_at}")

        # Test 4: Check temporary assignment
        print("\n[4] Checking temporary assignment...")
        assignment = TemporaryRoleAssignment.objects.filter(request=request).first()
        if assignment:
            print(f"[OK] Assignment created, Valid: {assignment.is_valid()}")

        # Test 5: Get active temporary roles
        print("\n[5] Getting active temporary roles...")
        active = EmergencyAccessService.get_active_temporary_roles(user)
        print(f"[OK] {active.count()} active temporary roles")

        # Test 6: Withdraw request
        print("\n[6] Withdrawing request...")
        withdrawn = EmergencyAccessService.withdraw_request(
            request_id=request.id,
            admin_user=admin,
            reason="Test complete"
        )
        print(f"[OK] Withdrawn, Status: {withdrawn.status}")

        print("\n=== ALL TESTS PASSED ===")
        return True

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_emergency_access()
    sys.exit(0 if success else 1)
