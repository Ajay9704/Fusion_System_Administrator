#!/usr/bin/env python
"""
Get or reset passwords for specific users
"""
import os
import sys
import django

sys.path.append('C:\\Users\\Yadav\\OneDrive\\Documents\\work\\backup\\Fusion_System_Administrator\\Backend\\backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from api.models import AuthUser

users_to_check = ['admin764', 'testadmin', 'admin']

print("=== User Password Information ===\n")

for username in users_to_check:
    try:
        user = AuthUser.objects.get(username__iexact=username)
        print(f"User: {user.username}")
        print(f"Email: {user.email}")
        print(f"Active: {user.is_active}")
        print(f"Staff: {user.is_staff}")
        print(f"Superuser: {user.is_superuser}")
        print(f"Password (hashed): {user.password[:50]}...")
        print()
    except AuthUser.DoesNotExist:
        print(f"User '{username}' does NOT exist")
        print()

print("\n=== Creating simple passwords ===")

# Set simple passwords for testing
test_passwords = {
    'admin764': 'Admin764@123',
    'testadmin': 'Testadmin@123',
    'admin': 'Admin@123'
}

for username, new_password in test_passwords.items():
    try:
        user = AuthUser.objects.get(username__iexact=username)
        user.set_password(new_password)
        user.save()
        print(f"[OK] {username}: {new_password}")
    except AuthUser.DoesNotExist:
        print(f"[SKIP] {username}: User does not exist")

print("\n=== DONE ===")
