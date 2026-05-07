"""
Test Execution Script
Run all tests and generate CSV reports for assignment submission
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
django.setup()

from django.test.utils import get_runner
from django.conf import settings
from api.tests.runner import get_reporter

def main():
    """Run all tests and generate reports"""

    print("="*70)
    print("SUPER ADMIN MODULE - COMPREHENSIVE TEST EXECUTION")
    print("="*70)
    print()

    # Get the reporter instance
    reporter = get_reporter()

    # Run tests
    print("Running all tests...")
    TestRunner = get_runner(settings)
    test_runner = TestRunner(verbosity=2, interactive=False, keepdb=False)

    # Run the test suite
    failures = test_runner.run_tests(["api.tests"])

    # Generate reports
    print()
    print("="*70)
    print("GENERATING REPORTS")
    print("="*70)

    reporter.generate_all_reports(module_name="Super Admin")

    print()
    print("="*70)
    print("TEST EXECUTION COMPLETE")
    print("="*70)
    print()
    print("Reports generated in: api/tests/reports/")
    print("  - Module_Test_Summary.csv")
    print("  - UC_Test_Design.csv")
    print("  - BR_Test_Design.csv")
    print("  - WF_Test_Design.csv")
    print("  - Test_Execution_Log.csv")
    print("  - Defect_Log.csv")
    print("  - Artifact_Evaluation.csv")
    print()

    return failures

if __name__ == "__main__":
    sys.exit(main())
