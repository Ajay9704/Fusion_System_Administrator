"""
Business Rule Tests for Super Admin Module
Tests all constraints, validations, permissions, and policies
"""
from .conftest import BaseModuleTestCase
from api.models import (
    GlobalsExtrainfo, GlobalsDesignation,
    GlobalsHoldsdesignation, EmergencyAccessRequest,
    TemporaryRoleAssignment, AuditLog
)
from django.utils import timezone
from datetime import timedelta
import json

class TestBR01_BlockedUserCannotLogin(BaseModuleTestCase):
    """BR-1: Blocked users cannot authenticate regardless of roles"""

    def test_valid_active_user_login(self):
        """Valid: Active user with admin role attempts login"""
        self._test_id = "BR-1-V-01"
        self._br_id = "BR-1"
        self._test_category = "Valid"
        self._input_action = "Active user with admin role attempts login"
        self._expected_result = "Login successful"

        response = self.api_post('/auth/login/', {
            'username': 'testadmin',
            'password': 'testpass123'
        }, expected_status=None)

        if response.status_code == 200:
            self._record_result("Active user login successful", "Pass", "200 OK")
        else:
            self._record_result(f"Active user login failed: {response.status_code}", "Fail", str(response.status_code))

    def test_invalid_blocked_user_login(self):
        """Invalid: Blocked user (even with admin role) attempts login"""
        self._test_id = "BR-1-I-01"
        self._br_id = "BR-1"
        self._test_category = "Invalid"
        self._input_action = "Blocked user attempts login"
        self._expected_result = "Login rejected with 403"

        # Block the admin user
        admin_extra = GlobalsExtrainfo.objects.get(user=self.admin_user)
        admin_extra.user_status = 'BLOCKED'
        admin_extra.save()

        # Try to login
        response = self.api_post('/auth/login/', {
            'username': 'testadmin',
            'password': 'testpass123'
        }, expected_status=None)

        if response.status_code == 403:
            self._record_result("Blocked user login correctly rejected", "Pass", "403 Forbidden")
        else:
            self._record_result(f"Blocked user login not rejected: {response.status_code}", "Fail", str(response.status_code))

        # Cleanup
        admin_extra.user_status = 'ACTIVE'
        admin_extra.save()


class TestBR02_EmergencyRoleExpiration(BaseModuleTestCase):
    """BR-2: Emergency roles automatically expire after approved duration"""

    def test_valid_active_emergency_role(self):
        """Valid: User with active emergency role (within time limit)"""
        self._test_id = "BR-2-V-01"
        self._br_id = "BR-2"
        self._test_category = "Valid"
        self._input_action = "User with active emergency role attempts to access system"
        self._expected_result = "Emergency role included in user's active roles"

        # Create and approve emergency request
        self.login_as_staff()
        response = self.api_post('/emergency-access/request/', {
            'role': self.director_role.id,
            'requested_duration': 60,
            'reason': 'Test'
        })
        request_id = response.json().get('id') if hasattr(response, 'json') else response.data.get('id')

        self.logout()
        self.login_as_admin()
        self.api_post(f'/emergency-access/approve/{request_id}/', {'approved_duration': 60})

        # Get roles immediately (should include temporary role)
        self.logout()
        self.login_as_staff()
        response = self.api_get(f'/rbac/roles/?username=teststaff')

        data = response.json() if hasattr(response, 'json') else response.data
        roles = data.get('roles', [])
        role_types = [r.get('role_type') for r in roles]

        if 'temporary' in role_types:
            self._record_result("Active emergency role correctly included", "Pass", "Temporary role present")
        else:
            self._record_result("Active emergency role not included", "Fail", f"Role types: {role_types}")

    def test_invalid_expired_emergency_role(self):
        """Invalid: User attempts to use expired emergency role"""
        self._test_id = "BR-2-I-01"
        self._br_id = "BR-2"
        self._test_category = "Invalid"
        self._input_action = "User with expired emergency role attempts access"
        self._expected_result = "Emergency role not included in active roles"

        # Create and approve emergency request
        self.login_as_staff()
        response = self.api_post('/emergency-access/request/', {
            'role': self.director_role.id,
            'requested_duration': 1,  # 1 minute for quick expiry
            'reason': 'Test'
        })
        request_id = response.json().get('id') if hasattr(response, 'json') else response.data.get('id')

        self.logout()
        self.login_as_admin()
        self.api_post(f'/emergency-access/approve/{request_id}/', {'approved_duration': 1})

        # Manually expire the role by setting expires_at to past
        temp_role = TemporaryRoleAssignment.objects.get(request_id=request_id)
        temp_role.expires_at = timezone.now() - timedelta(minutes=1)
        temp_role.save()

        # Get roles (should not include expired temporary role)
        self.logout()
        self.login_as_staff()
        response = self.api_get(f'/rbac/roles/?username=teststaff')

        data = response.json() if hasattr(response, 'json') else response.data
        roles = data.get('roles', [])
        role_types = [r.get('role_type') for r in roles]

        if 'temporary' not in role_types:
            self._record_result("Expired emergency role correctly excluded", "Pass", "Only permanent roles shown")
        else:
            self._record_result("Expired emergency role still included", "Fail", f"Role types: {role_types}")


class TestBR04_EmergencyRequestRequiresValidRole(BaseModuleTestCase):
    """BR-4: Emergency access requests must reference valid existing roles"""

    def test_valid_emergency_request(self):
        """Valid: Submit emergency request for valid role"""
        self._test_id = "BR-4-V-01"
        self._br_id = "BR-4"
        self._test_category = "Valid"
        self._input_action = "Submit emergency request for valid role (director)"
        self._expected_result = "Request created successfully"

        self.login_as_staff()
        response = self.api_post('/emergency-access/request/', {
            'role': self.director_role.id,
            'requested_duration': 60,
            'reason': 'Valid emergency request'
        }, expected_status=None)

        if response.status_code in [200, 201]:
            self._record_result("Valid emergency request accepted", "Pass", "Request created")
        else:
            self._record_result(f"Valid request rejected: {response.status_code}", "Fail", str(response.status_code))

    def test_invalid_emergency_request_nonexistent_role(self):
        """Invalid: Submit emergency request for non-existent role"""
        self._test_id = "BR-4-I-01"
        self._br_id = "BR-4"
        self._test_category = "Invalid"
        self._input_action = "Submit emergency request for non-existent role"
        self._expected_result = "Request rejected with 404"

        self.login_as_staff()
        response = self.api_post('/emergency-access/request/', {
            'role': 99999,  # Non-existent role
            'requested_duration': 60,
            'reason': 'Test'
        }, expected_status=None)

        if response.status_code == 404:
            self._record_result("Non-existent role correctly rejected", "Pass", "404 Not Found")
        else:
            self._record_result(f"Non-existent role not rejected: {response.status_code}", "Fail", str(response.status_code))


class TestBR05_EmergencyDurationConstraints(BaseModuleTestCase):
    """BR-5: Emergency access duration must be positive and reasonable"""

    def test_valid_positive_duration(self):
        """Valid: Submit emergency request with duration=60"""
        self._test_id = "BR-5-V-01"
        self._br_id = "BR-5"
        self._test_category = "Valid"
        self._input_action = "Submit emergency request with duration=60"
        self._expected_result = "Request accepted"

        self.login_as_staff()
        response = self.api_post('/emergency-access/request/', {
            'role': self.director_role.id,
            'requested_duration': 60,
            'reason': 'Test'
        }, expected_status=None)

        if response.status_code in [200, 201]:
            self._record_result("Positive duration accepted", "Pass", "Request created")
        else:
            self._record_result(f"Positive duration rejected: {response.status_code}", "Fail", str(response.status_code))

    def test_invalid_zero_duration(self):
        """Invalid: Submit emergency request with duration=0"""
        self._test_id = "BR-5-I-01"
        self._br_id = "BR-5"
        self._test_category = "Invalid"
        self._input_action = "Submit emergency request with duration=0"
        self._expected_result = "Request rejected with validation error"

        self.login_as_staff()
        response = self.api_post('/emergency-access/request/', {
            'role': self.director_role.id,
            'requested_duration': 0,
            'reason': 'Test'
        }, expected_status=None)

        if response.status_code in [400, 422]:
            self._record_result("Zero duration correctly rejected", "Pass", "Validation error")
        else:
            self._record_result(f"Zero duration not rejected: {response.status_code}", "Fail", str(response.status_code))


class TestBR07_InactiveAccountCannotLogin(BaseModuleTestCase):
    """BR-7: Inactive accounts (is_active=False) cannot authenticate"""

    def test_valid_active_account_login(self):
        """Valid: Active user (is_active=True) attempts login"""
        self._test_id = "BR-7-V-01"
        self._br_id = "BR-7"
        self._test_category = "Valid"
        self._input_action = "Active user attempts login"
        self._expected_result = "Login successful"

        response = self.api_post('/auth/login/', {
            'username': 'testadmin',
            'password': 'testpass123'
        }, expected_status=None)

        if response.status_code == 200:
            self._record_result("Active account login successful", "Pass", "200 OK")
        else:
            self._record_result(f"Active account login failed: {response.status_code}", "Fail", str(response.status_code))

    def test_invalid_inactive_account_login(self):
        """Invalid: Inactive user (is_active=False) attempts login"""
        self._test_id = "BR-7-I-01"
        self._br_id = "BR-7"
        self._test_category = "Invalid"
        self._input_action = "Inactive user attempts login"
        self._expected_result = "Login rejected with 403"

        # Deactivate the user
        self.admin_user.is_active = False
        self.admin_user.save()

        # Try to login
        response = self.api_post('/auth/login/', {
            'username': 'testadmin',
            'password': 'testpass123'
        }, expected_status=None)

        if response.status_code == 403:
            self._record_result("Inactive account login correctly rejected", "Pass", "403 Forbidden")
        else:
            self._record_result(f"Inactive account not rejected: {response.status_code}", "Fail", str(response.status_code))

        # Cleanup
        self.admin_user.is_active = True
        self.admin_user.save()


class TestBR08_OnlyAdminCanApproveRequests(BaseModuleTestCase):
    """BR-8: Emergency access approval requires admin role"""

    def test_valid_admin_approves_request(self):
        """Valid: Admin user approves emergency request"""
        self._test_id = "BR-8-V-01"
        self._br_id = "BR-8"
        self._test_category = "Valid"
        self._input_action = "Admin user approves emergency request"
        self._expected_result = "Request approved"

        # Create request
        self.login_as_staff()
        response = self.api_post('/emergency-access/request/', {
            'role': self.director_role.id,
            'requested_duration': 60,
            'reason': 'Test'
        })
        request_id = response.json().get('id') if hasattr(response, 'json') else response.data.get('id')

        # Approve as admin
        self.logout()
        self.login_as_admin()
        response = self.api_post(f'/emergency-access/approve/{request_id}/', {
            'approved_duration': 60
        }, expected_status=None)

        if response.status_code in [200, 202]:
            self._record_result("Admin approval successful", "Pass", "Request approved")
        else:
            self._record_result(f"Admin approval failed: {response.status_code}", "Fail", str(response.status_code))

    def test_invalid_non_admin_approves_request(self):
        """Invalid: Non-admin user attempts to approve emergency request"""
        self._test_id = "BR-8-I-01"
        self._br_id = "BR-8"
        self._test_category = "Invalid"
        self._input_action = "Non-admin user attempts to approve emergency request"
        self._expected_result = "Request rejected with 403"

        # Create request
        self.login_as_staff()
        response = self.api_post('/emergency-access/request/', {
            'role': self.director_role.id,
            'requested_duration': 60,
            'reason': 'Test'
        })
        request_id = response.json().get('id') if hasattr(response, 'json') else response.data.get('id')

        # Try to approve as non-admin (staff user)
        # Note: staff_user is already logged in, so try to approve directly
        response = self.api_post(f'/emergency-access/approve/{request_id}/', {
            'approved_duration': 60
        }, expected_status=None)

        if response.status_code == 403:
            self._record_result("Non-admin approval correctly rejected", "Pass", "403 Forbidden")
        else:
            self._record_result(f"Non-admin approval not rejected: {response.status_code}", "Fail", str(response.status_code))
