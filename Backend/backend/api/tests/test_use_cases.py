"""
Use Case Tests for Super Admin Module
Tests all functional features as per UC specifications
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

class TestUC01_UserAuthentication(BaseModuleTestCase):
    """UC-1: User Login Authentication"""

    def test_hp01_valid_login(self):
        """Happy Path: User logs in with valid username and password"""
        self._test_id = "UC-1-HP-01"
        self._uc_id = "UC-1"
        self._test_category = "Happy Path"
        self._scenario = "User logs in with valid username and password"
        self._preconditions = "User account is active and not blocked"
        self._input_action = "POST /auth/login/ with valid username and password"
        self._expected_result = "Login successful, returns tokens with user roles"

        # Login with valid credentials
        response = self.api_post('/auth/login/', {
            'username': 'testadmin',
            'password': 'testpass123'
        }, expected_status=None)

        data = response.json() if hasattr(response, 'json') else response.data

        if response.status_code == 200:
            if 'access' in data and 'refresh' in data and 'roles' in data.get('user', {}):
                self._record_result("Login successful with tokens and roles", "Pass", json.dumps(data))
            else:
                self._record_result(f"Login successful but missing fields: {data}", "Partial", json.dumps(data))
        else:
            self._record_result(f"Login failed with status {response.status_code}: {data}", "Fail", str(data))
            self.fail(f"Expected 200, got {response.status_code}")

    def test_ap01_login_with_email(self):
        """Alternate Path: User logs in with email instead of username"""
        self._test_id = "UC-1-AP-01"
        self._uc_id = "UC-1"
        self._test_category = "Alternate Path"
        self._scenario = "User logs in with email instead of username"
        self._preconditions = "User account is active"
        self._input_action = "POST /auth/login/ with email instead of username"
        self._expected_result = "Login successful, same response format"

        response = self.api_post('/auth/login/', {
            'username': 'admin@test.com',  # Using email as username
            'password': 'testpass123'
        }, expected_status=None)

        data = response.json() if hasattr(response, 'json') else response.data

        if response.status_code == 200:
            self._record_result("Email login successful", "Pass", json.dumps(data))
        else:
            # Email login might not be implemented, that's okay
            self._record_result(f"Email login not supported: {response.status_code}", "Partial", str(data))

    def test_ex01_invalid_password(self):
        """Exception: User attempts login with invalid password"""
        self._test_id = "UC-1-EX-01"
        self._uc_id = "UC-1"
        self._test_category = "Exception"
        self._scenario = "User attempts login with invalid password"
        self._preconditions = "User account exists"
        self._input_action = "POST /auth/login/ with incorrect password"
        self._expected_result = "Login failed with 401 Unauthorized"

        response = self.api_post('/auth/login/', {
            'username': 'testadmin',
            'password': 'wrongpassword'
        }, expected_status=None)

        if response.status_code == 401:
            self._record_result("Correctly rejected invalid password", "Pass", "401 Unauthorized")
        else:
            self._record_result(f"Expected 401, got {response.status_code}", "Fail", str(response.status_code))


class TestUC02_EmergencyRoleRequest(BaseModuleTestCase):
    """UC-2: Request Emergency Role Access"""

    def test_hp01_request_director_role(self):
        """Happy Path: User requests temporary director role for 60 minutes"""
        self._test_id = "UC-2-HP-01"
        self._uc_id = "UC-2"
        self._test_category = "Happy Path"
        self._scenario = "User requests temporary director role for 60 minutes"
        self._preconditions = "User is logged in, director role exists"
        self._input_action = "POST /emergency-access/request/ with role=director, duration=60"
        self._expected_result = "Request created with status=PENDING"

        self.login_as_staff()
        response = self.api_post('/emergency-access/request/', {
            'role': self.director_role.id,
            'requested_duration': 60,
            'reason': 'Emergency access for urgent administrative task'
        }, expected_status=None)

        data = response.json() if hasattr(response, 'json') else response.data

        if response.status_code in [200, 201]:
            if data.get('status') == 'PENDING':
                self._record_result("Emergency request created successfully", "Pass", json.dumps(data))
            else:
                self._record_result(f"Request created but status is {data.get('status')}", "Partial", json.dumps(data))
        else:
            self._record_result(f"Request creation failed: {data}", "Fail", str(data))

    def test_ap01_request_different_role(self):
        """Alternate Path: User requests different role type (fee_collector)"""
        self._test_id = "UC-2-AP-01"
        self._uc_id = "UC-2"
        self._test_category = "Alternate Path"
        self._scenario = "User requests fee_collector role"
        self._preconditions = "User is logged in, role exists"
        self._input_action = "POST /emergency-access/request/ with role=fee_collector"
        self._expected_result = "Request created successfully"

        self.login_as_staff()
        response = self.api_post('/emergency-access/request/', {
            'role': self.fee_collector_role.id,
            'requested_duration': 30,
            'reason': 'Need fee collection access'
        }, expected_status=None)

        if response.status_code in [200, 201]:
            self._record_result("Different role request successful", "Pass", "Request created")
        else:
            self._record_result(f"Different role request failed: {response.status_code}", "Fail", str(response.status_code))

    def test_ex01_request_nonexistent_role(self):
        """Exception: User requests non-existent role"""
        self._test_id = "UC-2-EX-01"
        self._uc_id = "UC-2"
        self._test_category = "Exception"
        self._scenario = "User requests non-existent role"
        self._preconditions = "User is logged in"
        self._input_action = "POST /emergency-access/request/ with invalid role ID"
        self._expected_result = "Request rejected with 404"

        self.login_as_staff()
        response = self.api_post('/emergency-access/request/', {
            'role': 99999,  # Non-existent role ID
            'requested_duration': 60,
            'reason': 'Test'
        }, expected_status=None)

        if response.status_code == 404:
            self._record_result("Correctly rejected non-existent role", "Pass", "404 Not Found")
        else:
            self._record_result(f"Expected 404, got {response.status_code}", "Fail", str(response.status_code))


class TestUC03_ApproveEmergencyRequest(BaseModuleTestCase):
    """UC-3: Approve Emergency Access Request"""

    def setUp(self):
        super().setUp()
        # Create a pending emergency request
        self.login_as_staff()
        response = self.api_post('/emergency-access/request/', {
            'role': self.director_role.id,
            'requested_duration': 60,
            'reason': 'Emergency access'
        })
        self.request_id = response.json().get('id') if hasattr(response, 'json') else response.data.get('id')
        self.logout()

    def test_hp01_admin_approves_request(self):
        """Happy Path: Admin approves pending emergency request"""
        self._test_id = "UC-3-HP-01"
        self._uc_id = "UC-3"
        self._test_category = "Happy Path"
        self._scenario = "Admin approves pending emergency request"
        self._preconditions = "Admin is logged in, pending request exists"
        self._input_action = "POST /emergency-access/approve/{request_id}/"
        self._expected_result = "Request approved, TemporaryRoleAssignment created"

        self.login_as_admin()
        response = self.api_post(f'/emergency-access/approve/{self.request_id}/', {
            'approved_duration': 60
        }, expected_status=None)

        data = response.json() if hasattr(response, 'json') else response.data

        if response.status_code in [200, 202]:
            if data.get('status') == 'APPROVED':
                # Check if TemporaryRoleAssignment was created
                if TemporaryRoleAssignment.objects.filter(request_id=self.request_id).exists():
                    self._record_result("Request approved and temporary assignment created", "Pass", json.dumps(data))
                else:
                    self._record_result("Request approved but no temporary assignment found", "Partial", json.dumps(data))
            else:
                self._record_result(f"Request status is {data.get('status')}", "Partial", json.dumps(data))
        else:
            self._record_result(f"Approval failed: {data}", "Fail", str(data))

    def test_ap01_admin_approves_with_modified_duration(self):
        """Alternate Path: Admin approves with modified duration"""
        self._test_id = "UC-3-AP-01"
        self._uc_id = "UC-3"
        self._test_category = "Alternate Path"
        self._scenario = "Admin approves with modified duration (120 instead of 60)"
        self._input_action = "POST /emergency-access/approve/{request_id}/ with approved_duration=120"
        self._expected_result = "Request approved with modified duration"

        self.login_as_admin()
        response = self.api_post(f'/emergency-access/approve/{self.request_id}/', {
            'approved_duration': 120
        }, expected_status=None)

        if response.status_code in [200, 202]:
            # Check if the duration was modified
            temp_role = TemporaryRoleAssignment.objects.filter(request_id=self.request_id).first()
            if temp_role:
                expiry_window = temp_role.expires_at - timezone.now()
                if 115 < expiry_window.total_seconds() / 60 < 125:  # Around 120 minutes
                    self._record_result("Request approved with modified duration", "Pass", "Duration set to ~120 minutes")
                else:
                    self._record_result(f"Duration not properly set: {expiry_window}", "Partial", str(expiry_window))
            else:
                self._record_result("No temporary role assignment found", "Fail", "Missing assignment")
        else:
            self._record_result(f"Approval with modified duration failed: {response.status_code}", "Fail", str(response.status_code))

    def test_ex01_approve_already_approved_request(self):
        """Exception: Admin tries to approve already approved request"""
        self._test_id = "UC-3-EX-01"
        self._uc_id = "UC-3"
        self._test_category = "Exception"
        self._scenario = "Admin tries to approve already approved request"
        self._input_action = "POST /emergency-access/approve/{request_id}/ (already approved)"
        self._expected_result = "Request rejected with error"

        # First approval
        self.login_as_admin()
        self.api_post(f'/emergency-access/approve/{self.request_id}/', {'approved_duration': 60})
        self.logout()

        # Try to approve again
        self.login_as_admin()
        response = self.api_post(f'/emergency-access/approve/{self.request_id}/', {
            'approved_duration': 60
        }, expected_status=None)

        if response.status_code in [400, 404, 409]:
            self._record_result("Correctly rejected duplicate approval", "Pass", f"Status {response.status_code}")
        else:
            self._record_result(f"Duplicate approval should be rejected, got {response.status_code}", "Fail", str(response.status_code))


class TestUC04_ViewUserRoles(BaseModuleTestCase):
    """UC-4: View All User Roles Including Temporary"""

    def test_hp01_view_permanent_and_temporary_roles(self):
        """Happy Path: User views roles showing both permanent and temporary"""
        self._test_id = "UC-4-HP-01"
        self._uc_id = "UC-4"
        self._test_category = "Happy Path"
        self._scenario = "User views roles with both permanent and temporary assignments"
        self._preconditions = "User has permanent roles and active temporary role"
        self._input_action = "GET /rbac/roles/?username={username}"
        self._expected_result = "Returns all roles with role_type field"

        # Create emergency request and approve it to get temporary role
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

        # Now get roles
        self.logout()
        self.login_as_staff()
        response = self.api_get(f'/rbac/roles/?username=teststaff')

        data = response.json() if hasattr(response, 'json') else response.data

        if response.status_code == 200:
            roles = data.get('roles', [])
            role_types = [r.get('role_type') for r in roles]

            if 'permanent' in role_types and 'temporary' in role_types:
                self._record_result("Both permanent and temporary roles shown", "Pass", json.dumps(roles))
            elif 'permanent' in role_types:
                self._record_result("Only permanent roles shown", "Partial", json.dumps(roles))
            else:
                self._record_result(f"Unexpected role types: {role_types}", "Fail", json.dumps(roles))
        else:
            self._record_result(f"Failed to get roles: {response.status_code}", "Fail", str(response.status_code))

    def test_ap01_view_only_permanent_roles(self):
        """Alternate Path: User views roles with only permanent assignments"""
        self._test_id = "UC-4-AP-01"
        self._uc_id = "UC-4"
        self._test_category = "Alternate Path"
        self._scenario = "User views roles with only permanent role assignments"
        self._input_action = "GET /rbac/roles/?username={username} (no temporary roles)"
        self._expected_result = "Returns only permanent roles"

        self.login_as_admin()
        response = self.api_get('/rbac/roles/?username=testadmin')

        data = response.json() if hasattr(response, 'json') else response.data

        if response.status_code == 200:
            roles = data.get('roles', [])
            role_types = [r.get('role_type') for r in roles]

            if all(rt == 'permanent' for rt in role_types):
                self._record_result("Only permanent roles shown correctly", "Pass", json.dumps(roles))
            else:
                self._record_result(f"Found non-permanent roles: {role_types}", "Partial", json.dumps(roles))
        else:
            self._record_result(f"Failed to get roles: {response.status_code}", "Fail", str(response.status_code))

    def test_ex01_view_roles_nonexistent_user(self):
        """Exception: User views roles for non-existent user"""
        self._test_id = "UC-4-EX-01"
        self._uc_id = "UC-4"
        self._test_category = "Exception"
        self._scenario = "User views roles for non-existent user"
        self._input_action = "GET /rbac/roles/?username=nonexistent_user"
        self._expected_result = "Returns 404 error"

        self.login_as_admin()
        response = self.api_get('/rbac/roles/?username=nonexistent_user', expected_status=None)

        if response.status_code == 404:
            self._record_result("Correctly returned 404 for non-existent user", "Pass", "404 Not Found")
        else:
            self._record_result(f"Expected 404, got {response.status_code}", "Fail", str(response.status_code))


class TestUC05_BlockUserAccess(BaseModuleTestCase):
    """UC-5: Block User from System Access"""

    def test_hp01_admin_blocks_active_user(self):
        """Happy Path: Admin blocks active user"""
        self._test_id = "UC-5-HP-01"
        self._uc_id = "UC-5"
        self._test_category = "Happy Path"
        self._scenario = "Admin blocks active user"
        self._preconditions = "Admin logged in, user is active"
        self._input_action = "POST /rbac/users/block/ with username and reason"
        self._expected_result = "User status changed to BLOCKED"

        self.login_as_admin()
        response = self.api_post('/rbac/users/block/', {
            'username': 'teststaff',
            'reason': 'Policy violation'
        }, expected_status=None)

        if response.status_code in [200, 202]:
            # Verify user is blocked
            extra = GlobalsExtrainfo.objects.get(user=self.staff_user)
            if extra.user_status == 'BLOCKED':
                self._record_result("User successfully blocked", "Pass", "User status = BLOCKED")
            else:
                self._record_result(f"User status is {extra.user_status}, not BLOCKED", "Fail", str(extra.user_status))
        else:
            self._record_result(f"Block request failed: {response.status_code}", "Fail", str(response.status_code))

        # Cleanup: unblock the user
        extra = GlobalsExtrainfo.objects.get(user=self.staff_user)
        extra.user_status = 'ACTIVE'
        extra.save()

    def test_ap01_admin_blocks_with_different_reason(self):
        """Alternate Path: Admin blocks user with different reason"""
        self._test_id = "UC-5-AP-01"
        self._uc_id = "UC-5"
        self._test_category = "Alternate Path"
        self._scenario = "Admin blocks user with security concern reason"
        self._input_action = "POST /rbac/users/block/ with reason='Security concern'"
        self._expected_result = "User blocked with reason recorded"

        self.login_as_admin()
        response = self.api_post('/rbac/users/block/', {
            'username': 'teststaff',
            'reason': 'Security concern'
        }, expected_status=None)

        if response.status_code in [200, 202]:
            # Check audit log for reason
            audit_log = AuditLog.objects.filter(
                action='USER_BLOCKED',
                description__contains='Security concern'
            ).exists()

            if audit_log:
                self._record_result("User blocked with reason recorded in audit", "Pass", "Audit log found")
            else:
                self._record_result("User blocked but audit log missing", "Partial", "No audit log")
        else:
            self._record_result(f"Block with different reason failed: {response.status_code}", "Fail", str(response.status_code))

        # Cleanup
        extra = GlobalsExtrainfo.objects.get(user=self.staff_user)
        extra.user_status = 'ACTIVE'
        extra.save()

    def test_ex01_admin_blocks_nonexistent_user(self):
        """Exception: Admin tries to block non-existent user"""
        self._test_id = "UC-5-EX-01"
        self._uc_id = "UC-5"
        self._test_category = "Exception"
        self._scenario = "Admin tries to block non-existent user"
        self._input_action = "POST /rbac/users/block/ with username=nonexistent"
        self._expected_result = "Request rejected with 404"

        self.login_as_admin()
        response = self.api_post('/rbac/users/block/', {
            'username': 'nonexistent_user',
            'reason': 'Test'
        }, expected_status=None)

        if response.status_code == 404:
            self._record_result("Correctly rejected with 404", "Pass", "404 Not Found")
        else:
            self._record_result(f"Expected 404, got {response.status_code}", "Fail", str(response.status_code))
