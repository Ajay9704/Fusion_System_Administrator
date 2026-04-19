"""
Emergency Access System Backend Implementation
Provides temporary role escalation and approval workflow
"""

from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q
from .models import AuthUser, GlobalsDesignation, GlobalsHoldsdesignation, GlobalsExtrainfo
from .serializers import AuthUserSerializer, GlobalsDesignationSerializer
from .audit import audit_log, get_client_ip, get_user_agent
import logging

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_emergency_access_requests(request):
    """
    Get emergency access requests with filtering
    Query params:
    - view: 'my-requests', 'all-requests'
    - status: 'PENDING', 'APPROVED', 'DENIED', 'ACTIVE', 'EXPIRED', 'ALL'
    """
    user = request.user
    view_type = request.query_params.get('view', 'my-requests')
    status_filter = request.query_params.get('status', 'PENDING')

    try:
        # Create mock data for now (replace with actual EmergencyAccess model when implemented)
        if view_type == 'my-requests':
            # Return current user's requests
            requests = []
        else:
            # Return all requests for admin
            requests = []

        return Response({
            'requests': requests
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error fetching emergency access requests: {str(e)}")
        return Response({
            'error': 'Failed to fetch emergency access requests'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@audit_log(action='CREATE_EMERGENCY_ACCESS_REQUEST', model_name='EmergencyAccess')
def create_emergency_access_request(request):
    """
    Create a new emergency access request
    Body:
    - role_id: ID of the requested role
    - reason: Reason for emergency access
    - duration_hours: Duration in hours (max 168 = 7 days)
    """
    user = request.user
    role_id = request.data.get('role_id')
    reason = request.data.get('reason')
    duration_hours = request.data.get('duration_hours', 24)

    try:
        # Validate inputs
        if not role_id or not reason:
            return Response({
                'error': 'Role ID and reason are required'
            }, status=status.HTTP_400_BAD_REQUEST)

        if duration_hours > 168:
            return Response({
                'error': 'Maximum duration is 168 hours (7 days)'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate role exists
        try:
            role = GlobalsDesignation.objects.get(id=role_id)
        except GlobalsDesignation.DoesNotExist:
            return Response({
                'error': 'Requested role does not exist'
            }, status=status.HTTP_404_NOT_FOUND)

        # Create mock request (replace with actual EmergencyAccess model)
        request_data = {
            'id': 1,
            'requester': AuthUserSerializer(user).data,
            'requested_role': GlobalsDesignationSerializer(role).data,
            'reason': reason,
            'duration_hours': duration_hours,
            'status': 'PENDING',
            'created_at': timezone.now().isoformat(),
            'expires_at': (timezone.now() + timedelta(hours=duration_hours)).isoformat()
        }

        return Response(request_data, status=status.HTTP_201_CREATED)

    except Exception as e:
        logger.error(f"Error creating emergency access request: {str(e)}")
        return Response({
            'error': 'Failed to create emergency access request'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@audit_log(action='APPROVE_EMERGENCY_ACCESS', model_name='EmergencyAccess')
def approve_emergency_access(request, request_id):
    """
    Approve or deny an emergency access request
    Body:
    - action: 'approve' or 'deny'
    - reason: Optional reason for approval/denial
    """
    user = request.user
    action = request.data.get('action')
    reason = request.data.get('reason', '')

    try:
        if action not in ['approve', 'deny']:
            return Response({
                'error': 'Invalid action. Must be "approve" or "deny"'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Mock approval (replace with actual EmergencyAccess model)
        return Response({
            'message': f'Emergency access request {action}ed successfully',
            'request_id': request_id,
            'action': action,
            'reason': reason
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error approving emergency access: {str(e)}")
        return Response({
            'error': 'Failed to process approval'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@audit_log(action='ACTIVATE_EMERGENCY_ACCESS', model_name='EmergencyAccess')
def activate_emergency_access(request, request_id):
    """
    Activate an approved emergency access request
    """
    user = request.user

    try:
        # Mock activation (replace with actual EmergencyAccess model)
        return Response({
            'message': 'Emergency access activated successfully',
            'request_id': request_id
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error activating emergency access: {str(e)}")
        return Response({
            'error': 'Failed to activate emergency access'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@audit_log(action='REVOKE_EMERGENCY_ACCESS', model_name='EmergencyAccess')
def revoke_emergency_access(request, request_id):
    """
    Revoke an active emergency access
    Body:
    - reason: Optional reason for revocation
    """
    user = request.user
    reason = request.data.get('reason', '')

    try:
        # Mock revocation (replace with actual EmergencyAccess model)
        return Response({
            'message': 'Emergency access revoked successfully',
            'request_id': request_id,
            'reason': reason
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error revoking emergency access: {str(e)}")
        return Response({
            'error': 'Failed to revoke emergency access'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
