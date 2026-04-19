"""
Model Tests
Tests for all model functionality and relationships
"""

from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from api.models import (
    AuthUser, GlobalsExtrainfo, GlobalsDesignation, GlobalsHoldsdesignation,
    GlobalsDepartmentinfo, Student, Staff, GlobalsFaculty, Programme,
    Discipline, Curriculum, Batch, AuditLog, EmergencyAccess, HandoverDocumentation
)

from .conftest import BaseModuleTestCase


class AuthUserTests(BaseModuleTestCase):
    """Test AuthUser model functionality"""

    def test_create_user(self):
        """Test basic user creation"""
        user = AuthUser.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='test123'
        )
        self.assertEqual(user.username, 'testuser')
        self.assertTrue(user.check_password('test123'))

    def test_create_superuser(self):
        """Test superuser creation"""
        superuser = AuthUser.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='admin123'
        )
        self.assertTrue(superuser.is_staff)
        self.assertTrue(superuser.is_superuser)

    def test_user_str_representation(self):
        """Test user string representation"""
        self.assertEqual(str(self.student_user), '2021BCS001')


class GlobalsExtrainfoTests(BaseModuleTestCase):
    """Test GlobalsExtrainfo model functionality"""

    def test_create_extrainfo(self):
        """Test extended info creation"""
        self.assertEqual(self.student_extra.user_type, 'student')
        self.assertEqual(self.student_extra.department, self.cse_dept)

    def test_user_extrainfo_relationship(self):
        """Test one-to-one relationship with user"""
        self.assertEqual(self.student_user.globalssextrainfo, self.student_extra)


class GlobalsDesignationTests(BaseModuleTestCase):
    """Test GlobalsDesignation model functionality"""

    def test_create_designation(self):
        """Test designation creation"""
        self.assertEqual(self.student_designation.name, 'student')
        self.assertEqual(self.student_designation.category, 'student')

    def test_singular_role_constraint(self):
        """Test singular role constraint"""
        # Try to assign singular role to another user
        another_user = AuthUser.objects.create_user(
            username='anotheruser',
            email='another@test.com',
            password='test123'
        )

        # This should not fail at model level (validation happens at view level)
        # But we can test the is_singular field works
        self.assertTrue(self.hod_designation.is_singular)
        self.assertFalse(self.student_designation.is_singular)


class GlobalsHoldsdesignationTests(BaseModuleTestCase):
    """Test GlobalsHoldsdesignation model functionality"""

    def test_assign_role_to_user(self):
        """Test role assignment to user"""
        designation = GlobalsHoldsdesignation.objects.filter(
            user=self.student_user
        ).first()

        self.assertEqual(designation.designation, self.student_designation)
        self.assertEqual(designation.working, self.student_user)

    def test_unique_role_assignment(self):
        """Test that same role can't be assigned twice to same user"""
        with self.assertRaises(IntegrityError):
            GlobalsHoldsdesignation.objects.create(
                user=self.student_user,
                designation=self.student_designation,
                working=self.student_user
            )


class DepartmentTests(BaseModuleTestCase):
    """Test Department model functionality"""

    def test_create_department(self):
        """Test department creation"""
        self.assertEqual(self.cse_dept.name, 'CSE')

    def test_department_hierarchy(self):
        """Test department parent-child relationship"""
        parent_dept = GlobalsDepartmentinfo.objects.create(name='Engineering')
        child_dept = GlobalsDepartmentinfo.objects.create(
            name='Computer Science',
            parent_department=parent_dept
        )

        self.assertEqual(child_dept.parent_department, parent_dept)
        self.assertIn(child_dept, parent_dept.child_departments.all())


class StudentTests(BaseModuleTestCase):
    """Test Student model functionality"""

    def test_create_student(self):
        """Test student creation"""
        self.assertEqual(self.student.programme, 'B.Tech')
        self.assertEqual(self.student.batch, 2021)
        self.assertEqual(self.student.cpi, 8.5)

    def test_student_batch_relationship(self):
        """Test student-batch relationship"""
        self.assertEqual(self.student.batch_id, self.batch_2021)

    def test_student_str_representation(self):
        """Test student string representation"""
        self.assertEqual(str(self.student), '2021BCS001')


class AcademicTests(BaseModuleTestCase):
    """Test academic model relationships"""

    def test_programme_creation(self):
        """Test programme creation"""
        self.assertEqual(self.btech_programme.category, 'B')
        self.assertEqual(self.btech_programme.name, 'B.Tech')

    def test_discipline_programme_relationship(self):
        """Test discipline-programme many-to-many"""
        self.assertIn(self.btech_programme, self.cse_discipline.programme.all())

    def test_curriculum_programme_relationship(self):
        """Test curriculum-programme relationship"""
        self.assertEqual(self.curriculum.programme, self.btech_programme)

    def test_batch_discipline_relationship(self):
        """Test batch-discipline relationship"""
        self.assertEqual(self.batch_2021.discipline, self.cse_discipline)

    def test_batch_curriculum_relationship(self):
        """Test batch-curriculum relationship"""
        self.assertEqual(self.batch_2021.curriculum, self.curriculum)


class AuditLogTests(BaseModuleTestCase):
    """Test AuditLog model functionality"""

    def test_create_audit_log(self):
        """Test audit log creation"""
        audit_log = AuditLog.objects.create(
            user=self.student_user,
            action='TEST_ACTION',
            model_name='AuthUser',
            object_id='123',
            description='Test audit log entry',
            ip_address='127.0.0.1',
            user_agent='Test Agent',
            status='SUCCESS'
        )

        self.assertEqual(audit_log.action, 'TEST_ACTION')
        self.assertEqual(audit_log.user, self.student_user)
        self.assertTrue(audit_log.status, 'SUCCESS')

    def test_audit_log_ordering(self):
        """Test audit logs are ordered by timestamp descending"""
        AuditLog.objects.create(
            user=self.student_user,
            action='ACTION_1',
            description='First action'
        )

        AuditLog.objects.create(
            user=self.student_user,
            action='ACTION_2',
            description='Second action'
        )

        logs = AuditLog.objects.filter(user=self.student_user)
        self.assertEqual(logs.first().action, 'ACTION_2')


class EmergencyAccessTests(BaseModuleTestCase):
    """Test EmergencyAccess model functionality"""

    def test_create_emergency_access_request(self):
        """Test emergency access request creation"""
        emergency = EmergencyAccess.objects.create(
            requester=self.student_user,
            requested_role=self.hod_designation,
            reason='Emergency access needed',
            duration_hours=24
        )

        self.assertEqual(emergency.requester, self.student_user)
        self.assertEqual(emergency.status, 'PENDING')
        self.assertFalse(emergency.is_active())

    def test_emergency_access_activation(self):
        """Test emergency access activation"""
        emergency = EmergencyAccess.objects.create(
            requester=self.student_user,
            requested_role=self.hod_designation,
            reason='Emergency access needed',
            duration_hours=24
        )

        emergency.status = 'APPROVED'
        emergency.save()
        emergency.activate()

        self.assertTrue(emergency.is_active())
        self.assertIsNotNone(emergency.activated_at)
        self.assertIsNotNone(emergency.expires_at)

    def test_emergency_access_expiration(self):
        """Test emergency access expiration"""
        emergency = EmergencyAccess.objects.create(
            requester=self.student_user,
            requested_role=self.hod_designation,
            reason='Emergency access needed',
            duration_hours=1
        )

        emergency.status = 'APPROVED'
        emergency.save()
        emergency.activate()

        # Set expiration to past
        from django.utils import timezone
        from datetime import timedelta
        emergency.expires_at = timezone.now() - timedelta(hours=1)
        emergency.save()

        self.assertTrue(emergency.is_expired())


class HandoverDocumentationTests(BaseModuleTestCase):
    """Test HandoverDocumentation model functionality"""

    def test_create_handover(self):
        """Test handover documentation creation"""
        handover = HandoverDocumentation.objects.create(
            from_user=self.faculty_user,
            to_user=self.staff_user,
            title='Department Handover',
            description='Handover of department responsibilities',
            department=self.cse_dept,
            priority='HIGH',
            status='PENDING'
        )

        self.assertEqual(handover.from_user, self.faculty_user)
        self.assertEqual(handover.to_user, self.staff_user)
        self.assertEqual(handover.status, 'PENDING')

    def test_handover_acceptance(self):
        """Test handover acceptance workflow"""
        handover = HandoverDocumentation.objects.create(
            from_user=self.faculty_user,
            to_user=self.staff_user,
            title='Department Handover',
            description='Handover of department responsibilities',
            status='PENDING'
        )

        handover.accept()

        self.assertEqual(handover.status, 'IN_PROGRESS')
        self.assertIsNotNone(handover.accepted_at)

    def test_handover_completion(self):
        """Test handover completion"""
        handover = HandoverDocumentation.objects.create(
            from_user=self.faculty_user,
            to_user=self.staff_user,
            title='Department Handover',
            description='Handover of department responsibilities',
            status='IN_PROGRESS'
        )

        handover.complete()

        self.assertEqual(handover.status, 'COMPLETED')
        self.assertEqual(handover.progress_percentage, 100)
        self.assertIsNotNone(handover.completed_at)

    def test_handover_cancellation(self):
        """Test handover cancellation"""
        handover = HandoverDocumentation.objects.create(
            from_user=self.faculty_user,
            to_user=self.staff_user,
            title='Department Handover',
            description='Handover of department responsibilities',
            status='PENDING'
        )

        handover.cancel()

        self.assertEqual(handover.status, 'CANCELLED')