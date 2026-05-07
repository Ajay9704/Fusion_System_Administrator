#!/usr/bin/env python
"""
Diagnostic script for login issues - checks aadmin764 and badmin206
Run: python manage.py shell --command="exec(open('diagnose_login_issues.py').read())"
Or: python diagnose_login_issues_standalone.py
"""
import os
import sys
import django

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from api.models import AuthUser, GlobalsExtrainfo, GlobalsHoldsdesignation, GlobalsDesignation
from django.contrib.auth.hashers import check_password

usernames = ["aadmin764", "badmin206"]

print(f"\n{'='*70}")
print(f"LOGIN DIAGNOSTIC REPORT")
print(f"{'='*70}")

for username in usernames:
    print(f"\n{'─'*70}")
    print(f"User: {username}")
    print(f"{'─'*70}")
    
    try:
        user = AuthUser.objects.get(username__iexact=username)
        print(f"✓ Found in AuthUser table")
        print(f"  • Username: {user.username}")
        print(f"  • Email: {user.email or '(empty)'}")
        print(f"  • is_active: {user.is_active}")
        print(f"  • is_staff: {user.is_staff}")
        print(f"  • is_superuser: {user.is_superuser}")
        print(f"  • last_login: {user.last_login or '(never)'}")
        
        # Check password hash
        has_valid_hash = user.password.startswith('pbkdf2_sha256$') or user.password.startswith('argon2')
        print(f"  • Password hash valid: {has_valid_hash}")
        
        # Check GlobalsExtrainfo
        try:
            extra = GlobalsExtrainfo.objects.get(user=user)
            print(f"\n✓ GlobalsExtrainfo found:")
            print(f"  • user_status: {extra.user_status}")
            print(f"  • user_type: {extra.user_type}")
            
            if extra.user_status == 'BLOCKED':
                print(f"\n  🚨 CRITICAL ISSUE: User is BLOCKED - cannot login!")
            if not user.is_active:
                print(f"\n  🚨 CRITICAL ISSUE: User is not active (is_active=False)!")
                
        except GlobalsExtrainfo.DoesNotExist:
            print(f"\n  ⚠️  WARNING: No GlobalsExtrainfo record - may cause login issues!")
            
        # Check assigned roles
        roles = GlobalsHoldsdesignation.objects.filter(user=user).select_related('designation')
        if roles.exists():
            print(f"\n✓ Assigned Roles ({roles.count()}):")
            for role_entry in roles:
                print(f"  • {role_entry.designation.name}")
        else:
            print(f"\n  ⚠️  WARNING: No roles assigned!")
            
        # Test common passwords
        print(f"\n  Testing common passwords:")
        test_passwords = ['admin123', 'password', 'admin@123', 'Admin@123', username, f'{username}123']
        found_password = None
        for test_pwd in test_passwords:
            if check_password(test_pwd, user.password):
                found_password = test_pwd
                print(f"  ✓ Matches: '{test_pwd}'")
                break
        
        if not found_password:
            print(f"  ℹ️  Password is not a common test password (this is normal)")
            
    except AuthUser.DoesNotExist:
        print(f"✗ NOT FOUND in database!")

print(f"\n{'='*70}")
print(f"DIAGNOSTIC COMPLETE")
print(f"{'='*70}\n")
