#!/usr/bin/env python
"""
Verify that the reset passwords work correctly
Run: python verify_passwords.py
"""
import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from api.models import AuthUser
from django.contrib.auth.hashers import check_password

print(f"\n{'='*70}")
print(f"PASSWORD VERIFICATION TEST")
print(f"{'='*70}\n")

test_credentials = {
    'aadmin764': 'Admin764@2024',
    'badmin206': 'Admin206@2024',
}

all_passed = True

for username, expected_password in test_credentials.items():
    print(f"Testing: {username}")
    try:
        user = AuthUser.objects.get(username__iexact=username)
        
        # Test if the password matches
        if check_password(expected_password, user.password):
            print(f"  ✓ SUCCESS - Password '{expected_password}' is valid!")
            print(f"  ✓ User can login with this password\n")
        else:
            print(f"  ✗ FAILED - Password '{expected_password}' does NOT match!")
            print(f"  ✗ User will NOT be able to login\n")
            all_passed = False
            
    except AuthUser.DoesNotExist:
        print(f"  ✗ User not found!\n")
        all_passed = False

print(f"{'='*70}")
if all_passed:
    print(f"✓ ALL PASSWORDS VERIFIED - Login should work now!")
else:
    print(f"✗ SOME PASSWORDS FAILED - There may still be issues")
print(f"{'='*70}\n")
