"""
Service layer for System Administrator module
Contains all business logic separated from views
"""

from django.contrib.auth.hashers import make_password
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Max
from datetime import datetime, timedelta
import string
import random

from .models import (
    GlobalsDesignation, GlobalsHoldsdesignation, GlobalsModuleaccess,
    AuthUser, Batch, Student, GlobalsDepartmentinfo, Programme,
    GlobalsFaculty, Staff, GlobalsExtrainfo, Curriculum, Discipline,
    EmergencyAccessRequest, TemporaryRoleAssignment
)
from .serializers import (
    GlobalExtraInfoSerializer, GlobalsDesignationSerializer,
    GlobalsModuleaccessSerializer, AuthUserSerializer,
    GlobalsHoldsDesignationSerializer, StudentSerializer,
    StaffSerializer, GlobalsFacultySerializer
)


class UserService:
    """Service class for user-related operations"""

    @staticmethod
    def generate_password(username, first_name=None):
        """Generate a random password for user"""
        special_characters = string.punctuation

        if first_name:
            # For existing users with first name
            random_specials = "".join(random.choice(special_characters) for _ in range(2))
            return f"{first_name.lower().capitalize().split(' ')[0]}{username[5:].upper()}{random_specials}"
        else:
            # For new users
            random_specials = ''.join(random.choice(special_characters) for _ in range(3))
            return f"{username.lower().capitalize()}{random_specials}"

    @staticmethod
    def create_auth_user(user_data):
        """Create authentication user"""
        auth_user_data = {
            "password": make_password(user_data.get('password', 'user@123')),
            "username": user_data['username'].upper(),
            "first_name": user_data.get('first_name', '').lower().capitalize(),
            "last_name": user_data.get('last_name', '').lower().capitalize(),
            "email": user_data.get('email', f"{user_data['username'].lower()}@iiitdmj.ac.in"),
            "is_staff": user_data.get('is_staff', False),
            "is_superuser": user_data.get('is_superuser', False),
            "is_active": user_data.get('is_active', True),
            "date_joined": datetime.now().strftime("%Y-%m-%d"),
        }
        serializer = AuthUserSerializer(data=auth_user_data)
        if serializer.is_valid():
            return serializer.save()
        return None, serializer.errors

    @staticmethod
    def create_extra_info(user, extra_info_data):
        """Create extra info for user"""
        default_department = GlobalsDepartmentinfo.objects.get(name='CSE').id

        data = {
            'id': user.username.lower(),
            'title': extra_info_data.get('title') or ('Mr.' if extra_info_data.get('sex', 'M')[0].upper() == 'M' else 'Ms.'),
            'sex': extra_info_data.get('sex', 'M')[0].upper(),
            'date_of_birth': extra_info_data.get("dob") or "2025-01-01",
            'user_status': "PRESENT",
            'address': extra_info_data.get("address") or "NA",
            'phone_no': extra_info_data.get("phone") or 9999999999,
            'about_me': "NA",
            'user_type': extra_info_data.get('user_type'),
            'profile_picture': None,
            'date_modified': datetime.now().strftime("%Y-%m-%d"),
            'department': extra_info_data.get("department") or default_department,
            'user': user.id,
        }

        serializer = GlobalExtraInfoSerializer(data=data)
        if serializer.is_valid():
            return serializer.save()
        return None, serializer.errors

    @staticmethod
    def assign_designation(user, designation):
        """Assign designation to user"""
        if isinstance(designation, str):
            designation_obj = get_object_or_404(GlobalsDesignation, name=designation)
        else:
            designation_obj = designation

        holds_data = {
            'designation': designation_obj.id,
            'user': user.id,
            'working': user.id,
        }

        serializer = GlobalsHoldsDesignationSerializer(data=holds_data)
        if serializer.is_valid():
            return serializer.save()
        return None, serializer.errors

    @staticmethod
    def create_student_profile(extra_info, student_data):
        """Create student academic profile"""
        batch = Batch.objects.filter(
            name=student_data.get('programme', 'B.Tech'),
            discipline__acronym=extra_info.department.name,
            year=student_data.get('batch', datetime.now().year)
        ).first()

        data = {
            'id': extra_info.id,
            'programme': student_data.get('programme', 'B.Tech'),
            'batch': student_data.get('batch', datetime.now().year),
            'batch_id': batch.id if batch else None,
            'cpi': 0.0,
            'category': student_data.get('category', 'GEN').upper(),
            'father_name': student_data.get('father_name'),
            'mother_name': student_data.get('mother_name'),
            'hall_no': student_data.get('hall_no', 3),
            'room_no': None,
            'specialization': None,
            'curr_semester_no': 2 * (datetime.now().year - int(student_data.get('batch', datetime.now().year))) + datetime.now().month // 7,
        }

        serializer = StudentSerializer(data=data)
        if serializer.is_valid():
            return serializer.save()
        return None, serializer.errors

    @staticmethod
    def create_staff_profile(extra_info):
        """Create staff profile"""
        data = {
            'id': extra_info.id,
        }
        serializer = StaffSerializer(data=data)
        if serializer.is_valid():
            return serializer.save()
        return None, serializer.errors

    @staticmethod
    def create_faculty_profile(extra_info):
        """Create faculty profile"""
        data = {
            'id': extra_info.id,
        }
        serializer = GlobalsFacultySerializer(data=data)
        if serializer.is_valid():
            return serializer.save()
        return None, serializer.errors


class RoleManagementService:
    """Service class for role and designation management"""

    @staticmethod
    def get_user_roles(username):
        """Get all roles for a user including active emergency access"""
        try:
            from django.utils import timezone
            from .models import EmergencyAccessRequest

            user = AuthUser.objects.get(username__iexact=username)

            # Get permanent roles
            holds_designations = GlobalsHoldsdesignation.objects.filter(user=user)
            designation_ids = [entry.designation_id for entry in holds_designations]
            roles = GlobalsDesignation.objects.filter(id__in=designation_ids)

            # Get active emergency access roles (not expired)
            now = timezone.now()
            active_emergency_roles = EmergencyAccessRequest.objects.filter(
                user=user,
                status='APPROVED',
                reviewed_at__isnull=False
            ).all()

            # Add emergency roles that haven't expired
            for emergency in active_emergency_roles:
                if emergency.reviewed_at and emergency.approved_duration:
                    expiry_time = emergency.reviewed_at + timezone.timedelta(minutes=emergency.approved_duration)
                    if now < expiry_time:
                        # Role is still active, add to list if not already present
                        if emergency.role not in roles:
                            roles = roles | GlobalsDesignation.objects.filter(id=emergency.role.id)

            if not roles.exists():
                return None, "User has no designations"

            return {
                'user': AuthUserSerializer(user).data,
                'roles': GlobalsDesignationSerializer(roles, many=True).data,
            }, None
        except AuthUser.DoesNotExist:
            return None, "User not found"
        except Exception as e:
            return None, str(e)

    @staticmethod
    def update_user_roles(username, roles_to_add):
        """Update roles for a user"""
        user = get_object_or_404(AuthUser, username__iexact=username)

        existing_roles = GlobalsHoldsdesignation.objects.filter(user=user)
        existing_role_names = set(existing_roles.values_list('designation__name', flat=True))

        # Process roles to add
        processed_roles = set()
        for role in roles_to_add:
            if isinstance(role, dict) and 'name' in role:
                processed_roles.add(role['name'])
            elif isinstance(role, str):
                processed_roles.add(role)

        # Remove roles not in new list
        roles_to_remove = existing_role_names - processed_roles
        GlobalsHoldsdesignation.objects.filter(
            user=user,
            designation__name__in=roles_to_remove
        ).delete()

        # Add new roles
        for role_name in processed_roles:
            if role_name not in existing_role_names:
                designation = get_object_or_404(GlobalsDesignation, name=role_name)
                GlobalsHoldsdesignation.objects.create(
                    held_at=timezone.now(),
                    designation=designation,
                    user=user,
                    working=user
                )

        return "User roles updated successfully"

    @staticmethod
    def create_designation_and_module_access(designation_data):
        """Create designation with default module access"""
        # Create designation
        designation_serializer = GlobalsDesignationSerializer(data=designation_data)
        if not designation_serializer.is_valid():
            return None, designation_serializer.errors

        role = designation_serializer.save()

        # Create default module access
        max_id = GlobalsModuleaccess.objects.aggregate(Max('id'))['id__max']
        new_id = (max_id or 0) + 1

        module_data = {
            'id': new_id,
            'designation': role.name,
            'program_and_curriculum': False,
            'course_registration': False,
            'course_management': False,
            'other_academics': False,
            'spacs': False,
            'department': False,
            'examinations': False,
            'hr': False,
            'iwd': False,
            'complaint_management': False,
            'fts': False,
            'purchase_and_store': False,
            'rspc': False,
            'hostel_management': False,
            'mess_management': False,
            'gymkhana': False,
            'placement_cell': False,
            'visitor_hostel': False,
            'phc': False,
            'inventory_management': False,
        }

        module_serializer = GlobalsModuleaccessSerializer(data=module_data)
        if not module_serializer.is_valid():
            return None, module_serializer.errors

        module_serializer.save()

        return {
            'role': designation_serializer.data,
            'modules': module_serializer.data
        }, None

    @staticmethod
    def update_designation(name, update_data, partial=True):
        """Update designation details"""
        try:
            designation = GlobalsDesignation.objects.get(name=name)
        except GlobalsDesignation.DoesNotExist:
            return None, f"Designation with name '{name}' not found"

        serializer = GlobalsDesignationSerializer(
            designation,
            data=update_data,
            partial=partial
        )

        if serializer.is_valid():
            serializer.save()
            return serializer.data, None
        return None, serializer.errors


class ModuleAccessService:
    """Service class for module access management"""

    @staticmethod
    def get_module_access(designation):
        """Get module access for a designation"""
        try:
            module_access = GlobalsModuleaccess.objects.get(designation=designation)
            return GlobalsModuleaccessSerializer(module_access).data, None
        except GlobalsModuleaccess.DoesNotExist:
            return None, f"Module access for designation '{designation}' not found"

    @staticmethod
    def update_module_access(designation, update_data):
        """Update module access for a designation"""
        try:
            module_access = GlobalsModuleaccess.objects.get(designation=designation)
        except GlobalsModuleaccess.DoesNotExist:
            return None, f"Module access for designation '{designation}' not found"

        serializer = GlobalsModuleaccessSerializer(
            module_access,
            data=update_data,
            partial=True
        )

        if serializer.is_valid():
            serializer.save()
            return serializer.data, None
        return None, serializer.errors


class UsernameGenerationService:
    """Service class for auto-generating usernames based on database patterns"""

    @staticmethod
    def generate_student_username(batch_year, programme, discipline_acronym):
        """
        Generate student username (roll number)
        Pattern: {batch_2digit}{programme_1char}{discipline_acronym_2chars}{serial}
        Examples: 21BCS030, 20BEE014, 22MCS007, 25MDS01, 22BDS036

        Args:
            batch_year: int (e.g., 2020)
            programme: str (e.g., 'B.Tech', 'M.Tech', 'B.Des', 'M.Des', 'Ph.D')
            discipline_acronym: str from database (e.g., 'CS', 'EE', 'DS', 'ME')

        Returns:
            str: Generated username (e.g., '20BCS001')
        """
        # Programme code mapping (first letter only)
        programme_map = {
            'B.Tech': 'B',
            'M.Tech': 'M',
            'Ph.D': 'PHD',
            'B.Des': 'B',
            'M.Des': 'M',
        }
        programme_code = programme_map.get(programme, 'B')

        # Build pattern using discipline acronym from database
        pattern = f"{str(batch_year)[-2:]}{programme_code}{discipline_acronym}"

        # Count existing students with this pattern
        existing_count = Student.objects.filter(
            id__user__username__startswith=pattern
        ).count()

        serial = existing_count + 1

        # Determine serial number digits based on count
        # Use 2 digits for small counts, 3 for larger
        if serial < 100:
            username = f"{pattern}{serial:02d}"  # e.g., 25MDS01
        else:
            username = f"{pattern}{serial:03d}"  # e.g., 22BDS036

        # Ensure uniqueness (handle edge cases)
        while AuthUser.objects.filter(username=username).exists():
            serial += 1
            if serial < 100:
                username = f"{pattern}{serial:02d}"
            else:
                username = f"{pattern}{serial:03d}"

        return username

    @staticmethod
    def generate_faculty_username(first_name, last_name):
        """
        Generate faculty username
        Pattern: {first_name_initials}{last_name} (lowercase)
        Examples: snsharma, rkverma, ajsingh
        """
        # Get initials from first name (handle multiple names)
        first_names = first_name.strip().split()
        initials = ''.join([name[0].lower() for name in first_names])
        last_name_clean = last_name.strip().lower()

        # Base username
        username = f"{initials}{last_name_clean}"

        # Ensure uniqueness - append number if duplicate
        if AuthUser.objects.filter(username=username).exists():
            counter = 1
            while AuthUser.objects.filter(username=f"{username}{counter}").exists():
                counter += 1
            username = f"{username}{counter}"

        return username

    @staticmethod
    def generate_staff_username(first_name, last_name):
        """
        Generate staff username (same pattern as faculty)
        Pattern: {first_name_initials}{last_name} (lowercase)
        """
        return UsernameGenerationService.generate_faculty_username(
            first_name, last_name
        )

    @staticmethod
    def generate_college_email(username):
        """Generate college email from username"""
        return f"{username.lower()}@iiitdmj.ac.in"


class BatchDataService:
    """Service class for batch-related data"""

    @staticmethod
    def get_all_departments():
        """Get all departments"""
        return GlobalsDepartmentinfo.objects.all().order_by('id')

    @staticmethod
    def get_all_batches():
        """Get all distinct batches by year"""
        return Batch.objects.distinct('year')

    @staticmethod
    def get_all_programmes():
        """Get all programmes"""
        return Programme.objects.all().order_by('id')

    @staticmethod
    def get_all_designations():
        """Get all designations"""
        return GlobalsDesignation.objects.all()

    @staticmethod
    def get_designations_by_category(category='student', basic=True):
        """Get designations filtered by category"""
        return GlobalsDesignation.objects.filter(
            category=category,
            basic=basic
        )


class EmergencyAccessService:
    """Service class for Emergency/Just-In-Time access management"""

    @staticmethod
    def create_request(user, role_id, duration, reason):
        """Create a new emergency access request"""
        from django.core.exceptions import ValidationError

        if not user.is_active:
            raise ValidationError("Blocked users cannot request emergency access")

        try:
            role = GlobalsDesignation.objects.get(id=role_id)
        except GlobalsDesignation.DoesNotExist:
            raise ValidationError("Invalid role")

        duplicate = EmergencyAccessRequest.objects.filter(
            user=user,
            role=role,
            status=EmergencyAccessRequest.Status.PENDING
        ).exists()

        if duplicate:
            raise ValidationError("You already have a pending request for this role")

        if duration > 1440:
            raise ValidationError("Maximum duration is 24 hours (1440 minutes)")

        if not reason or len(reason.strip()) < 10:
            raise ValidationError("Reason must be at least 10 characters")

        request = EmergencyAccessRequest.objects.create(
            user=user,
            role=role,
            reason=reason.strip(),
            requested_duration=duration
        )

        return request

    @staticmethod
    def get_pending_requests():
        """Get all pending emergency access requests"""
        return EmergencyAccessRequest.objects.filter(
            status=EmergencyAccessRequest.Status.PENDING
        ).select_related('user', 'role').order_by('-requested_at')

    @staticmethod
    def get_all_requests(limit=None):
        """Get all emergency access requests"""
        qs = EmergencyAccessRequest.objects.select_related(
            'user', 'role', 'reviewed_by'
        ).order_by('-requested_at')
        if limit:
            return qs[:limit]
        return qs

    @staticmethod
    def get_user_requests(user):
        """Get all requests for a specific user"""
        return EmergencyAccessRequest.objects.filter(
            user=user
        ).select_related('role', 'reviewed_by').order_by('-requested_at')

    @staticmethod
    def approve_request(request_id, admin_user, approved_duration=None, duration_reason=None):
        """Approve an emergency access request with row locking"""
        from django.db import transaction
        from django.core.exceptions import ValidationError

        with transaction.atomic():
                request = EmergencyAccessRequest.objects.select_for_update().get(id=request_id)

                if request.status != EmergencyAccessRequest.Status.PENDING:
                    raise ValidationError("Request is not in pending status")

                if request.user == admin_user:
                    raise ValidationError("Cannot approve your own request")

                if not request.user.is_active:
                    raise ValidationError("User is not active")

                final_duration = approved_duration if approved_duration is not None else request.requested_duration

                if final_duration > 1440:
                    raise ValidationError("Maximum duration is 24 hours (1440 minutes)")

                expires_at = timezone.now() + timezone.timedelta(minutes=final_duration)

                if not EmergencyAccessService._check_role_conflicts(request.user, request.role):
                    raise ValidationError("Role conflict detected with user's existing roles")

                if not EmergencyAccessService._check_temporary_role_conflicts(request.user, request.role):
                    raise ValidationError("Role conflict detected with user's temporary roles")

                request.status = EmergencyAccessRequest.Status.APPROVED
                request.approved_duration = final_duration
                request.expires_at = expires_at
                request.reviewed_at = timezone.now()
                request.reviewed_by = admin_user
                if duration_reason:
                    request.duration_modified_reason = duration_reason
                request.save()

                TemporaryRoleAssignment.objects.create(
                    user=request.user,
                    role=request.role,
                    request=request,
                    expires_at=expires_at
                )

                return request

    @staticmethod
    def reject_request(request_id, admin_user, reason=None):
        """Reject an emergency access request"""
        from django.db import transaction

        with transaction.atomic():
                request = EmergencyAccessRequest.objects.select_for_update().get(id=request_id)

                if request.status != EmergencyAccessRequest.Status.PENDING:
                    raise ValidationError("Request is not in pending status")

                request.status = EmergencyAccessRequest.Status.REJECTED
                request.reviewed_at = timezone.now()
                request.reviewed_by = admin_user
                request.rejection_reason = reason
                request.save()

                return request

    @staticmethod
    def withdraw_request(request_id, admin_user, reason=None):
        """Withdraw an approved emergency access request"""
        from django.db import transaction

        with transaction.atomic():
                request = EmergencyAccessRequest.objects.select_for_update().get(id=request_id)

                if request.status != EmergencyAccessRequest.Status.APPROVED:
                    raise ValidationError("Can only withdraw approved requests")

                assignments = TemporaryRoleAssignment.objects.filter(
                    request=request,
                    is_active=True
                )

                for assignment in assignments:
                    assignment.revoke(admin_user, reason)

                request.status = EmergencyAccessRequest.Status.WITHDRAWN
                request.save()

                return request

    @staticmethod
    def check_and_expire_roles():
        """Background job to check and expire temporary roles"""
        from django.db import transaction

        expired_count = 0

        with transaction.atomic():
                expired_assignments = TemporaryRoleAssignment.objects.filter(
                    is_active=True,
                    expires_at__lte=timezone.now()
                ).select_for_update()

                for assignment in expired_assignments:
                    assignment.is_active = False
                    assignment.save()

                    if assignment.request.status == EmergencyAccessRequest.Status.APPROVED:
                        assignment.request.status = EmergencyAccessRequest.Status.EXPIRED
                        assignment.request.save()

                    expired_count += 1

        return expired_count

    @staticmethod
    def get_active_temporary_roles(user):
        """Get all active temporary roles for a user"""
        return TemporaryRoleAssignment.objects.filter(
            user=user,
            is_active=True,
            expires_at__gt=timezone.now()
        ).select_related('role', 'request')

    @staticmethod
    def has_active_temporary_role(user, role_id):
        """Check if user has an active temporary role"""
        return TemporaryRoleAssignment.objects.filter(
            user=user,
            role_id=role_id,
            is_active=True,
            expires_at__gt=timezone.now()
        ).exists()

    @staticmethod
    def revoke_all_user_temporary_roles(user):
        """Revoke all temporary roles for a user (e.g., when user is blocked)"""
        from django.db import transaction

        with transaction.atomic():
                active_assignments = TemporaryRoleAssignment.objects.filter(
                    user=user,
                    is_active=True
                ).select_for_update()

                for assignment in active_assignments:
                    assignment.is_active = False
                    assignment.save()

                    if assignment.request.status == EmergencyAccessRequest.Status.APPROVED:
                        assignment.request.status = EmergencyAccessRequest.Status.WITHDRAWN
                        assignment.request.save()

    @staticmethod
    def _check_role_conflicts(user, role):
        """Check if role conflicts with user's existing permanent roles"""
        from .models import RoleConflictRule

        user_roles = GlobalsHoldsdesignation.objects.filter(
            user=user
        ).values_list('designation__name', flat=True)

        conflict_rules = RoleConflictRule.objects.filter(
            role_name=role.name
        ).first()

        if conflict_rules:
            for conflict_role in conflict_rules.conflicts_with:
                if conflict_role in user_roles:
                    return False

        return True

    @staticmethod
    def _check_temporary_role_conflicts(user, role):
        """Check if role conflicts with user's active temporary roles"""
        from .models import RoleConflictRule

        active_temp_roles = TemporaryRoleAssignment.objects.filter(
            user=user,
            is_active=True,
            expires_at__gt=timezone.now()
        ).values_list('role__name', flat=True)

        conflict_rules = RoleConflictRule.objects.filter(
            role_name=role.name
        ).first()

        if conflict_rules:
            for conflict_role in conflict_rules.conflicts_with:
                if conflict_role in active_temp_roles:
                    return False

        return True

    @staticmethod
    def get_request_detail(request_id):
        """Get detailed information about a specific request"""
        try:
            return EmergencyAccessRequest.objects.select_related(
                'user', 'role', 'reviewed_by'
            ).get(id=request_id)
        except EmergencyAccessRequest.DoesNotExist:
            return None
