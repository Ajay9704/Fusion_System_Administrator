"""
API Endpoint Tests
Tests for all API endpoints with authentication and authorization
"""

from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from .conftest import BaseModuleTestCase, APITestCase


class DepartmentAPITests(APITestCase):
    """Test department-related API endpoints"""

    def test_get_all_departments(self):
        """Test getting all academic departments"""
        response = self.api_get('/api/departments/')
        self.assertEqual(len(response.data), 1)  # Only CSE is academic

    def test_get_all_departments_admin(self):
        """Test getting all departments including administrative"""
        self.login_as_staff()
        response = self.api_get('/api/departments/all/')
        self.assertGreaterEqual(len(response.data), 2)  # CSE and ECE

    def test_get_departments_by_programme(self):
        """Test filtering departments by programme"""
        response = self.api_get('/api/departments/by-programme/?programme=B.Tech')
        self.assert_success_response(response)

    def test_create_department_unauthorized(self):
        """Test department creation without authentication"""
        response = self.client.post('/api/departments/create/', {
            'name': 'Mechanical Engineering'
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_department_authorized(self):
        """Test department creation with proper authentication"""
        self.login_as_faculty()
        response = self.api_post('/api/departments/create/', {
            'name': 'Mechanical Engineering'
        })
        self.assert_success_response(response)


class UserManagementAPITests(APITestCase):
    """Test user management API endpoints"""

    def test_get_user_roles_by_username(self):
        """Test getting user roles by username"""
        response = self.api_get(f'/api/get-user-roles-by-username/?username={self.student_user.username}')
        self.assert_success_response(response)
        self.assertIn('user', response.data)
        self.assertIn('roles', response.data)

    def test_get_nonexistent_user_roles(self):
        """Test getting roles for non-existent user"""
        response = self.api_get('/api/get-user-roles-by-username/?username=nonexistent')
        self.assert_error_response(response, status.HTTP_404_NOT_FOUND)

    def test_update_user_roles_unauthorized(self):
        """Test role update without authentication"""
        response = self.client.put('/api/update-user-roles/', {
            'username': self.student_user.username,
            'roles': ['student']
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_user_roles_authorized(self):
        """Test role update with proper authentication"""
        self.login_as_faculty()
        response = self.api_put('/api/update-user-roles/', {
            'username': self.student_user.username,
            'roles': []
        })
        self.assert_success_response(response)

    def test_reset_password_unauthorized(self):
        """Test password reset without authentication"""
        response = self.client.post('/api/users/reset_password/', {
            'username': self.student_user.username,
            'new_password': 'new123'
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class RoleManagementAPITests(APITestCase):
    """Test role management API endpoints"""

    def test_get_all_designations(self):
        """Test getting all designations"""
        response = self.api_get('/api/view-roles/')
        self.assert_success_response(response)
        self.assertGreater(len(response.data), 0)

    def test_get_designations_by_category(self):
        """Test getting designations by category"""
        response = self.api_post('/api/view-designations/', {
            'category': 'student',
            'basic': True
        })
        self.assert_success_response(response)

    def test_create_designation_unauthorized(self):
        """Test designation creation without authentication"""
        response = self.client.post('/api/create-role/', {
            'name': 'new_role',
            'full_name': 'New Role',
            'type': 'test',
            'category': 'test',
            'basic': True
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_designation_authorized(self):
        """Test designation creation with proper authentication"""
        self.login_as_faculty()
        response = self.api_post('/api/create-role/', {
            'name': 'test_role',
            'full_name': 'Test Role',
            'type': 'test',
            'category': 'test',
            'basic': True
        })
        self.assert_success_response(response)

    def test_get_module_access(self):
        """Test getting module access for designation"""
        response = self.api_get(f'/api/get-module-access/?designation={self.student_designation.name}')
        self.assert_success_response(response)


class AcademicAPITests(APITestCase):
    """Test academic information API endpoints"""

    def test_get_all_batches(self):
        """Test getting all batches"""
        response = self.api_get('/api/batches/')
        self.assert_success_response(response)
        self.assertGreater(len(response.data), 0)

    def test_get_all_programmes(self):
        """Test getting all programmes"""
        response = self.api_get('/api/programmes/')
        self.assert_success_response(response)
        self.assertGreater(len(response.data), 0)


class AuthenticationAPITests(APITestCase):
    """Test authentication API endpoints"""

    def test_login_valid_credentials(self):
        """Test login with valid credentials"""
        response = self.api_post('/api/auth/login/', {
            'username': '2021BCS001',
            'password': 'test123'
        })
        self.assert_success_response(response)
        self.assertIn('token', response.data)

    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = self.api_post('/api/auth/login/', {
            'username': '2021BCS001',
            'password': 'wrongpassword'
        })
        self.assert_error_response(response, status.HTTP_401_UNAUTHORIZED)

    def test_get_current_user_authenticated(self):
        """Test getting current user when authenticated"""
        self.login_as_student()
        response = self.api_get('/api/auth/me/')
        self.assert_success_response(response)
        self.assertEqual(response.data['username'], '2021BCS001')

    def test_get_current_user_unauthenticated(self):
        """Test getting current user when not authenticated"""
        response = self.api_get('/api/auth/me/')
        self.assert_error_response(response, status.HTTP_401_UNAUTHORIZED)

    def test_logout_authenticated(self):
        """Test logout when authenticated"""
        self.login_as_student()
        response = self.api_post('/api/auth/logout/')
        self.assert_success_response(response)


class EmergencyAccessAPITests(APITestCase):
    """Test emergency access API endpoints"""

    def test_request_emergency_access(self):
        """Test emergency access request creation"""
        self.login_as_student()
        response = self.api_post('/api/emergency-access/request/', {
            'requested_role': self.hod_designation.id,
            'reason': 'Emergency access needed for critical task',
            'duration_hours': 24
        })
        self.assert_success_response(response)

    def test_list_emergency_requests_unauthorized(self):
        """Test listing emergency requests without authentication"""
        response = self.api_get('/api/emergency-access/requests/')
        self.assert_error_response(response, status.HTTP_401_UNAUTHORIZED)

    def test_approve_emergency_access_authorized(self):
        """Test emergency access approval by authorized user"""
        # First create a request
        emergency = EmergencyAccess.objects.create(
            requester=self.student_user,
            requested_role=self.hod_designation,
            reason='Emergency access needed',
            duration_hours=24
        )

        # Then approve it as faculty
        self.login_as_faculty()
        response = self.api_post(f'/api/emergency-access/{emergency.id}/approve/', {
            'status': 'APPROVED',
            'approval_reason': 'Access granted for emergency'
        })
        self.assert_success_response(response)


class HandoverDocumentationAPITests(APITestCase):
    """Test handover documentation API endpoints"""

    def test_create_handover(self):
        """Test handover documentation creation"""
        self.login_as_faculty()
        response = self.api_post('/api/handovers/create/', {
            'to_user': self.staff_user.id,
            'title': 'Department Handover',
            'description': 'Handover of department responsibilities',
            'department': self.cse_dept.id,
            'priority': 'HIGH'
        })
        self.assert_success_response(response)

    def test_list_handovers(self):
        """Test listing handover documents"""
        # Create a handover first
        HandoverDocumentation.objects.create(
            from_user=self.faculty_user,
            to_user=self.staff_user,
            title='Test Handover',
            description='Test handover description'
        )

        self.login_as_faculty()
        response = self.api_get('/api/handovers/')
        self.assert_success_response(response)

    def test_accept_handover(self):
        """Test handover acceptance"""
        handover = HandoverDocumentation.objects.create(
            from_user=self.faculty_user,
            to_user=self.staff_user,
            title='Test Handover',
            description='Test handover description',
            status='PENDING'
        )

        self.login_as_staff()
        response = self.api_post(f'/api/handovers/{handover.id}/accept/')
        self.assert_success_response(response)

    def test_complete_handover(self):
        """Test handover completion"""
        handover = HandoverDocumentation.objects.create(
            from_user=self.faculty_user,
            to_user=self.staff_user,
            title='Test Handover',
            description='Test handover description',
            status='IN_PROGRESS'
        )

        self.login_as_staff()
        response = self.api_post(f'/api/handovers/{handover.id}/complete/')
        self.assert_success_response(response)


class AuditLogAPITests(APITestCase):
    """Test audit log API endpoints"""

    def test_get_audit_logs_unauthorized(self):
        """Test getting audit logs without authentication"""
        response = self.api_get('/api/audit-logs/')
        self.assert_error_response(response, status.HTTP_401_UNAUTHORIZED)

    def test_get_audit_logs_authorized(self):
        """Test getting audit logs with proper authentication"""
        # Create some audit logs first
        AuditLog.objects.create(
            user=self.student_user,
            action='TEST_ACTION',
            description='Test audit log'
        )

        self.login_as_faculty()
        response = self.api_get('/api/audit-logs/')
        self.assert_success_response(response)
        self.assertGreater(len(response.data), 0)


# Import models needed for tests
from api.models import EmergencyAccess, HandoverDocumentation, AuditLog