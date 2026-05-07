"""
Test Reporting Runner
Generates all 7 required CSV deliverables for the assignment
"""
import csv
import os
from datetime import datetime
from django.conf import settings

class TestReporter:
    """Collects test results and generates CSV reports"""

    def __init__(self):
        self.test_results = []
        self.defects = []

    def add_test_result(self, test_data):
        """Add a test result to the collection"""
        self.test_results.append(test_data)

        # If test failed or partial, add to defects
        if test_data.get('status') in ['Fail', 'Partial']:
            self.defects.append({
                'defect_id': f"DEF-{len(self.defects) + 1:03d}",
                'related_test_id': test_data.get('test_id'),
                'related_artifact': test_data.get('source_id'),
                'severity': 'Critical' if test_data.get('status') == 'Fail' else 'Medium',
                'description': test_data.get('actual_result', 'Test did not pass'),
                'suggested_fix': 'Review implementation against specification'
            })

    def generate_all_reports(self, module_name="Super Admin"):
        """Generate all 7 required CSV files"""

        # Create reports directory
        reports_dir = os.path.join(os.path.dirname(__file__), 'reports')
        os.makedirs(reports_dir, exist_ok=True)

        # Calculate statistics
        total_uc = len(set(r['source_id'] for r in self.test_results if r['source_type'] == 'UC'))
        total_br = len(set(r['source_id'] for r in self.test_results if r['source_type'] == 'BR'))
        total_wf = len(set(r['source_id'] for r in self.test_results if r['source_type'] == 'WF'))

        uc_tests = [r for r in self.test_results if r['source_type'] == 'UC']
        br_tests = [r for r in self.test_results if r['source_type'] == 'BR']
        wf_tests = [r for r in self.test_results if r['source_type'] == 'WF']

        total_pass = sum(1 for r in self.test_results if r['status'] == 'Pass')
        total_partial = sum(1 for r in self.test_results if r['status'] == 'Partial')
        total_fail = sum(1 for r in self.test_results if r['status'] == 'Fail')
        total_executed = len(self.test_results)

        # Sheet 1: Module_Test_Summary
        self._write_sheet1(os.path.join(reports_dir, 'Module_Test_Summary.csv'), {
            'Total Use Cases': total_uc,
            'Total Business Rules': total_br,
            'Total Workflows': total_wf,
            'Required UC Tests': total_uc * 3,
            'Designed UC Tests': len(uc_tests),
            'Required BR Tests': total_br * 2,
            'Designed BR Tests': len(br_tests),
            'Required WF Tests': total_wf * 2,
            'Designed WF Tests': len(wf_tests),
            'UC Adequacy %': f"{(len(uc_tests) / (total_uc * 3) * 100):.1f}%" if total_uc > 0 else "N/A",
            'BR Adequacy %': f"{(len(br_tests) / (total_br * 2) * 100):.1f}%" if total_br > 0 else "N/A",
            'WF Adequacy %': f"{(len(wf_tests) / (total_wf * 2) * 100):.1f}%" if total_wf > 0 else "N/A",
            'Total Tests Executed': total_executed,
            'Total Pass': total_pass,
            'Total Partial': total_partial,
            'Total Fail': total_fail,
            'Strict Pass Rate %': f"{(total_pass / total_executed * 100):.1f}%" if total_executed > 0 else "N/A"
        })

        # Sheet 2: UC_Test_Design
        self._write_sheet2(os.path.join(reports_dir, 'UC_Test_Design.csv'), uc_tests)

        # Sheet 3: BR_Test_Design
        self._write_sheet3(os.path.join(reports_dir, 'BR_Test_Design.csv'), br_tests)

        # Sheet 4: WF_Test_Design
        self._write_sheet4(os.path.join(reports_dir, 'WF_Test_Design.csv'), wf_tests)

        # Sheet 5: Test_Execution_Log
        self._write_sheet5(os.path.join(reports_dir, 'Test_Execution_Log.csv'), self.test_results)

        # Sheet 6: Defect_Log
        self._write_sheet6(os.path.join(reports_dir, 'Defect_Log.csv'), self.defects)

        # Sheet 7: Artifact_Evaluation
        self._write_sheet7(os.path.join(reports_dir, 'Artifact_Evaluation.csv'),
                          uc_tests, br_tests, wf_tests)

        print(f"\n✓ All reports generated in: {reports_dir}")

    def _write_sheet1(self, filepath, metrics):
        """Sheet 1: Module_Test_Summary"""
        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Metric', 'Value'])
            for key, value in metrics.items():
                writer.writerow([key, value])

    def _write_sheet2(self, filepath, uc_tests):
        """Sheet 2: UC_Test_Design"""
        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Test ID', 'UC ID', 'Test Category', 'Scenario', 'Preconditions',
                           'Input / Action', 'Expected Result'])
            for test in uc_tests:
                writer.writerow([
                    test.get('test_id', ''),
                    test.get('source_id', ''),
                    test.get('test_category', ''),
                    test.get('scenario', ''),
                    test.get('preconditions', ''),
                    test.get('input_action', ''),
                    test.get('expected_result', '')
                ])

    def _write_sheet3(self, filepath, br_tests):
        """Sheet 3: BR_Test_Design"""
        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Test ID', 'BR ID', 'Test Category', 'Input / Action', 'Expected Result'])
            for test in br_tests:
                writer.writerow([
                    test.get('test_id', ''),
                    test.get('source_id', ''),
                    test.get('test_category', ''),
                    test.get('input_action', ''),
                    test.get('expected_result', '')
                ])

    def _write_sheet4(self, filepath, wf_tests):
        """Sheet 4: WF_Test_Design"""
        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Test ID', 'WF ID', 'Test Category', 'Scenario', 'Expected Final State'])
            for test in wf_tests:
                writer.writerow([
                    test.get('test_id', ''),
                    test.get('source_id', ''),
                    test.get('test_category', ''),
                    test.get('scenario', ''),
                    test.get('expected_result', '')
                ])

    def _write_sheet5(self, filepath, test_results):
        """Sheet 5: Test_Execution_Log"""
        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Test ID', 'Source Type', 'Source ID', 'Expected Result',
                           'Actual Result', 'Status', 'Evidence', 'Tester'])
            for test in test_results:
                writer.writerow([
                    test.get('test_id', ''),
                    test.get('source_type', ''),
                    test.get('source_id', ''),
                    test.get('expected_result', ''),
                    test.get('actual_result', ''),
                    test.get('status', ''),
                    test.get('evidence', ''),
                    test.get('tester', 'Claude Haiku 4.5')
                ])

    def _write_sheet6(self, filepath, defects):
        """Sheet 6: Defect_Log"""
        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Defect ID', 'Related Test ID', 'Related Artifact',
                           'Severity', 'Description', 'Suggested Fix'])
            for defect in defects:
                writer.writerow([
                    defect['defect_id'],
                    defect['related_test_id'],
                    defect['related_artifact'],
                    defect['severity'],
                    defect['description'],
                    defect['suggested_fix']
                ])

    def _write_sheet7(self, filepath, uc_tests, br_tests, wf_tests):
        """Sheet 7: Artifact_Evaluation"""
        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Artifact ID', 'Artifact Type', 'Tests', 'Pass', 'Partial',
                           'Fail', 'Final Status', 'Remarks'])

            # Evaluate UCs
            uc_ids = set(t['source_id'] for t in uc_tests)
            for uc_id in uc_ids:
                uc_tests_for_artifact = [t for t in uc_tests if t['source_id'] == uc_id]
                pass_count = sum(1 for t in uc_tests_for_artifact if t['status'] == 'Pass')
                partial_count = sum(1 for t in uc_tests_for_artifact if t['status'] == 'Partial')
                fail_count = sum(1 for t in uc_tests_for_artifact if t['status'] == 'Fail')

                if fail_count == 0 and partial_count == 0:
                    final_status = 'Implemented Correctly'
                elif pass_count > 0:
                    final_status = 'Partially Implemented'
                elif fail_count > pass_count:
                    final_status = 'Incorrectly Implemented'
                else:
                    final_status = 'Not Implemented'

                writer.writerow([
                    uc_id, 'Use Case', len(uc_tests_for_artifact),
                    pass_count, partial_count, fail_count, final_status, ''
                ])

            # Evaluate BRs
            br_ids = set(t['source_id'] for t in br_tests)
            for br_id in br_ids:
                br_tests_for_artifact = [t for t in br_tests if t['source_id'] == br_id]
                pass_count = sum(1 for t in br_tests_for_artifact if t['status'] == 'Pass')
                partial_count = sum(1 for t in br_tests_for_artifact if t['status'] == 'Partial')
                fail_count = sum(1 for t in br_tests_for_artifact if t['status'] == 'Fail')

                if fail_count == 0 and partial_count == 0:
                    final_status = 'Enforced Correctly'
                elif pass_count > 0 or partial_count > 0:
                    final_status = 'Partially Enforced'
                else:
                    final_status = 'Incorrectly Enforced'

                writer.writerow([
                    br_id, 'Business Rule', len(br_tests_for_artifact),
                    pass_count, partial_count, fail_count, final_status, ''
                ])

            # Evaluate WFs
            wf_ids = set(t['source_id'] for t in wf_tests)
            for wf_id in wf_ids:
                wf_tests_for_artifact = [t for t in wf_tests if t['source_id'] == wf_id]
                pass_count = sum(1 for t in wf_tests_for_artifact if t['status'] == 'Pass')
                partial_count = sum(1 for t in wf_tests_for_artifact if t['status'] == 'Partial')
                fail_count = sum(1 for t in wf_tests_for_artifact if t['status'] == 'Fail')

                if fail_count == 0 and partial_count == 0:
                    final_status = 'Complete'
                elif pass_count > 0:
                    final_status = 'Partial'
                else:
                    final_status = 'Incorrect'

                writer.writerow([
                    wf_id, 'Workflow', len(wf_tests_for_artifact),
                    pass_count, partial_count, fail_count, final_status, ''
                ])


# Global reporter instance
_test_reporter = None

def get_reporter():
    """Get or create the global reporter instance"""
    global _test_reporter
    if _test_reporter is None:
        _test_reporter = TestReporter()
    return _test_reporter
