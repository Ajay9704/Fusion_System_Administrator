#!/usr/bin/env python
"""
Create admin764 user and set all passwords
"""
import os
import sys
import django

sys.path.append('C:\\Users\\Yadav\\OneDrive\\Documents\\work\\backup\\Fusion_System_Administrator\\Backend\\backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from api.models import AuthUser
from django.contrib.auth.hashers import make_password

# Create admin764 user
try:
    admin764 = AuthUser.objects.create_user(
        username='admin764',
        email='admin764@iiitdmj.ac.in',
        password='Admin764@123',
        first_name='Admin',
        last_name='764',
        is_staff=True,
        is_superuser=True,
        is_active=True,
    )
    print("[OK] Created admin764 user")
except Exception as e:
    print(f"[INFO] admin764: {e}")

# Set/update all passwords
users_passwords = {
    'admin764': 'Admin764@123',
    'testadmin': 'Testadmin@123',
    'admin': 'Admin@123'
}

print("\n=== USER CREDENTIALS ===\n")

for username, password in users_passwords.items():
    try:
        # Try exact match first
        try:
            user = AuthUser.objects.get(username=username)
        except AuthUser.DoesNotExist:
            # Try case-insensitive
            user = AuthUser.objects.get(username__iexact=username)

        user.set_password(password)
        user.save()
        print(f"✅ {username}")
        print(f"   Password: {password}")
        print()
    except AuthUser.DoesNotExist:
        print(f"❌ {username}: User does not exist")
        print()

print("=== READY TO LOGIN ===")
