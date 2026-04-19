import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from api.models import AuthUser

# Check if admin user exists
try:
    admin_user = AuthUser.objects.get(username='admin')
    print(f"✓ Admin user exists: {admin_user.username}")
    print(f"  Email: {admin_user.email}")
    print(f"  Is Active: {admin_user.is_active}")
    print(f"  Is Staff: {admin_user.is_staff}")
    print(f"  Is Superuser: {admin_user.is_superuser}")
except AuthUser.DoesNotExist:
    print("✗ Admin user does not exist")
    
# Count total users
total_users = AuthUser.objects.count()
print(f"\nTotal users in database: {total_users}")

# List first 5 users
users = AuthUser.objects.all()[:5]
print("\nFirst 5 users:")
for user in users:
    print(f"  - {user.username} ({user.email}) - Active: {user.is_active}")
