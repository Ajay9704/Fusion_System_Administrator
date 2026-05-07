"""
Data consistency script to ensure all users have appropriate records
Run this in Django shell: python manage.py shell < ensure_user_data_consistency.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from backend.api.models import AuthUser, GlobalsExtrainfo, Student, Staff, Faculty
from django.utils import timezone

print(f"\n{'='*60}")
print(f"DATA CONSISTENCY CHECK")
print(f"{'='*60}\n")

# Get all users
all_users = AuthUser.objects.all()
print(f"Total users in system: {all_users.count()}")

# Check users without GlobalsExtrainfo
users_without_extra = all_users.exclude(globals_extrainfo__isnull=False)
print(f"Users without GlobalsExtrainfo: {users_without_extra.count()}")

if users_without_extra.exists():
    print(f"\nCreating missing GlobalsExtrainfo records...")
    for user in users_without_extra:
        # Determine user_type based on roles or superuser status
        user_type = 'STAFF'  # default
        if user.is_superuser:
            user_type = 'STAFF'  # Admin users are treated as staff type
        else:
            # Check if user has student-specific roles
            from backend.api.models import GlobalsHoldsdesignation, GlobalsDesignation
            user_roles = GlobalsHoldsdesignation.objects.filter(user=user)
            for role_entry in user_roles:
                role_name = role_entry.designation.name.lower()
                if 'student' in role_name:
                    user_type = 'STUDENT'
                    break

        GlobalsExtrainfo.objects.create(
            user=user,
            user_status='ACTIVE',
            user_type=user_type,
            department_id=None
        )
        print(f"  ✓ Created GlobalsExtrainfo for {user.username} (type: {user_type})")

# Check admin users without staff records
admin_users = all_users.filter(is_superuser=True) | all_users.filter(username__iexact='admin')
admin_users_without_staff = admin_users.exclude(staff__isnull=False)

print(f"\nAdmin users: {admin_users.count()}")
print(f"Admin users without staff record: {admin_users_without_staff.count()}")

if admin_users_without_staff.exists():
    print(f"\nCreating missing Staff records for admin users...")
    for user in admin_users_without_staff:
        # Check if staff record already exists
        if not Staff.objects.filter(user=user).exists():
            Staff.objects.create(
                user=user,
                department_id=None,
                designation='Administrator',
                date_of_joining=timezone.now().date()
            )
            print(f"  ✓ Created Staff record for admin user: {user.username}")

# Final status
print(f"\n{'='*60}")
print(f"DATA CONSISTENCY CHECK COMPLETE")
print(f"{'='*60}")

# Verify
final_users_without_extra = AuthUser.objects.exclude(globals_extrainfo__isnull=False)
final_admin_users_without_staff = (all_users.filter(is_superuser=True) | all_users.filter(username__iexact='admin')).exclude(staff__isnull=False)

print(f"\nRemaining issues:")
print(f"  Users without GlobalsExtrainfo: {final_users_without_extra.count()}")
print(f"  Admin users without staff record: {final_admin_users_without_staff.count()}")

if final_users_without_extra.count() == 0 and final_admin_users_without_staff.count() == 0:
    print(f"\n✓ All data consistency issues resolved!")
else:
    print(f"\n⚠️  Some issues remain. Please review manually.")
