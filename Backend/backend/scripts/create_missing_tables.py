import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.db import connection, transaction

def create_missing_tables():
    """Create missing database tables for development"""

    tables_to_create = [
        {
            'name': 'globals_departmentinfo',
            'columns': """
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            """
        },
        {
            'name': 'globals_designation',
            'columns': """
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL UNIQUE,
                full_name VARCHAR(255),
                type VARCHAR(50),
                category VARCHAR(50),
                basic BOOLEAN DEFAULT FALSE,
                dept_if_not_basic_id INTEGER REFERENCES globals_departmentinfo(id)
            """
        },
        {
            'name': 'globals_faculty',
            'columns': """
                id VARCHAR(20) PRIMARY KEY REFERENCES auth_user(username),
                user_id INTEGER REFERENCES auth_user(id),
                department_id INTEGER REFERENCES globals_departmentinfo(id)
            """
        },
        {
            'name': 'globals_staff',
            'columns': """
                id VARCHAR(20) PRIMARY KEY REFERENCES auth_user(username),
                user_id INTEGER REFERENCES auth_user(id),
                department_id INTEGER REFERENCES globals_departmentinfo(id)
            """
        },
        {
            'name': 'programme_curriculum_batch',
            'columns': """
                id SERIAL PRIMARY KEY,
                running_batch VARCHAR(20) NOT NULL,
                programme_id INTEGER REFERENCES programme_curriculum_programme(id)
            """
        },
        {
            'name': 'academic_information_student',
            'columns': """
                student_id INTEGER REFERENCES academic_information_student(id),
                batch_id INTEGER REFERENCES programme_curriculum_batch(running_batch)
            """
        }
    ]

    with connection.cursor() as cursor:
        for table in tables_to_create:
            try:
                # Check if table exists
                cursor.execute("""
                    SELECT EXISTS (
                       SELECT FROM information_schema.tables
                       WHERE table_schema = 'public'
                       AND table_name = %s
                    )
                """, [table['name']])
                exists = cursor.fetchone()[0]

                if not exists:
                    print(f"Creating table: {table['name']}")
                    cursor.execute(f"""
                        CREATE TABLE {table['name']} (
                            {table['columns']}
                        )
                    """)
                    print(f"OK Table {table['name']} created successfully")
                else:
                    print(f"OK Table {table['name']} already exists")

            except Exception as e:
                print(f"ERROR creating table {table['name']}: {e}")

        connection.commit()
        print("\nOK All tables created successfully!")

if __name__ == "__main__":
    create_missing_tables()