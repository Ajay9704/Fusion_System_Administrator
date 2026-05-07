"""
Enterprise-Grade RBAC (Role-Based Access Control) Service

Provides:
- Role assignment/removal with validation
- Eligibility checking
- Conflict detection
- User blocking/unblocking (independent of roles)
- Real-time consistency with transactions
"""

from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework.response import Response
from rest_framework import status

from ..models import (
    AuthUser, GlobalsExtrainfo, GlobalsDesignation,
    GlobalsHoldsdesignation, AuditLog
)
from ..serializers import (
    AuthUserSerializer, GlobalExtraInfoSerializer,
    GlobalsHoldsDesignationSerializer
)
from ..error_handlers import (
    ErrorCodes, ErrorMessageBuilder,
    AuditMessageBuilder, LogMessageBuilder
)
from ..audit import create_audit_log, get_client_ip, get_user_agent


class UserStatusChoices:
    """User account status (blocking mechanism)"""
    ACTIVE = 'PRESENT'
    BLOCKED = 'BLOCKED'
    SUSPENDED = 'SUSPENDED'


class EligibilityValidator:
    """Validates if a user type is eligible for a role"""

    # Default role eligibility mapping (fallback if database not configured)
    DEFAULT_ROLE_ELIGIBILITY = {
        'student': ['student'],
        'faculty': ['faculty'],
        'staff': ['staff'],
        'hod': ['faculty'],
        'dean': ['faculty'],
        'director': ['faculty', 'staff'],
        'admin': ['faculty', 'staff'],
        'registrar': ['staff'],
        'vice_chancellor': ['faculty'],
    }

    @staticmethod
    def get_eligibility_rules():
        """Get eligibility rules from database or use defaults"""
        try:
            from ..models import RBACConfiguration
            config = RBACConfiguration.objects.get(config_type='eligibility')
            return config.config_data
        except:
            return EligibilityValidator.DEFAULT_ROLE_ELIGIBILITY

    @staticmethod
    def validate(user_type: str, role_name: str) -> tuple[bool, str]:
        """
        Check if user type is eligible for role

        Returns:
            (is_eligible, error_message)
        """
        role_eligibility = EligibilityValidator.get_eligibility_rules()
        role_name_lower = role_name.lower()

        if role_name_lower not in role_eligibility:
            # Role not in mapping - allow by default (admin roles)
            return True, ""

        eligible_types = role_eligibility[role_name_lower]

        if user_type.lower() not in eligible_types:
            return False, f"User type '{user_type}' is not eligible for role '{role_name}'. Eligible types: {', '.join(eligible_types)}"

        return True, ""


class ConflictResolver:
    """Detects and resolves role conflicts"""

    # Default bidirectional conflict mapping (fallback if database not configured)
    DEFAULT_ROLE_CONFLICTS = {
        'director': ['dean', 'hod', 'student'],
        'dean': ['director', 'hod', 'student'],
        'hod': ['director', 'dean', 'student'],
        'student': ['faculty', 'staff', 'admin', 'director', 'dean', 'hod'],
        'faculty': ['student'],
        'staff': ['student'],
    }

    @staticmethod
    def get_all_conflicts():
        """Get all conflict rules from database or use defaults"""
        try:
            from ..models import RBACConfiguration
            config = RBACConfiguration.objects.get(config_type='conflicts')
            return config.config_data
        except:
            return ConflictResolver.DEFAULT_ROLE_CONFLICTS

    @staticmethod
    def check_conflict(user_id: int, new_role_id: int) -> tuple[bool, list[str]]:
        """
        Check if assigning a role conflicts with existing roles

        Returns:
            (has_conflict, list_of_conflicting_role_names)
        """
        try:
            new_role = GlobalsDesignation.objects.get(id=new_role_id)
            existing_roles = GlobalsHoldsdesignation.objects.filter(
                user_id=user_id
            ).select_related('designation')

            existing_role_names = [
                entry.designation.name.lower()
                for entry in existing_roles
            ]

            new_role_name = new_role.name.lower()
            conflicting_roles = []

            # Check if new role conflicts with existing roles
            if new_role_name in ConflictResolver.ROLE_CONFLICTS:
                for conflict_with in ConflictResolver.ROLE_CONFLICTS[new_role_name]:
                    if conflict_with in existing_role_names:
                        conflicting_roles.append(conflict_with)

            # Check if existing roles conflict with new role
            for existing_role_name in existing_role_names:
                if existing_role_name in ConflictResolver.ROLE_CONFLICTS:
                    if new_role_name in ConflictResolver.ROLE_CONFLICTS[existing_role_name]:
                        if new_role_name not in conflicting_roles:
                            conflicting_roles.append(new_role_name)

            return len(conflicting_roles) > 0, conflicting_roles

        except GlobalsDesignation.DoesNotExist:
            return False, []

    @staticmethod
    def get_all_conflicts() -> dict:
        """Get complete conflict mapping"""
        return ConflictResolver.ROLE_CONFLICTS.copy()


class UserRoleService:
    """Service for managing user roles with validation and consistency"""

    @staticmethod
    def get_user_roles(username: str) -> dict:
        """Get all roles assigned to a user (including temporary emergency access roles)"""
        try:
            from django.utils import timezone
            from ..models import TemporaryRoleAssignment
            from ..services import EmergencyAccessService
            
            # Auto-expire any expired temporary roles before fetching
            EmergencyAccessService.check_and_expire_roles()

            user = AuthUser.objects.get(username__iexact=username)

            # Get permanent roles
            holds_entries = GlobalsHoldsdesignation.objects.filter(
                user=user
            ).select_related('designation')

            roles = []

            # Add permanent roles
            for entry in holds_entries:
                roles.append({
                    'id': entry.designation.id,
                    'name': entry.designation.name,
                    'full_name': entry.designation.full_name,
                    'category': entry.designation.category,
                    'assigned_at': entry.held_at.isoformat() if entry.held_at else None,
                    'start_date': entry.start_date.isoformat() if entry.start_date else None,
                    'end_date': entry.end_date.isoformat() if entry.end_date else None,
                    'role_type': 'permanent',
                    # Enhanced permanent role indicators
                    'is_emergency': False,
                    'permanent_tag': 'PERMANENT',
                    'display_label': entry.designation.name,
                    'access_type': 'Permanent Role Assignment',
                })

            # Add active temporary roles (emergency access) - ONLY NON-EXPIRED
            current_time = timezone.now()
            temp_roles = TemporaryRoleAssignment.objects.filter(
                user=user,
                is_active=True,
                expires_at__gt=current_time
            ).select_related('role', 'request')

            for temp_role in temp_roles:
                # Calculate time remaining
                time_remaining = temp_role.expires_at - current_time
                hours_remaining = int(time_remaining.total_seconds() // 3600)
                minutes_remaining = int((time_remaining.total_seconds() % 3600) // 60)

                # Format time remaining for display
                if hours_remaining > 0:
                    time_remaining_str = f"{hours_remaining}h {minutes_remaining}m"
                else:
                    time_remaining_str = f"{minutes_remaining} minutes"

                roles.append({
                    'id': f"temp_{temp_role.id}",
                    'name': temp_role.role.name,
                    'full_name': temp_role.role.full_name,
                    'category': temp_role.role.category,
                    'assigned_at': temp_role.request.requested_at.isoformat() if temp_role.request.requested_at else None,
                    'start_date': temp_role.request.reviewed_at.isoformat() if temp_role.request.reviewed_at else None,
                    'end_date': temp_role.expires_at.isoformat(),
                    'role_type': 'temporary',
                    'expires_at': temp_role.expires_at.isoformat(),
                    # Enhanced temporary role indicators
                    'is_emergency': True,
                    'temporary_tag': 'EMERGENCY ACCESS',
                    'display_label': f'{temp_role.role.name} (Emergency)',
                    'time_remaining': time_remaining_str,
                    'time_remaining_minutes': int(time_remaining.total_seconds() // 60),
                    'access_type': 'Temporary Emergency Access',
                    'approved_duration_minutes': temp_role.request.approved_duration if temp_role.request.approved_duration else 60,
                    'assignment_id': temp_role.id,
                })

            return {
                'username': username,
                'roles': roles,
                'role_count': len(roles)
            }

        except AuthUser.DoesNotExist:
            return None

    @staticmethod
    @transaction.atomic
    def assign_role(username: str, role_name: str, assigned_by: AuthUser,
                   start_date=None, end_date=None) -> dict:
        """
        Assign a role to a user with full validation

        Returns:
            dict with success/error details
        """
        try:
            # Get user and extra info
            user = AuthUser.objects.get(username__iexact=username)

            try:
                extra_info = GlobalsExtrainfo.objects.get(user=user)
            except GlobalsExtrainfo.DoesNotExist:
                return {
                    'success': False,
                    'error': f"User '{username}' does not have a profile record",
                    'error_code': ErrorCodes.DB_RECORD_NOT_FOUND
                }

            # Get role/designation
            try:
                role = GlobalsDesignation.objects.get(name__iexact=role_name)
            except GlobalsDesignation.DoesNotExist:
                return {
                    'success': False,
                    'error': f"Role '{role_name}' does not exist",
                    'error_code': ErrorCodes.DB_RECORD_NOT_FOUND
                }

            # 1. Check eligibility
            is_eligible, eligibility_error = EligibilityValidator.validate(
                extra_info.user_type, role.name
            )
            if not is_eligible:
                return {
                    'success': False,
                    'error': eligibility_error,
                    'error_code': ErrorCodes.BIZ_INVALID_OPERATION
                }

            # 2. Check for singular role constraint
            if role.is_singular:
                existing_holder = GlobalsHoldsdesignation.objects.filter(
                    designation=role
                ).exclude(user=user).first()

                if existing_holder:
                    return {
                        'success': False,
                        'error': f"Role '{role.name}' is singular and already held by '{existing_holder.user.username}'",
                        'error_code': ErrorCodes.BIZ_ROLE_CONFLICT
                    }

            # 3. Check conflicts
            has_conflict, conflicts = ConflictResolver.check_conflict(user.id, role.id)
            if has_conflict:
                return {
                    'success': False,
                    'error': f"Role '{role.name}' conflicts with existing roles: {', '.join(conflicts)}",
                    'conflicting_roles': conflicts,
                    'error_code': ErrorCodes.BIZ_ROLE_CONFLICT
                }

            # 4. Check for duplicate assignment
            existing_assignment = GlobalsHoldsdesignation.objects.filter(
                user=user, designation=role
            ).first()

            if existing_assignment:
                return {
                    'success': False,
                    'error': f"User already has role '{role.name}'",
                    'error_code': ErrorCodes.VAL_DUPLICATE_ENTRY
                }

            # 5. Assign role
            holds_data = {
                'user': user.id,
                'designation': role.id,
                'working': user.id,
                'start_date': start_date,
                'end_date': end_date,
            }

            holds_serializer = GlobalsHoldsDesignationSerializer(data=holds_data)
            if not holds_serializer.is_valid():
                return {
                    'success': False,
                    'error': f"Validation failed: {holds_serializer.errors}",
                    'error_code': ErrorCodes.VAL_INVALID_DATA_FORMAT
                }

            holds_entry = holds_serializer.save()

            # 6. Create audit log
            create_audit_log(
                user=assigned_by,
                action='ROLE_ASSIGNED',
                model_name='GlobalsHoldsdesignation',
                object_id=str(holds_entry.id),
                description=AuditMessageBuilder.role_assigned(username, role.name),
                ip_address=get_client_ip(assigned_by),
                user_agent=get_user_agent(assigned_by),
                status='SUCCESS'
            )

            print(LogMessageBuilder.success(
                "RBAC",
                f"Role '{role.name}' assigned to user '{username}'"
            ))

            return {
                'success': True,
                'message': f"Role '{role.name}' assigned to user '{username}'",
                'role': {
                    'id': role.id,
                    'name': role.name,
                    'full_name': role.full_name,
                }
            }

        except AuthUser.DoesNotExist:
            return {
                'success': False,
                'error': f"User '{username}' not found",
                'error_code': ErrorCodes.DB_RECORD_NOT_FOUND
            }
        except Exception as e:
            print(LogMessageBuilder.error("RBAC", f"Error assigning role to '{username}'", e))
            return {
                'success': False,
                'error': f"Unexpected error: {str(e)}",
                'error_code': ErrorCodes.SYS_INTERNAL_ERROR
            }

    @staticmethod
    @transaction.atomic
    def remove_role(username: str, role_name: str, removed_by: AuthUser) -> dict:
        """
        Remove a role from a user with validation

        Returns:
            dict with success/error details
        """
        try:
            # Get user and role
            user = AuthUser.objects.get(username__iexact=username)
            role = GlobalsDesignation.objects.get(name__iexact=role_name)

            # Check if user has this role
            assignment = GlobalsHoldsdesignation.objects.filter(
                user=user, designation=role
            ).first()

            if not assignment:
                return {
                    'success': False,
                    'error': f"User '{username}' does not have role '{role_name}'",
                    'error_code': ErrorCodes.DB_RECORD_NOT_FOUND
                }

            # Check if this is the last role - MANDATORY CONSTRAINT
            role_count = GlobalsHoldsdesignation.objects.filter(user=user).count()
            if role_count <= 1:
                return {
                    'success': False,
                    'error': "Cannot remove last role. User must have at least one role.",
                    'error_code': ErrorCodes.BIZ_INVALID_STATE_TRANSITION
                }

            # Remove role
            assignment_id = assignment.id
            assignment.delete()

            # Create audit log
            create_audit_log(
                user=removed_by,
                action='ROLE_REMOVED',
                model_name='GlobalsHoldsdesignation',
                object_id=str(assignment_id),
                description=AuditMessageBuilder.role_removed(username, role.name),
                ip_address=get_client_ip(removed_by),
                user_agent=get_user_agent(removed_by),
                status='SUCCESS'
            )

            print(LogMessageBuilder.success(
                "RBAC",
                f"Role '{role.name}' removed from user '{username}'"
            ))

            return {
                'success': True,
                'message': f"Role '{role.name}' removed from user '{username}'",
            }

        except AuthUser.DoesNotExist:
            return {
                'success': False,
                'error': f"User '{username}' not found",
                'error_code': ErrorCodes.DB_RECORD_NOT_FOUND
            }
        except GlobalsDesignation.DoesNotExist:
            return {
                'success': False,
                'error': f"Role '{role_name}' not found",
                'error_code': ErrorCodes.DB_RECORD_NOT_FOUND
            }
        except Exception as e:
            print(LogMessageBuilder.error("RBAC", f"Error removing role from '{username}'", e))
            return {
                'success': False,
                'error': f"Unexpected error: {str(e)}",
                'error_code': ErrorCodes.SYS_INTERNAL_ERROR
            }

    @staticmethod
    @transaction.atomic
    def replace_roles(username: str, new_role_names: list[str],
                     replaced_by: AuthUser, start_date=None, end_date=None) -> dict:
        """
        Replace all user roles with new roles (atomic operation)

        Returns:
            dict with success/error details
        """
        try:
            user = AuthUser.objects.get(username__iexact=username)

            if not new_role_names or len(new_role_names) == 0:
                return {
                    'success': False,
                    'error': "At least one role must be provided",
                    'error_code': ErrorCodes.VAL_MISSING_REQUIRED_FIELD
                }

            # Get current roles
            current_roles = GlobalsHoldsdesignation.objects.filter(user=user)
            current_role_count = current_roles.count()

            # Validate each new role
            new_roles = []
            errors = []

            for role_name in new_role_names:
                try:
                    role = GlobalsDesignation.objects.get(name__iexact=role_name)
                    new_roles.append(role)
                except GlobalsDesignation.DoesNotExist:
                    errors.append(f"Role '{role_name}' does not exist")

            if errors:
                return {
                    'success': False,
                    'error': f"Role validation failed: {'; '.join(errors)}",
                    'error_code': ErrorCodes.DB_RECORD_NOT_FOUND
                }

            # Check for conflicts among new roles themselves
            for i, role in enumerate(new_roles):
                for other_role in new_roles[i+1:]:
                    role1_conflicts = ConflictResolver.ROLE_CONFLICTS.get(
                        role.name.lower(), []
                    )
                    if other_role.name.lower() in role1_conflicts:
                        return {
                            'success': False,
                            'error': f"New roles conflict with each other: '{role.name}' and '{other_role.name}'",
                            'error_code': ErrorCodes.BIZ_ROLE_CONFLICT
                        }

            # Remove old roles
            old_role_names = [entry.designation.name for entry in current_roles]
            current_roles.delete()

            # Assign new roles
            assigned_roles = []
            for role in new_roles:
                holds_data = {
                    'user': user.id,
                    'designation': role.id,
                    'working': user.id,
                    'start_date': start_date,
                    'end_date': end_date,
                }

                holds_serializer = GlobalsHoldsDesignationSerializer(data=holds_data)
                if holds_serializer.is_valid():
                    holds_entry = holds_serializer.save()
                    assigned_roles.append(role.name)
                else:
                    # Rollback on failure
                    return {
                        'success': False,
                        'error': f"Failed to assign role '{role.name}': {holds_serializer.errors}",
                        'error_code': ErrorCodes.VAL_INVALID_DATA_FORMAT
                    }

            # Create audit log
            create_audit_log(
                user=replaced_by,
                action='ROLES_REPLACED',
                model_name='GlobalsHoldsdesignation',
                object_id=str(user.id),
                description=f"Roles replaced for user '{username}'. Old: [{', '.join(old_role_names)}], New: [{', '.join(assigned_roles)}]",
                ip_address=get_client_ip(replaced_by),
                user_agent=get_user_agent(replaced_by),
                status='SUCCESS'
            )

            print(LogMessageBuilder.success(
                "RBAC",
                f"Roles replaced for user '{username}': [{', '.join(assigned_roles)}]"
            ))

            return {
                'success': True,
                'message': f"Roles replaced for user '{username}'",
                'old_roles': old_role_names,
                'new_roles': assigned_roles,
            }

        except AuthUser.DoesNotExist:
            return {
                'success': False,
                'error': f"User '{username}' not found",
                'error_code': ErrorCodes.DB_RECORD_NOT_FOUND
            }
        except Exception as e:
            print(LogMessageBuilder.error("RBAC", f"Error replacing roles for '{username}'", e))
            return {
                'success': False,
                'error': f"Unexpected error: {str(e)}",
                'error_code': ErrorCodes.SYS_INTERNAL_ERROR
            }


class UserBlockingService:
    """
    Service for user blocking/unblocking (independent of roles)

    Blocking is a user-level override that doesn't affect role assignments.
    """

    @staticmethod
    def get_user_status(username: str) -> dict:
        """Get current status and blocking details of a user"""
        try:
            user = AuthUser.objects.get(username__iexact=username)

            try:
                extra_info = GlobalsExtrainfo.objects.get(user=user)
                status = extra_info.user_status
            except GlobalsExtrainfo.DoesNotExist:
                # User without GlobalsExtrainfo record - treat as active
                status = UserStatusChoices.ACTIVE

            return {
                'username': username,
                'status': status,
                'is_blocked': status == UserStatusChoices.BLOCKED,
                'is_active': status == UserStatusChoices.ACTIVE,
            }

        except AuthUser.DoesNotExist:
            return None

    @staticmethod
    @transaction.atomic
    def block_user(username: str, blocked_by: AuthUser, reason: str) -> dict:
        """
        Block a user (prevents login and API access)

        This does NOT remove roles - they remain intact
        """
        try:
            user = AuthUser.objects.get(username__iexact=username)

            try:
                extra_info = GlobalsExtrainfo.objects.get(user=user)
            except GlobalsExtrainfo.DoesNotExist:
                return {
                    'success': False,
                    'error': f"User '{username}' does not have a profile record and cannot be blocked",
                    'error_code': ErrorCodes.DB_RECORD_NOT_FOUND
                }

            # Check if already blocked
            if extra_info.user_status == UserStatusChoices.BLOCKED:
                return {
                    'success': False,
                    'error': f"User '{username}' is already blocked",
                    'error_code': ErrorCodes.BIZ_INVALID_STATE_TRANSITION
                }

            # Block the user by updating user_status
            old_status = extra_info.user_status
            extra_info.user_status = UserStatusChoices.BLOCKED
            extra_info.save()

            # Create audit log
            create_audit_log(
                user=blocked_by,
                action='USER_BLOCKED',
                model_name='GlobalsExtrainfo',
                object_id=str(extra_info.id),
                description=f"User '{username}' blocked by {blocked_by.username}. Reason: {reason}",
                ip_address=None,  # Service layer operation - no request context
                user_agent='RBAC Service',  # Service layer operation
                status='SUCCESS'
            )

            print(LogMessageBuilder.success(
                "RBAC",
                f"User '{username}' blocked by '{blocked_by.username}'. Reason: {reason}"
            ))

            return {
                'success': True,
                'message': f"User '{username}' has been blocked",
                'blocked_by': blocked_by.username,
                'reason': reason,
                'previous_status': old_status,
            }

        except AuthUser.DoesNotExist:
            return {
                'success': False,
                'error': f"User '{username}' not found",
                'error_code': ErrorCodes.DB_RECORD_NOT_FOUND
            }
        except Exception as e:
            print(LogMessageBuilder.error("RBAC", f"Error blocking user '{username}'", e))
            return {
                'success': False,
                'error': f"Unexpected error: {str(e)}",
                'error_code': ErrorCodes.SYS_INTERNAL_ERROR
            }

    @staticmethod
    @transaction.atomic
    def unblock_user(username: str, unblocked_by: AuthUser) -> dict:
        """
        Unblock a user (restores access, roles remain intact)
        """
        try:
            print(f"[UNBLOCK_SERVICE] Starting unblock for user: {username}")
            
            user = AuthUser.objects.get(username__iexact=username)
            print(f"[UNBLOCK_SERVICE] Found user: {user.username} (id: {user.id})")

            try:
                extra_info = GlobalsExtrainfo.objects.get(user=user)
                print(f"[UNBLOCK_SERVICE] Found extra_info, current status: {extra_info.user_status}")
            except GlobalsExtrainfo.DoesNotExist:
                print(f"[UNBLOCK_SERVICE] No extra_info found for user: {username}")
                return {
                    'success': False,
                    'error': f"User '{username}' does not have a profile record and cannot be unblocked",
                    'error_code': ErrorCodes.DB_RECORD_NOT_FOUND
                }

            # Check if already active
            if extra_info.user_status != UserStatusChoices.BLOCKED:
                print(f"[UNBLOCK_SERVICE] User is not blocked, current status: {extra_info.user_status}")
                return {
                    'success': False,
                    'error': f"User '{username}' is not blocked",
                    'error_code': ErrorCodes.BIZ_INVALID_STATE_TRANSITION
                }

            # Unblock the user
            print(f"[UNBLOCK_SERVICE] Changing status from '{extra_info.user_status}' to '{UserStatusChoices.ACTIVE}'")
            extra_info.user_status = UserStatusChoices.ACTIVE
            extra_info.save()
            print(f"[UNBLOCK_SERVICE] Successfully saved new status")

            # Create audit log
            create_audit_log(
                user=unblocked_by,
                action='USER_UNBLOCKED',
                model_name='GlobalsExtrainfo',
                object_id=str(extra_info.id),
                description=f"User '{username}' unblocked by {unblocked_by.username}",
                ip_address=None,  # Service layer operation - no request context
                user_agent='RBAC Service',  # Service layer operation
                status='SUCCESS'
            )

            print(LogMessageBuilder.success(
                "RBAC",
                f"User '{username}' unblocked by '{unblocked_by.username}'"
            ))

            return {
                'success': True,
                'message': f"User '{username}' has been unblocked",
                'unblocked_by': unblocked_by.username,
            }

        except AuthUser.DoesNotExist:
            print(f"[UNBLOCK_SERVICE] User not found: {username}")
            return {
                'success': False,
                'error': f"User '{username}' not found",
                'error_code': ErrorCodes.DB_RECORD_NOT_FOUND
            }
        except Exception as e:
            import traceback
            error_msg = f"[UNBLOCK_SERVICE] Unexpected error: {str(e)}"
            print(error_msg)
            print(traceback.format_exc())
            return {
                'success': False,
                'error': f"Unexpected error: {str(e)}",
                'error_code': ErrorCodes.SYS_INTERNAL_ERROR
            }

    @staticmethod
    def list_blocked_users() -> dict:
        """List all blocked users with their roles"""
        try:
            blocked_extra_info = GlobalsExtrainfo.objects.filter(
                user_status=UserStatusChoices.BLOCKED
            ).select_related('user')

            blocked_users = []
            for extra_info in blocked_extra_info:
                user = extra_info.user

                # Get user's roles (they remain intact even when blocked)
                role_entries = GlobalsHoldsdesignation.objects.filter(
                    user=user
                ).select_related('designation')

                roles = [entry.designation.name for entry in role_entries]

                blocked_users.append({
                    'username': user.username,
                    'user_type': extra_info.user_type,
                    'roles': roles,
                    'department': extra_info.department.name if extra_info.department else None,
                })

            return {
                'success': True,
                'blocked_users': blocked_users,
                'blocked_count': len(blocked_users),
            }

        except Exception as e:
            print(LogMessageBuilder.error("RBAC", "Error fetching blocked users", e))
            return {
                'success': False,
                'error': f"Unexpected error: {str(e)}",
                'error_code': ErrorCodes.SYS_INTERNAL_ERROR
            }


class RBACGuard:
    """
    Middleware guard for checking user access and blocking status

    Use this to check if a user can perform an action
    """

    @staticmethod
    def can_access(username: str) -> tuple[bool, str]:
        """
        Check if user can access the system (not blocked)

        Returns:
            (can_access, error_message)
        """
        try:
            user = AuthUser.objects.get(username__iexact=username)

            # Superusers and staff always have access
            if user.is_superuser or user.is_staff:
                return True, ""

            try:
                extra_info = GlobalsExtrainfo.objects.get(user=user)

                # Check if blocked
                if extra_info.user_status == UserStatusChoices.BLOCKED:
                    return False, "User is blocked by administrator. Contact system administrator."

                # Check if suspended
                if extra_info.user_status == UserStatusChoices.SUSPENDED:
                    return False, "User account is suspended."
            except GlobalsExtrainfo.DoesNotExist:
                # User without GlobalsExtrainfo - check if they have roles
                role_count = GlobalsHoldsdesignation.objects.filter(user=user).count()
                if role_count == 0:
                    return False, "User has no roles assigned. Contact system administrator."

            # Check if user has any roles
            role_count = GlobalsHoldsdesignation.objects.filter(user=user).count()
            if role_count == 0:
                return False, "User has no roles assigned. Contact system administrator."

            return True, ""

        except AuthUser.DoesNotExist:
            return False, "User does not exist"
        except Exception as e:
            print(LogMessageBuilder.error("RBAC_GUARD", f"Error checking access for '{username}'", e))
            return False, "Error checking user access"
