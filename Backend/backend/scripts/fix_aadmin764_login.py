"""
Fix aadmin764 login - UNBLOCKS and enables account
Run: python manage.py shell < fix_aadmin764_login.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from backend.api.models import AuthUser, GlobalsExtrainfo

username = "aadmin764"

try:
    user = AuthUser.objects.get(username__iexact=username)
    user.is_active = True
    user.save()

    try:
        extra = GlobalsExtrainfo.objects.get(user=user)
        extra.user_status = 'ACTIVE'
        extra.save()
    except:
        GlobalsExtrainfo.objects.create(user=user, user_status='ACTIVE', user_type='STAFF')

    print(f"✓ {username} enabled and unblocked - can now login")
except:
    print(f"✗ User not found")
