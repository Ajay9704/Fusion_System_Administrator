"""
Script to fix the password for badmin206 user that was saved in plain text.
Run this script to hash the password properly.
"""
import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.contrib.auth.hashers import make_password
from api.models import AuthUser

def fix_badmin206_password():
    """Fix the password for badmin206 user"""
    try:
        # Find the user
        user = AuthUser.objects.get(username='badmin206')
        
        print(f"Found user: {user.username}")
        print(f"Current password (plain text): {user.password}")
        
        # The password you mentioned: Badmin206|&
        plain_password = "Badmin206|&"
        
        # Hash the password properly
        hashed_password = make_password(plain_password)
        
        # Update the user's password
        user.password = hashed_password
        user.save()
        
        print(f"✅ Password has been hashed and updated successfully!")
        print(f"User can now login with password: {plain_password}")
        
    except AuthUser.DoesNotExist:
        print("❌ User badmin206 not found in database")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    fix_badmin206_password()
