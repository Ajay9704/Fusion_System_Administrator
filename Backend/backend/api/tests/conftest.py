"""
Test Configuration and Fixtures
Provides base setup for all test modules with reusable test data
"""

import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from unittest.mock import Mock, patch

from api.models import (
    AuthUser, GlobalsExtrainfo, GlobalsDesignation, GlobalsHoldsdesignation,
    GlobalsDepartmentinfo, Student, Staff, GlobalsFaculty, Programme,
    Discipline, Curriculum, Batch
)


class BaseModuleTestCase(TestCase):
    """
    Base test case with common setup for all modules
    Provides reusable test data and helper methods
    """

    @classmethod
    def setUpTestData(cls):
        """Create base test data for all tests"""
        super().setUpTestData()

        # Create departments
        cls.cse_dept = GlobalsDepartmentinfo.objects.create(name='CSE')
        cls.ece_dept = GlobalsDepartmentinfo.objects.create(name='ECE')

        # Create designations
        cls.student_designation = GlobalsDesignation.objects.create(
            name='student',
            full_name='Student',
            type='student',
            basic=True,
            category='student',
            is_singular=False
        )

        cls.faculty_designation = GlobalsDesignation.objects.create(
            name='faculty',
            full_name='Faculty Member',
            type='faculty',
            basic=True,
            category='faculty',
            is_singular=False
        )

        cls.hod_designation = GlobalsDesignation.objects.create(
            name='hod',
            full_name='Head of Department',
            type='administrative',
            basic=False,
            category='administrative',
            is_singular=True
        )

        # Create test users
        cls.create_test_users()

        # Create academic data
        cls.create_academic_data()

    @classmethod
    def create_test_users(cls):
        """Create test users for different roles"""

        # Student user
        cls.student_user = AuthUser.objects.create_user(
            username='2021BCS001',
            email='student@test.com',
            password='test123'
        )
        cls.student_extra = GlobalsExtrainfo.objects.create(
            id='2021BCS001',
            user=cls.student_user,
            title='Mr.',
            sex='M',
            date_of_birth='2000-01-01',
            user_status='PRESENT',
            address='Test Address',
            phone_no=1234567890,
            user_type='student',
            profile_picture=None,
            about_me='Test student',
            department=cls.cse_dept
        )

        # Staff user
        cls.staff_user = AuthUser.objects.create_user(
            username='staff001',
            email='staff@test.com',
            password='test123'
        )
        cls.staff_extra = GlobalsExtrainfo.objects.create(
            id='staff001',
            user=cls.staff_user,
            title='Mr.',
            sex='M',
            date_of_birth='1980-01-01',
            user_status='PRESENT',
            address='Staff Address',
            phone_no=9876543210,
            user_type='staff',
            profile_picture=None,
            about_me='Test staff',
            department=cls.cse_dept
        )

        # Faculty user
        cls.faculty_user = AuthUser.objects.create_user(
            username='faculty001',
            email='faculty@test.com',
            password='test123',
            is_staff=True
        )
        cls.faculty_extra = GlobalsExtrainfo.objects.create(
            id='faculty001',
            user=cls.faculty_user,
            title='Dr.',
            sex='M',
            date_of_birth='1975-01-01',
            user_status='PRESENT',
            address='Faculty Address',
            phone_no=5555555555,
            user_type='faculty',
            profile_picture=None,
            about_me='Test faculty',
            department=cls.cse_dept
        )

        # Assign designations
        GlobalsHoldsdesignation.objects.create(
            user=cls.student_user,
            designation=cls.student_designation,
            working=cls.student_user
        )

        GlobalsHoldsdesignation.objects.create(
            user=cls.staff_user,
            designation=cls.faculty_designation,
            working=cls.staff_user
        )

        GlobalsHoldsdesignation.objects.create(
            user=cls.faculty_user,
            designation=cls.hod_designation,
            working=cls.faculty_user
        )

    @classmethod
    def create_academic_data(cls):
        """Create academic programme and batch data"""

        # Create programme
        cls.btech_programme = Programme.objects.create(
            category='B',
            name='B.Tech',
            programme_begin_year=2021
        )

        # Create discipline
        cls.cse_discipline = Discipline.objects.create(
            name='Computer Science and Engineering',
            acronym='CSE'
        )
        cls.cse_discipline.programme.add(cls.btech_programme)

        # Create curriculum
        cls.curriculum = Curriculum.objects.create(
            programme=cls.btech_programme,
            name='B.Tech CSE 2021',
            version=1.0,
            working_curriculum=True,
            no_of_semester=8,
            min_credit=120
        )

        # Create batch
        cls.batch_2021 = Batch.objects.create(
            name='2021 Batch',
            discipline=cls.cse_discipline,
            year=2021,
            curriculum=cls.curriculum,
            running_batch=True
        )

        # Create student record
        cls.student = Student.objects.create(
            id=cls.student_extra,
            programme='B.Tech',
            batch=2021,
            batch_id=cls.batch_2021,
            cpi=8.5,
            category='GEN',
            father_name='Father Name',
            mother_name='Mother Name',
            hall_no=1,
            room_no='101',
            specialization='Computer Science',
            curr_semester_no=4
        )

    def setUp(self):
        """Set up test client and authenticate for each test"""
        super().setUp()
        self.client = APIClient()

    def login_as_student(self):
        """Authenticate as student user"""
        self.client.force_authenticate(user=self.student_user)

    def login_as_staff(self):
        """Authenticate as staff user"""
        self.client.force_authenticate(user=self.staff_user)

    def login_as_faculty(self):
        """Authenticate as faculty user"""
        self.client.force_authenticate(user=self.faculty_user)

    def logout(self):
        """Logout current user"""
        self.client.force_authenticate(user=None)

    def api_get(self, endpoint, expected_status=200):
        """Make GET request and return response"""
        response = self.client.get(endpoint)
        if expected_status:
            self.assertEqual(response.status_code, expected_status)
        return response

    def api_post(self, endpoint, data=None, expected_status=201):
        """Make POST request and return response"""
        response = self.client.post(endpoint, data, format='json')
        if expected_status:
            self.assertEqual(response.status_code, expected_status)
        return response

    def api_put(self, endpoint, data=None, expected_status=200):
        """Make PUT request and return response"""
        response = self.client.put(endpoint, data, format='json')
        if expected_status:
            self.assertEqual(response.status_code, expected_status)
        return response

    def api_delete(self, endpoint, expected_status=204):
        """Make DELETE request and return response"""
        response = self.client.delete(endpoint)
        if expected_status:
            self.assertEqual(response.status_code, expected_status)
        return response

    def assert_object_exists(self, model, **kwargs):
        """Assert that an object exists in database"""
        self.assertTrue(
            model.objects.filter(**kwargs).exists(),
            f"{model.__name__} with {kwargs} does not exist"
        )

    def assert_object_not_exists(self, model, **kwargs):
        """Assert that an object does not exist in database"""
        self.assertFalse(
            model.objects.filter(**kwargs).exists(),
            f"{model.__name__} with {kwargs} exists but shouldn't"
        )


class APITestCase(BaseModuleTestCase):
    """
    Base class for API endpoint tests
    Provides additional API-specific helper methods
    """

    def assert_success_response(self, response):
        """Assert response indicates success"""
        self.assertIn(response.status_code, [200, 201, 204])
        return response.data

    def assert_error_response(self, response, expected_status=400):
        """Assert response indicates error"""
        self.assertIn(response.status_code, [400, 401, 403, 404, 500])
        return response.data

    def assert_response_contains(self, response, fields):
        """Assert response contains specified fields"""
        for field in fields:
            self.assertIn(field, response.data)


# Pytest fixtures for pytest-style tests
@pytest.fixture
def api_client():
    """Provide API client for tests"""
    return APIClient()


@pytest.fixture
def test_department():
    """Provide test department"""
    return GlobalsDepartmentinfo.objects.create(name='Test Department')


@pytest.fixture
def test_designation():
    """Provide test designation"""
    return GlobalsDesignation.objects.create(
        name='test_role',
        full_name='Test Role',
        type='test',
        basic=True,
        category='test'
    )


@pytest.fixture
def authenticated_client(api_client):
    """Provide authenticated API client"""
    user = AuthUser.objects.create_user(
        username='testuser',
        password='test123'
    )
    api_client.force_authenticate(user=user)
    return api_client