import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.db import connection, transaction

def add_sample_data():
    """Add sample data for development testing"""

    with connection.cursor() as cursor:
        # Add sample departments
        departments = [
            ('Computer Science & Engineering', 'CSE'),
            ('Electronics & Communication Engineering', 'ECE'),
            ('Mechanical Engineering', 'ME'),
            ('Civil Engineering', 'CE'),
            ('Electrical Engineering', 'EE'),
        ]

        for name, acronym in departments:
            cursor.execute("""
                INSERT INTO globals_departmentinfo (name) VALUES (%s)
                ON CONFLICT DO NOTHING
            """, [name])
            print(f"Added department: {name}")

        # Add sample designations
        designations = [
            ('Professor', 'Professor', 'Basic', 'Teaching', True, None),
            ('Associate Professor', 'Associate Professor', 'Basic', 'Teaching', True, None),
            ('Assistant Professor', 'Assistant Professor', 'Basic', 'Teaching', True, None),
            ('HOD', 'Head of Department', 'Basic', 'Administration', True, None),
            ('Dean', 'Dean', 'Basic', 'Administration', True, None),
            ('System Administrator', 'System Admin', 'Basic', 'Administration', True, None),
            ('Technical Staff', 'Tech Staff', 'Non-Basic', 'Support', False, None),
            ('Lab Assistant', 'Lab Assistant', 'Non-Basic', 'Support', False, None),
        ]

        for name, full_name, type, category, basic, dept_id in designations:
            cursor.execute("""
                INSERT INTO globals_designation (name, full_name, type, category, basic, dept_if_not_basic_id)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
            """, [name, full_name, type, category, basic, dept_id])
            print(f"Added designation: {name}")

        connection.commit()
        print("\nOK Sample data added successfully!")

        # Verify data
        cursor.execute("SELECT COUNT(*) FROM globals_departmentinfo")
        dept_count = cursor.fetchone()[0]
        print(f"Departments: {dept_count}")

        cursor.execute("SELECT COUNT(*) FROM globals_designation")
        desig_count = cursor.fetchone()[0]
        print(f"Designations: {desig_count}")

if __name__ == "__main__":
    add_sample_data()