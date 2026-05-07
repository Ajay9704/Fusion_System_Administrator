#!/usr/bin/env python
"""
Reset passwords for aadmin764 and badmin206
Run: python reset_admin_passwords.py
"""
import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from api.models import AuthUser
from django.contrib.auth.hashers import make_password

# Define new passwords - CHANGE THESE as needed
PASSWORDS = {
    'aadmin764': 'Admin764@2024',  # Change this to your desired password
    'badmin206': 'Admin206@2024',  # Change this to your desired password
}

print(f"\n{'='*70}")
print(f"PASSWORD RESET SCRIPT")
print(f"{'='*70}\n")

for username, new_password in PASSWORDS.items():
    print(f"Processing: {username}")
    try:
        user = AuthUser.objects.get(username__iexact=username)
        
        # Hash the new password
        hashed_password = make_password(new_password)
        user.password = hashed_password
        user.save()
        
        print(f"  ✓ Password reset successfully!")
        print(f"  • Username: {user.username}")
        print(f"  • New Password: {new_password}")
        print(f"  • Email: {user.email}\n")
        
    except AuthUser.DoesNotExist:
        print(f"  ✗ User not found: {username}\n")

print(f"{'='*70}")
print(f"PASSWORD RESET COMPLETE")
print(f"{'='*70}")
print(f"\nYou can now login with the credentials above.\n")
