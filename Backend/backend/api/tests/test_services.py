"""
Service Layer Tests
Tests for business logic in service classes
"""

from django.test import TestCase
from django.core.exceptions import ValidationError

from .conftest import BaseModuleTestCase
from api.services import UserService, RoleManagementService, ModuleAccessService


class UserServiceTests(BaseModuleTestCase):
    """Test user service business logic"""

    def test_create_student_user(self):
        """Test student creation service"""
        user_service = UserService()

        student_data = {
            'username': '2022BCS001',
            'email': 'newstudent@test.com',
            'first_name': 'John',
            'last_name': 'Doe',
            'programme': 'B.Tech',
            'batch': 2022,
            'category': 'GEN',
            'department': self.cse_dept.id
        }

        result = user_service.create_student(student_data)

        self.assertTrue(result['success'])
        self.assertIsNotNone(result['user'])
        self.assertEqual(result['user']['username'], '2022BCS001')

    def test_create_user_with_invalid_data(self):
        """Test user creation with invalid data"""
        user_service = UserService()

        invalid_data = {
            'username': '',  # Empty username
            'email': 'invalid-email'  # Invalid email format
        }

        result = user_service.create_student(invalid_data)

        self.assertFalse(result['success'])
        self.assertIn('error', result)

    def test_update_user_roles(self):
        """Test user role update service"""
        user_service = UserService()

        # Add another designation
        new_designation = GlobalsDesignation.objects.create(
            name='class_rep',
            full_name='Class Representative',
            type='student',
            basic=False,
            category='student'
        )

        result = user_service.update_user_roles(
            self.student_user.username,
            ['student', 'class_rep']
        )

        self.assertTrue(result['success'])
        self.assertEqual(
            GlobalsHoldsdesignation.objects.filter(user=self.student_user).count(),
            2
        )


class RoleManagementServiceTests(BaseModuleTestCase):
    """Test role management service"""

    def test_get_available_roles_for_student(self):
        """Test getting available roles for student type"""
        role_service = RoleManagementService()

        available_roles = role_service.get_available_roles('student')

        self.assertIn('student', available_roles)
        self.assertNotIn('hod', available_roles)  # HOD is not for students

    def test_check_role_conflicts(self):
        """Test role conflict detection"""
        role_service = RoleManagementService()

        # Try to assign HOD role to user who already has it
        conflicts = role_service.check_role_conflicts(
            self.faculty_user.id,
            self.hod_designation.id
        )

        # Since faculty_user already has HOD role, there should be no conflict
        # (user can hold the same role)
        self.assertEqual(len(conflicts), 0)

    def test_singular_role_validation(self):
        """Test singular role constraint validation"""
        role_service = RoleManagementService()

        # Try to assign HOD (singular) to another user
        another_user = AuthUser.objects.create_user(
            username='anotherfaculty',
            email='another@test.com',
            password='test123'
        )

        is_available = role_service.is_role_available(
            self.hod_designation.name,
            another_user
        )

        # HOD is singular and already held by faculty_user
        self.assertFalse(is_available)


class ModuleAccessServiceTests(BaseModuleTestCase):
    """Test module access service"""

    def test_get_module_access_for_designation(self):
        """Test getting module access permissions"""
        access_service = ModuleAccessService()

        module_access = access_service.get_module_access('student')

        self.assertIsNotNone(module_access)
        self.assertIn('program_and_curriculum', module_access)

    def test_check_module_permission(self):
        """Test checking specific module permission"""
        access_service = ModuleAccessService()

        # Students should have access to certain modules
        has_access = access_service.check_permission(
            'student',
            'program_and_curriculum'
        )

        self.assertTrue(has_access)

    def test_update_module_access(self):
        """Test updating module access permissions"""
        access_service = ModuleAccessService()

        updated_access = {
            'program_and_curriculum': True,
            'course_registration': True,
            'department': True,
            'hr': False  # Students shouldn't have HR access
        }

        result = access_service.update_module_access('student', updated_access)

        self.assertTrue(result['success'])


class EmergencyAccessServiceTests(BaseModuleTestCase):
    """Test emergency access service logic"""

    def test_request_emergency_access(self):
        """Test emergency access request"""
        from api.services import EmergencyAccessService

        emergency_service = EmergencyAccessService()

        request_data = {
            'requester': self.student_user,
            'requested_role': self.hod_designation,
            'reason': 'Critical emergency',
            'duration_hours': 24
        }

        result = emergency_service.create_request(request_data)

        self.assertTrue(result['success'])
        self.assertEqual(result['emergency_access'].status, 'PENDING')

    def test_approve_emergency_access(self):
        """Test emergency access approval"""
        from api.services import EmergencyAccessService

        emergency_service = EmergencyAccessService()

        # Create a request
        emergency_access = EmergencyAccess.objects.create(
            requester=self.student_user,
            requested_role=self.hod_designation,
            reason='Emergency access',
            duration_hours=24
        )

        # Approve it
        result = emergency_service.approve_request(
            emergency_access.id,
            self.faculty_user,
            'Access granted for emergency'
        )

        self.assertTrue(result['success'])
        self.assertEqual(result['emergency_access'].status, 'APPROVED')


class HandoverServiceTests(BaseModuleTestCase):
    """Test handover service logic"""

    def test_create_handover(self):
        """Test handover creation"""
        from api.services import HandoverService

        handover_service = HandoverService()

        handover_data = {
            'from_user': self.faculty_user,
            'to_user': self.staff_user,
            'title': 'Department Handover',
            'description': 'Handover of department responsibilities',
            'department': self.cse_dept,
            'priority': 'HIGH'
        }

        result = handover_service.create_handover(handover_data)

        self.assertTrue(result['success'])
        self.assertEqual(result['handover'].status, 'PENDING')

    def test_accept_handover(self):
        """Test handover acceptance"""
        from api.services import HandoverService

        handover_service = HandoverService()

        handover = HandoverDocumentation.objects.create(
            from_user=self.faculty_user,
            to_user=self.staff_user,
            title='Test Handover',
            description='Test description',
            status='PENDING'
        )

        result = handover_service.accept_handover(handover.id, self.staff_user)

        self.assertTrue(result['success'])
        self.assertEqual(result['handover'].status, 'IN_PROGRESS')

    def test_complete_handover(self):
        """Test handover completion"""
        from api.services import HandoverService

        handover_service = HandoverService()

        handover = HandoverDocumentation.objects.create(
            from_user=self.faculty_user,
            to_user=self.staff_user,
            title='Test Handover',
            description='Test description',
            status='IN_PROGRESS'
        )

        result = handover_service.complete_handover(handover.id, self.staff_user)

        self.assertTrue(result['success'])
        self.assertEqual(result['handover'].status, 'COMPLETED')


# Import required models
from api.models import (
    AuthUser, GlobalsExtrainfo, GlobalsDesignation, GlobalsHoldsdesignation,
    GlobalsDepartmentinfo, EmergencyAccess, HandoverDocumentation
)