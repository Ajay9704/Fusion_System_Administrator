"""
Quick diagnostic for aadmin764 login issue
Run: python manage.py shell < diagnose_aadmin764.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from backend.api.models import AuthUser, GlobalsExtrainfo

username = "aadmin764"

try:
    user = AuthUser.objects.get(username__iexact=username)
    print(f"✓ User found: {username}")
    print(f"  is_active: {user.is_active}")

    try:
        extra = GlobalsExtrainfo.objects.get(user=user)
        print(f"  user_status: {extra.user_status}")
        print(f"  user_type: {extra.user_type}")

        if user.is_active and extra.user_status == 'ACTIVE':
            print(f"\n✓ No blocks found - check password or run: python manage.py shell < fix_aadmin764_login.py")
        else:
            print(f"\n⚠️  ISSUE FOUND:")
            if not user.is_active:
                print(f"  - Account is DISABLED (is_active=False)")
            if extra.user_status == 'BLOCKED':
                print(f"  - Account is BLOCKED in RBAC system")
    except:
        print(f"  ⚠️  No GlobalsExtrainfo found")

except AuthUser.DoesNotExist:
    print(f"✗ User not found")
