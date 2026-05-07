"""
Test Configuration and Base Setup
Provides test data, API clients, and helper functions
"""
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from django.utils import timezone
from datetime import timedelta, datetime
import json

User = get_user_model()

class BaseModuleTestCase(TestCase):
    """Base test case with common setup and helpers"""

    @classmethod
    def setUpTestData(cls):
        """Create base test data for all tests"""
        # Create admin user
        cls.admin_user = User.objects.create_user(
            username='testadmin',
            email='admin@test.com',
            password='testpass123',
            is_staff=True,
            is_superuser=True
        )

        # Create staff user
        cls.staff_user = User.objects.create_user(
            username='teststaff',
            email='staff@test.com',
            password='testpass123'
        )

        # Create student user
        cls.student_user = User.objects.create_user(
            username='2021BCS001',
            email='student@test.com',
            password='testpass123'
        )

        # Import models
        from api.models import (
            GlobalsExtrainfo, GlobalsDesignation,
            GlobalsHoldsdesignation, EmergencyAccessRequest
        )

        # Create ExtraInfo for users
        cls.admin_extra = GlobalsExtrainfo.objects.create(
            user=cls.admin_user,
            user_status='ACTIVE',
            user_type='STAFF'
        )

        cls.staff_extra = GlobalsExtrainfo.objects.create(
            user=cls.staff_user,
            user_status='ACTIVE',
            user_type='STAFF'
        )

        cls.student_extra = GlobalsExtrainfo.objects.create(
            user=cls.student_user,
            user_status='ACTIVE',
            user_type='STUDENT'
        )

        # Create designations (roles)
        cls.admin_role = GlobalsDesignation.objects.create(
            name='admin',
            full_name='Administrator',
            category='SYSTEM',
            description='Full system administrator'
        )

        cls.director_role = GlobalsDesignation.objects.create(
            name='director',
            full_name='Director',
            category='ACADEMIC',
            description='Academic director'
        )

        cls.fee_collector_role = GlobalsDesignation.objects.create(
            name='fee_collector',
            full_name='Fee Collector',
            category='FINANCE',
            description='Fee collection role'
        )

        # Assign admin role to admin user
        GlobalsHoldsdesignation.objects.create(
            user=cls.admin_user,
            designation=cls.admin_role
        )

    def setUp(self):
        """Set up API client for each test"""
        self.client = APIClient()
        self.django_client = Client()

    def login_as_admin(self):
        """Login as admin user"""
        self.client.force_authenticate(user=self.admin_user)

    def login_as_staff(self):
        """Login as staff user"""
        self.client.force_authenticate(user=self.staff_user)

    def login_as_student(self):
        """Login as student user"""
        self.client.force_authenticate(user=self.student_user)

    def logout(self):
        """Logout current user"""
        self.client.force_authenticate(user=None)

    def api_get(self, url, expected_status=200):
        """Make GET request and return response"""
        response = self.client.get(url)
        if expected_status:
            self.assertEqual(response.status_code, expected_status,
                           f"Expected {expected_status}, got {response.status_code}")
        return response

    def api_post(self, url, data, expected_status=200):
        """Make POST request and return response"""
        response = self.client.post(url, data, format='json')
        if expected_status:
            self.assertEqual(response.status_code, expected_status,
                           f"Expected {expected_status}, got {response.status_code}")
        return response

    def api_put(self, url, data, expected_status=200):
        """Make PUT request and return response"""
        response = self.client.put(url, data, format='json')
        if expected_status:
            self.assertEqual(response.status_code, expected_status,
                           f"Expected {expected_status}, got {response.status_code}")
        return response

    def api_delete(self, url, expected_status=204):
        """Make DELETE request and return response"""
        response = self.client.delete(url)
        if expected_status:
            self.assertEqual(response.status_code, expected_status,
                           f"Expected {expected_status}, got {response.status_code}")
        return response

    def future_date(self, days_from_now):
        """Get date string for future date"""
        return (timezone.now() + timedelta(days=days_from_now)).strftime('%Y-%m-%d')

    def past_date(self, days_ago):
        """Get date string for past date"""
        return (timezone.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d')

    def today(self):
        """Get today's date as string"""
        return timezone.now().strftime('%Y-%m-%d')

    def assert_object_exists(self, model_class, **kwargs):
        """Assert that an object exists in database"""
        self.assertTrue(
            model_class.objects.filter(**kwargs).exists(),
            f"{model_class.__name__} not found with {kwargs}"
        )

    def assert_object_not_exists(self, model_class, **kwargs):
        """Assert that an object does not exist in database"""
        self.assertFalse(
            model_class.objects.filter(**kwargs).exists(),
            f"{model_class.__name__} found with {kwargs}"
        )


# Base test classes for UC, BR, WF with automatic reporting
class UCTestBase(BaseModuleTestCase):
    """Base class for Use Case tests"""

    def _record_result(self, actual_result, status, evidence=""):
        """Record test result for reporting"""
        from .runner import get_reporter
        reporter = get_reporter()

        # Extract source info from test_id
        source_id = getattr(self, '_uc_id', 'Unknown')
        source_type = 'UC'

        reporter.add_test_result({
            'test_id': getattr(self, '_test_id', 'Unknown'),
            'source_type': source_type,
            'source_id': source_id,
            'test_category': getattr(self, '_test_category', ''),
            'scenario': getattr(self, '_scenario', ''),
            'preconditions': getattr(self, '_preconditions', ''),
            'input_action': getattr(self, '_input_action', ''),
            'expected_result': getattr(self, '_expected_result', ''),
            'actual_result': actual_result,
            'status': status,
            'evidence': evidence
        })


class BRTestBase(BaseModuleTestCase):
    """Base class for Business Rule tests"""

    def _record_result(self, actual_result, status, evidence=""):
        """Record test result for reporting"""
        from .runner import get_reporter
        reporter = get_reporter()

        source_id = getattr(self, '_br_id', 'Unknown')
        source_type = 'BR'

        reporter.add_test_result({
            'test_id': getattr(self, '_test_id', 'Unknown'),
            'source_type': source_type,
            'source_id': source_id,
            'test_category': getattr(self, '_test_category', ''),
            'input_action': getattr(self, '_input_action', ''),
            'expected_result': getattr(self, '_expected_result', ''),
            'actual_result': actual_result,
            'status': status,
            'evidence': evidence
        })


class WFTestBase(BaseModuleTestCase):
    """Base class for Workflow tests"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.workflow_steps = []

    def _add_step(self, step_num, description, expected, actual, passed):
        """Add a workflow step"""
        self.workflow_steps.append({
            'step_num': step_num,
            'description': description,
            'expected': expected,
            'actual': actual,
            'passed': passed
        })

    def _all_steps_passed(self):
        """Check if all workflow steps passed"""
        return all(step['passed'] for step in self.workflow_steps)

    def _record_result(self, actual_result, status, evidence=""):
        """Record test result for reporting"""
        from .runner import get_reporter
        reporter = get_reporter()

        source_id = getattr(self, '_wf_id', 'Unknown')
        source_type = 'WF'

        # Build evidence from workflow steps
        evidence_text = evidence
        if self.workflow_steps:
            steps_summary = "; ".join([
                f"Step {s['step_num']}: {'PASS' if s['passed'] else 'FAIL'} - {s['description']}"
                for s in self.workflow_steps
            ])
            evidence_text = f"{steps_summary} | {evidence}"

        reporter.add_test_result({
            'test_id': getattr(self, '_test_id', 'Unknown'),
            'source_type': source_type,
            'source_id': source_id,
            'test_category': getattr(self, '_test_category', ''),
            'scenario': getattr(self, '_scenario', ''),
            'expected_result': getattr(self, '_expected_result', ''),
            'actual_result': actual_result,
            'status': status,
            'evidence': evidence_text
        })
