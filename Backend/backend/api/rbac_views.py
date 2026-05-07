"""
RBAC (Role-Based Access Control) API Views

Enterprise-grade endpoints for:
- Role management (assign, remove, replace)
- User blocking/unblocking (independent of roles)
- Access checking
- Configuration viewing
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from .rbac_services.rbac_service import (
    UserRoleService,
    UserBlockingService,
    RBACGuard,
    EligibilityValidator,
    ConflictResolver,
    UserStatusChoices
)
from .audit import audit_log
from .error_handlers import ErrorCodes, ErrorMessageBuilder, LogMessageBuilder


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def rbac_get_user_roles(request):
    """Get all roles assigned to a user"""
    try:
        username = request.query_params.get('username')

        if not username:
            username = request.user.username

        result = UserRoleService.get_user_roles(username)

        if result is None:
            return Response(
                ErrorMessageBuilder.database_error(
                    ErrorCodes.DB_RECORD_NOT_FOUND,
                    f"User '{username}' not found",
                    solution="Verify the username"
                ),
                status=status.HTTP_404_NOT_FOUND
            )

        return Response(result, status=status.HTTP_200_OK)
    except Exception as e:
        import traceback
        print(f"Error in rbac_get_user_roles: {e}")
        print(traceback.format_exc())
        return Response(
            ErrorMessageBuilder.system_error(
                ErrorCodes.SYS_INTERNAL_ERROR,
                str(e)
            ),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@audit_log(action='ROLE_ASSIGNED', model_name='GlobalsHoldsdesignation')
def rbac_assign_role(request):
    """Assign a role to a user with full validation"""
    username = request.data.get('username')
    role_name = request.data.get('role_name')
    start_date = request.data.get('start_date')
    end_date = request.data.get('end_date')

    if not username or not role_name:
        return Response(
            ErrorMessageBuilder.validation_error(
                ErrorCodes.VAL_MISSING_REQUIRED_FIELD,
                "Username and role_name are required",
                solution="Provide both 'username' and 'role_name' in request body"
            ),
            status=status.HTTP_400_BAD_REQUEST
        )

    # Parse dates if provided
    if start_date:
        try:
            from datetime import datetime
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                ErrorMessageBuilder.validation_error(
                    ErrorCodes.VAL_INVALID_DATA_FORMAT,
                    "Invalid start_date format. Use YYYY-MM-DD"
                ),
                status=status.HTTP_400_BAD_REQUEST
            )

    if end_date:
        try:
            from datetime import datetime
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                ErrorMessageBuilder.validation_error(
                    ErrorCodes.VAL_INVALID_DATA_FORMAT,
                    "Invalid end_date format. Use YYYY-MM-DD"
                ),
                status=status.HTTP_400_BAD_REQUEST
            )

    result = UserRoleService.assign_role(
        username=username,
        role_name=role_name,
        assigned_by=request.user,
        start_date=start_date,
        end_date=end_date
    )

    if result['success']:
        return Response(result, status=status.HTTP_201_CREATED)
    else:
        return Response(
            ErrorMessageBuilder.validation_error(
                result.get('error_code', ErrorCodes.BIZ_INVALID_OPERATION),
                result['error'],
                solution="Check role eligibility, conflicts, and user status"
            ),
            status=status.HTTP_400_BAD_REQUEST if result.get('error_code') != ErrorCodes.SYS_INTERNAL_ERROR else status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
@audit_log(action='ROLE_REMOVED', model_name='GlobalsHoldsdesignation')
def rbac_remove_role(request):
    """Remove a role from a user (ensures user keeps at least one role)"""
    username = request.data.get('username')
    role_name = request.data.get('role_name')

    if not username or not role_name:
        return Response(
            ErrorMessageBuilder.validation_error(
                ErrorCodes.VAL_MISSING_REQUIRED_FIELD,
                "Username and role_name are required",
                solution="Provide both 'username' and 'role_name' in request body"
            ),
            status=status.HTTP_400_BAD_REQUEST
        )

    result = UserRoleService.remove_role(
        username=username,
        role_name=role_name,
        removed_by=request.user
    )

    if result['success']:
        return Response(result, status=status.HTTP_200_OK)
    else:
        return Response(
            ErrorMessageBuilder.validation_error(
                result.get('error_code', ErrorCodes.BIZ_INVALID_OPERATION),
                result['error'],
                solution="Ensure user has at least one role after removal"
            ),
            status=status.HTTP_400_BAD_REQUEST if result.get('error_code') != ErrorCodes.SYS_INTERNAL_ERROR else status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
@audit_log(action='ROLES_REPLACED', model_name='GlobalsHoldsdesignation')
def rbac_replace_roles(request):
    """Replace all user roles with new roles (atomic operation)"""
    username = request.data.get('username')
    role_names = request.data.get('roles')
    start_date = request.data.get('start_date')
    end_date = request.data.get('end_date')

    if not username or not role_names:
        return Response(
            ErrorMessageBuilder.validation_error(
                ErrorCodes.VAL_MISSING_REQUIRED_FIELD,
                "Username and roles are required",
                solution="Provide both 'username' and 'roles' (list) in request body"
            ),
            status=status.HTTP_400_BAD_REQUEST
        )

    if not isinstance(role_names, list):
        return Response(
            ErrorMessageBuilder.validation_error(
                ErrorCodes.VAL_INVALID_DATA_FORMAT,
                "Roles must be a list",
                solution="Provide roles as a list: ['role1', 'role2']"
            ),
            status=status.HTTP_400_BAD_REQUEST
        )

    # Parse dates if provided
    if start_date:
        try:
            from datetime import datetime
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                ErrorMessageBuilder.validation_error(
                    ErrorCodes.VAL_INVALID_DATA_FORMAT,
                    "Invalid start_date format. Use YYYY-MM-DD"
                ),
                status=status.HTTP_400_BAD_REQUEST
            )

    if end_date:
        try:
            from datetime import datetime
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                ErrorMessageBuilder.validation_error(
                    ErrorCodes.VAL_INVALID_DATA_FORMAT,
                    "Invalid end_date format. Use YYYY-MM-DD"
                ),
                status=status.HTTP_400_BAD_REQUEST
            )

    result = UserRoleService.replace_roles(
        username=username,
        new_role_names=role_names,
        replaced_by=request.user,
        start_date=start_date,
        end_date=end_date
    )

    if result['success']:
        return Response(result, status=status.HTTP_200_OK)
    else:
        return Response(
            ErrorMessageBuilder.validation_error(
                result.get('error_code', ErrorCodes.BIZ_INVALID_OPERATION),
                result['error'],
                solution="Check role eligibility, conflicts, and provide at least one role"
            ),
            status=status.HTTP_400_BAD_REQUEST if result.get('error_code') != ErrorCodes.SYS_INTERNAL_ERROR else status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def rbac_get_user_status(request):
    """Get current status of a user (blocked/unblocked)"""
    try:
        username = request.query_params.get('username')

        if not username:
            username = request.user.username

        result = UserBlockingService.get_user_status(username)

        if result is None:
            return Response(
                ErrorMessageBuilder.database_error(
                    ErrorCodes.DB_RECORD_NOT_FOUND,
                    f"User '{username}' not found",
                    solution="Verify the username"
                ),
                status=status.HTTP_404_NOT_FOUND
            )

        return Response(result, status=status.HTTP_200_OK)
    except Exception as e:
        import traceback
        print(f"Error in rbac_get_user_status: {e}")
        print(traceback.format_exc())
        return Response(
            ErrorMessageBuilder.system_error(
                ErrorCodes.SYS_INTERNAL_ERROR,
                str(e)
            ),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@audit_log(action='USER_BLOCKED', model_name='GlobalsExtrainfo')
def rbac_block_user(request):
    """
    Block a user (prevents login and API access)

    NOTE: This does NOT remove roles - they remain intact
    """
    try:
        username = request.data.get('username')
        reason = request.data.get('reason')

        if not username:
            return Response(
                ErrorMessageBuilder.validation_error(
                    ErrorCodes.VAL_MISSING_REQUIRED_FIELD,
                    "Username is required",
                    field="username",
                    solution="Provide 'username' in request body"
                ),
                status=status.HTTP_400_BAD_REQUEST
            )

        if not reason:
            return Response(
                ErrorMessageBuilder.validation_error(
                    ErrorCodes.VAL_MISSING_REQUIRED_FIELD,
                    "Reason is required for blocking user",
                    field="reason",
                    solution="Provide 'reason' in request body explaining why user is being blocked"
                ),
                status=status.HTTP_400_BAD_REQUEST
            )

        result = UserBlockingService.block_user(
            username=username,
            blocked_by=request.user,
            reason=reason
        )

        if result['success']:
            return Response(result, status=status.HTTP_200_OK)
        else:
            return Response(
                ErrorMessageBuilder.validation_error(
                    result.get('error_code', ErrorCodes.BIZ_INVALID_OPERATION),
                    result['error'],
                    solution="Check if user exists and is not already blocked"
                ),
                status=status.HTTP_400_BAD_REQUEST if result.get('error_code') != ErrorCodes.SYS_INTERNAL_ERROR else status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    except Exception as e:
        import traceback
        print(f"Error in rbac_block_user: {e}")
        print(traceback.format_exc())
        return Response(
            ErrorMessageBuilder.system_error(
                ErrorCodes.SYS_INTERNAL_ERROR,
                str(e)
            ),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@audit_log(action='USER_UNBLOCKED', model_name='GlobalsExtrainfo')
def rbac_unblock_user(request):
    """Unblock a user (restores access, roles remain intact)"""
    try:
        username = request.data.get('username')
        
        if not username:
            return Response(
                ErrorMessageBuilder.validation_error(
                    ErrorCodes.VAL_MISSING_REQUIRED_FIELD,
                    "Username is required",
                    field="username",
                    solution="Provide 'username' in request body"
                ),
                status=status.HTTP_400_BAD_REQUEST
            )

        print(f"[UNBLOCK] Attempting to unblock user: {username} by {request.user.username}")
        
        result = UserBlockingService.unblock_user(
            username=username,
            unblocked_by=request.user
        )

        if result['success']:
            print(f"[UNBLOCK] Successfully unblocked: {username}")
            return Response(result, status=status.HTTP_200_OK)
        else:
            print(f"[UNBLOCK] Failed to unblock {username}: {result.get('error')}")
            return Response(
                ErrorMessageBuilder.validation_error(
                    result.get('error_code', ErrorCodes.BIZ_INVALID_OPERATION),
                    result['error'],
                    solution="Check if user exists and is currently blocked"
                ),
                status=status.HTTP_400_BAD_REQUEST if result.get('error_code') != ErrorCodes.SYS_INTERNAL_ERROR else status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    except Exception as e:
        import traceback
        error_msg = f"Error in rbac_unblock_user: {e}"
        print(error_msg)
        print(traceback.format_exc())
        return Response(
            ErrorMessageBuilder.system_error(
                ErrorCodes.SYS_INTERNAL_ERROR,
                str(e)
            ),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def rbac_list_blocked_users(request):
    """List all blocked users with their roles"""
    try:
        result = UserBlockingService.list_blocked_users()

        if result['success']:
            return Response(result, status=status.HTTP_200_OK)
        else:
            return Response(
                ErrorMessageBuilder.system_error(
                    result.get('error_code', ErrorCodes.SYS_INTERNAL_ERROR),
                    result['error']
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    except Exception as e:
        import traceback
        print(f"Error in rbac_list_blocked_users: {e}")
        print(traceback.format_exc())
        return Response(
            ErrorMessageBuilder.system_error(
                ErrorCodes.SYS_INTERNAL_ERROR,
                str(e)
            ),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def rbac_check_access(request):
    """Check if a user can access the system (not blocked)"""
    try:
        username = request.query_params.get('username')

        if not username:
            username = request.user.username

        can_access, error_message = RBACGuard.can_access(username)

        return Response({
            'username': username,
            'can_access': can_access,
            'error': error_message if not can_access else None
        }, status=status.HTTP_200_OK)
    except Exception as e:
        import traceback
        print(f"Error in rbac_check_access: {e}")
        print(traceback.format_exc())
        return Response(
            ErrorMessageBuilder.system_error(
                ErrorCodes.SYS_INTERNAL_ERROR,
                str(e)
            ),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def rbac_get_conflicts(request):
    """Get complete role conflict mapping"""
    from .models import RBACConfiguration

    try:
        config = RBACConfiguration.objects.get(config_type='conflicts')
        conflicts = config.config_data
    except RBACConfiguration.DoesNotExist:
        conflicts = ConflictResolver.DEFAULT_ROLE_CONFLICTS

    return Response({
        'role_conflicts': conflicts,
        'total_conflicts': len(conflicts)
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def rbac_get_eligibility(request):
    """Get role eligibility mapping"""
    from .models import RBACConfiguration

    try:
        config = RBACConfiguration.objects.get(config_type='eligibility')
        eligibility = config.config_data
    except RBACConfiguration.DoesNotExist:
        eligibility = EligibilityValidator.DEFAULT_ROLE_ELIGIBILITY

    return Response({
        'role_eligibility': eligibility,
        'total_roles': len(eligibility)
    }, status=status.HTTP_200_OK)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def rbac_update_config(request):
    """Update RBAC configuration (eligibility or conflicts)"""
    try:
        config_type = request.data.get('config_type')
        config_data = request.data.get('config_data')

        if not config_type or config_type not in ['eligibility', 'conflicts']:
            return Response(
                ErrorMessageBuilder.validation_error(
                    ErrorCodes.VAL_INVALID_DATA_FORMAT,
                    "Invalid config_type. Must be 'eligibility' or 'conflicts'"
                ),
                status=status.HTTP_400_BAD_REQUEST
            )

        if not isinstance(config_data, dict):
            return Response(
                ErrorMessageBuilder.validation_error(
                    ErrorCodes.VAL_INVALID_DATA_FORMAT,
                    "config_data must be a dictionary"
                ),
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update configuration in database
        from .models import RBACConfiguration
        config = RBACConfiguration.objects.get(config_type=config_type)
        config.config_data = config_data
        config.updated_by = request.user
        config.save()

        # Invalidate cached data
        if hasattr(EligibilityValidator, '_cache'):
            delattr(EligibilityValidator, '_cache')
        if hasattr(ConflictResolver, '_cache'):
            delattr(ConflictResolver, '_cache')

        return Response({
            'success': True,
            'message': f'{config_type.capitalize()} configuration updated successfully',
            'config_type': config_type,
            'config_data': config_data
        }, status=status.HTTP_200_OK)

    except RBACConfiguration.DoesNotExist:
        return Response(
            ErrorMessageBuilder.database_error(
                ErrorCodes.DB_RECORD_NOT_FOUND,
                f"Configuration '{config_type}' not found"
            ),
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        import traceback
        print(f"Error updating RBAC config: {e}")
        print(traceback.format_exc())
        return Response(
            ErrorMessageBuilder.system_error(
                ErrorCodes.SYS_INTERNAL_ERROR,
                str(e)
            ),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def rbac_manage_eligibility(request):
    """View or update eligibility rules"""
    from .models import RoleEligibilityRule

    if request.method == 'GET':
        rules = RoleEligibilityRule.objects.all()
        return Response({
            'rules': [
                {
                    'id': r.id,
                    'role_name': r.role_name,
                    'eligible_user_types': r.eligible_user_types
                }
                for r in rules
            ]
        })

    elif request.method == 'POST':
        role_name = request.data.get('role_name')
        eligible_types = request.data.get('eligible_user_types')

        if not role_name or not eligible_types:
            return Response(
                ErrorMessageBuilder.validation_error(
                    ErrorCodes.VAL_MISSING_REQUIRED_FIELD,
                    "role_name and eligible_user_types required"
                ),
                status=status.HTTP_400_BAD_REQUEST
            )

        rule, created = RoleEligibilityRule.objects.update_or_create(
            role_name=role_name,
            defaults={'eligible_user_types': eligible_types}
        )

        return Response({
            'success': True,
            'message': 'Eligibility rule updated',
            'rule': {
                'id': rule.id,
                'role_name': rule.role_name,
                'eligible_user_types': rule.eligible_user_types
            }
        })


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def rbac_manage_conflicts(request):
    """View or update conflict rules"""
    from .models import RoleConflictRule

    if request.method == 'GET':
        rules = RoleConflictRule.objects.all()
        return Response({
            'rules': [
                {
                    'id': r.id,
                    'role_name': r.role_name,
                    'conflicts_with': r.conflicts_with
                }
                for r in rules
            ]
        })

    elif request.method == 'POST':
        role_name = request.data.get('role_name')
        conflicts = request.data.get('conflicts_with')

        if not role_name or conflicts is None:
            return Response(
                ErrorMessageBuilder.validation_error(
                    ErrorCodes.VAL_MISSING_REQUIRED_FIELD,
                    "role_name and conflicts_with required"
                ),
                status=status.HTTP_400_BAD_REQUEST
            )

        rule, created = RoleConflictRule.objects.update_or_create(
            role_name=role_name,
            defaults={'conflicts_with': conflicts}
        )

        return Response({
            'success': True,
            'message': 'Conflict rule updated',
            'rule': {
                'id': rule.id,
                'role_name': rule.role_name,
                'conflicts_with': rule.conflicts_with
            }
        })
