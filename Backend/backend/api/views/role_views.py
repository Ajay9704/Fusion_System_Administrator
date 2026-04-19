"""
Role Management Views - Handles role designations, assignments, switching, and module access
Extracted from the monolithic views.py for enterprise architecture
"""

from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.db.models import Max

from ..models import (
    GlobalsDesignation, GlobalsHoldsdesignation, GlobalsModuleaccess
)
from ..serializers import (
    GlobalsDesignationSerializer, GlobalsModuleaccessSerializer,
    GlobalsHoldsDesignationSerializer
)
from ..audit import audit_log, create_audit_log, get_client_ip, get_user_agent


@api_view(['GET'])
def global_designation_list(request):
    """Get all available role designations"""
    records = GlobalsDesignation.objects.all()
    serializer = GlobalsDesignationSerializer(records, many=True)
    return Response(serializer.data)


@api_view(['POST'])
def get_category_designations(request):
    """Get designations filtered by category and basic status"""
    category = request.data.get('category', 'student')
    basic = request.data.get('basic', True)
    records = GlobalsDesignation.objects.filter(category=category, basic=basic)
    serializer = GlobalsDesignationSerializer(records, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@audit_log(action='CREATE_ROLE', model_name='GlobalsDesignation')
def add_designation(request):
    """Create a new role designation with default module access"""
    serializer = GlobalsDesignationSerializer(data=request.data)
    if serializer.is_valid():
        role = serializer.save()
        max_id = GlobalsModuleaccess.objects.aggregate(Max('id'))['id__max']
        new_id = (max_id or 0) + 1

        # Create default module access with all permissions set to False
        data = {
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

        module_serializer = GlobalsModuleaccessSerializer(data=data)
        if module_serializer.is_valid():
            module_serializer.save()

        return Response({
            'role': serializer.data,
            'modules': module_serializer.data
        }, status.HTTP_201_CREATED)
    else:
        return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
@audit_log(action='UPDATE_ROLE', model_name='GlobalsDesignation')
def update_designation(request):
    """Update existing role designation"""
    name = request.data.get('name')

    if not name:
        return Response({
            "error": "No name provided."
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        designation = GlobalsDesignation.objects.get(name=name)
    except GlobalsDesignation.DoesNotExist:
        return Response({
            "error": f"Designation with name '{name}' not found."
        }, status=status.HTTP_404_NOT_FOUND)

    partial = request.method == 'PATCH'
    serializer = GlobalsDesignationSerializer(
        designation,
        data=request.data,
        partial=partial
    )

    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def get_module_access(request):
    """Get module access permissions for a specific role"""
    role_name = request.query_params.get('designation')

    if not role_name:
        return Response({
            "error": "No role provided."
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        module_access = GlobalsModuleaccess.objects.get(designation=role_name)
    except GlobalsModuleaccess.DoesNotExist:
        return Response({
            "error": f"Module access for designation '{role_name}' not found."
        }, status=status.HTTP_404_NOT_FOUND)

    serializer = GlobalsModuleaccessSerializer(module_access)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
@audit_log(action='MODIFY_MODULE_ACCESS', model_name='GlobalsModuleaccess')
def modify_moduleaccess(request):
    """Modify module access permissions for a role"""
    role_name = request.data.get('designation')

    if not role_name:
        return Response({
            "error": "No role provided."
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        designation = GlobalsModuleaccess.objects.get(designation=role_name)
    except GlobalsModuleaccess.DoesNotExist:
        return Response({
            "error": f"Designation with name '{role_name}' not found."
        }, status=status.HTTP_404_NOT_FOUND)

    serializer = GlobalsModuleaccessSerializer(
        designation,
        data=request.data,
        partial=True
    )

    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_available_roles(request):
    """Get all roles available to the current user with details"""
    try:
        user = request.user

        # Get all role assignments for this user
        role_assignments = GlobalsHoldsdesignation.objects.filter(
            user=user
        ).select_related('designation').order_by('designation__name')

        roles = []
        for assignment in role_assignments:
            designation = assignment.designation
            is_active = True

            # Check temporal constraints
            is_valid = True
            validity_info = None
            if assignment.start_date or assignment.end_date:
                from datetime import date
                today = date.today()

                if assignment.start_date and today < assignment.start_date:
                    is_valid = False
                    validity_info = f"Starts on {assignment.start_date}"

                if assignment.end_date and today > assignment.end_date:
                    is_valid = False
                    validity_info = f"Expired on {assignment.end_date}"

            roles.append({
                'id': designation.id,
                'name': designation.name,
                'full_name': designation.full_name,
                'type': designation.type,
                'category': designation.category,
                'is_active': is_active,
                'is_valid': is_valid,
                'validity_info': validity_info,
                'start_date': assignment.start_date,
                'end_date': assignment.end_date,
            })

        return Response({
            'roles': roles,
            'total_roles': len(roles)
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            'error': 'Failed to fetch user roles',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@audit_log(action='SWITCH_ROLE', model_name='AuthUser')
def switch_user_role(request):
    """Switch the user's active role"""
    try:
        role_id = request.data.get('role_id')

        if not role_id:
            return Response({
                'error': 'Role ID is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        user = request.user

        # Check if user has this role
        try:
            role_assignment = GlobalsHoldsdesignation.objects.get(
                user=user,
                designation_id=role_id
            )
        except GlobalsHoldsdesignation.DoesNotExist:
            return Response({
                'error': 'You do not have this role'
            }, status=status.HTTP_403_FORBIDDEN)

        # Check if role is valid (temporal constraints)
        from datetime import date
        today = date.today()

        if role_assignment.start_date and today < role_assignment.start_date:
            return Response({
                'error': 'This role has not started yet',
                'detail': f'Role starts on {role_assignment.start_date}'
            }, status=status.HTTP_403_FORBIDDEN)

        if role_assignment.end_date and today > role_assignment.end_date:
            return Response({
                'error': 'This role has expired',
                'detail': f'Role expired on {role_assignment.end_date}'
            }, status=status.HTTP_403_FORBIDDEN)

        # Return role info to be stored in frontend session
        designation = role_assignment.designation

        return Response({
            'message': 'Role switched successfully',
            'active_role': {
                'id': designation.id,
                'name': designation.name,
                'full_name': designation.full_name,
                'type': designation.type,
            }
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            'error': 'Failed to switch role',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_current_active_role(request):
    """Get the currently active role for the user"""
    try:
        user = request.user

        # Get primary role (first role or most recently used)
        role_assignment = GlobalsHoldsdesignation.objects.filter(
            user=user
        ).select_related('designation').first()

        if not role_assignment:
            return Response({
                'active_role': None,
                'message': 'No active role found'
            }, status=status.HTTP_200_OK)

        designation = role_assignment.designation

        return Response({
            'active_role': {
                'id': designation.id,
                'name': designation.name,
                'full_name': designation.full_name,
                'type': designation.type,
                'category': designation.category,
            },
            'message': 'Active role retrieved successfully'
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            'error': 'Failed to get active role',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)