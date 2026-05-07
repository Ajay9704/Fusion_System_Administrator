#!/usr/bin/env python
"""
Test unblocking badmin206
Run: python test_unblock.py
"""
import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from api.models import AuthUser, GlobalsExtrainfo

username = 'badmin206'

try:
    user = AuthUser.objects.get(username__iexact=username)
    extra = GlobalsExtrainfo.objects.get(user=user)
    
    print(f"User: {user.username}")
    print(f"Current status: {extra.user_status}")
    print(f"Is blocked: {extra.user_status == 'BLOCKED'}")
    
    if extra.user_status == 'BLOCKED':
        print("\nAttempting to unblock...")
        extra.user_status = 'PRESENT'
        extra.save()
        print(f"✓ Successfully unblocked! New status: {extra.user_status}")
    else:
        print(f"\nUser is not blocked (status: {extra.user_status})")
        
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
