#!/usr/bin/env python
import os
import sys
import django

# Setup Django
sys.path.append('C:\\Users\\Yadav\\OneDrive\\Documents\\work\\backup\\Fusion_System_Administrator\\Backend\\backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from rest_framework_simplejwt.tokens import RefreshToken
from api.models import AuthUser

def test_token_generation():
    try:
        # Get the TESTADMIN user
        user = AuthUser.objects.get(username='TESTADMIN')
        print(f"Found user: {user.username}")

        # Generate tokens
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        print(f"Access token length: {len(access_token)}")
        print(f"Access token (first 50 chars): {access_token[:50]}...")
        print(f"Refresh token (first 50 chars): {refresh_token[:50]}...")

        # Verify token payload
        print(f"Token user_id: {refresh['user_id']}")
        print(f"Token username: {user.username}")

        return True

    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    test_token_generation()