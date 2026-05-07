"""
Diagnostic script for login issues - checks aadmin764 and badmin206
Run: python manage.py shell < diagnose_login_issues.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from backend.api.models import AuthUser, GlobalsExtrainfo, GlobalsHoldsdesignation, GlobalsDesignation

usernames = ["aadmin764", "badmin206"]

for username in usernames:
    print(f"\n{'='*60}")
    print(f"Checking user: {username}")
    print(f"{'='*60}")
    
    try:
        user = AuthUser.objects.get(username__iexact=username)
        print(f"✓ User found in AuthUser table")
        print(f"  - Username: {user.username}")
        print(f"  - Email: {user.email}")
        print(f"  - is_active: {user.is_active}")
        print(f"  - is_staff: {user.is_staff}")
        print(f"  - is_superuser: {user.is_superuser}")
        print(f"  - last_login: {user.last_login}")
        print(f"  - password (hashed): {user.password[:30]}...")
        print(f"  - password has valid hash: {user.password.startswith('pbkdf2_sha256$') or user.password.startswith('argon2')}")
        
        # Check GlobalsExtrainfo
        try:
            extra = GlobalsExtrainfo.objects.get(user=user)
            print(f"\n✓ GlobalsExtrainfo found:")
            print(f"  - user_status: {extra.user_status}")
            print(f"  - user_type: {extra.user_type}")
            
            if extra.user_status == 'BLOCKED':
                print(f"  ⚠️  ISSUE: User is BLOCKED!")
            if not user.is_active:
                print(f"  ⚠️  ISSUE: User is not active!")
                
        except GlobalsExtrainfo.DoesNotExist:
            print(f"\n⚠️  ISSUE: No GlobalsExtrainfo record found!")
            
        # Check assigned roles
        roles = GlobalsHoldsdesignation.objects.filter(user=user).select_related('designation')
        if roles.exists():
            print(f"\n✓ Assigned Roles ({roles.count()}):")
            for role_entry in roles:
                print(f"  - {role_entry.designation.name} (ID: {role_entry.designation.id})")
        else:
            print(f"\n⚠️  ISSUE: No roles assigned to user!")
            
        # Test password validation
        from django.contrib.auth.hashers import check_password
        test_passwords = ['admin123', 'password', 'admin@123', 'Admin@123', username]
        print(f"\n  Testing common passwords...")
        for test_pwd in test_passwords:
            is_valid = check_password(test_pwd, user.password)
            if is_valid:
                print(f"  ✓ Password matches: '{test_pwd}'")
                break
        else:
            print(f"  ⚠️  Password is not one of the common test passwords")
            
    except AuthUser.DoesNotExist:
        print(f"✗ User NOT FOUND in database!")

print(f"\n{'='*60}")
print("Diagnostic complete")
print(f"{'='*60}")
