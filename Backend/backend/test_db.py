import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.conf import settings

db_name = settings.DATABASES['default']['NAME']
db_host = settings.DATABASES['default']['HOST']
print(f"Database Name: {db_name}")
print(f"Database Host: {db_host}")
print(f"Using settings: backend.settings")

# Test database connection
from django.db import connections
try:
    conn = connections['default']
    conn.ensure_connection()
    print("✓ Database connection successful!")
except Exception as e:
    print(f"✗ Database connection failed: {e}")
