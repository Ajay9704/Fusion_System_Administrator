"""
Emergency Access & Handover Views - Handles emergency access requests, approvals, and handover documentation
Extracted from the monolithic views.py for enterprise architecture
"""

from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from django.utils import timezone

from ..models import (
    GlobalsDesignation, GlobalsHoldsdesignation,
    EmergencyAccess, HandoverDocumentation
)
from ..emergency_handover_serializers import (
    EmergencyAccessSerializer, HandoverDocumentationSerializer
)
from ..audit import audit_log, create_audit_log, get_client_ip, get_user_agent


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def request_emergency_access(request):
    """Request emergency access to a role"""
    try:
        role_id = request.data.get('role_id')
        reason = request.data.get('reason')
        duration_hours = request.data.get('duration_hours', 24)

        # Validation
        if not role_id:
            return Response({
                'error': 'Role ID is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        if not reason or not reason.strip():
            return Response({
                'error': 'Reason is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Check if role exists
        try:
            requested_role = GlobalsDesignation.objects.get(id=role_id)
        except GlobalsDesignation.DoesNotExist:
            return Response({
                'error': 'Role not found'
            }, status=status.HTTP_404_NOT_FOUND)

        # Check if user already has this role
        user = request.user
        if GlobalsHoldsdesignation.objects.filter(
            user=user,
            designation=requested_role
        ).exists():
            return Response({
                'error': 'You already have this role',
                'detail': 'Emergency access is not needed for roles you already possess'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Check if there's already a pending or active request for this role
        existing_request = EmergencyAccess.objects.filter(
            requester=user,
            requested_role=requested_role,
            status__in=['PENDING', 'APPROVED', 'ACTIVE']
        ).first()

        if existing_request:
            return Response({
                'error': 'Existing request found',
                'detail': f'You already have a {existing_request.get_status_display()} request for this role'
            }, status=status.HTTP_409_CONFLICT)

        # Create emergency access request
        emergency_access = EmergencyAccess.objects.create(
            requester=user,
            requested_role=requested_role,
            reason=reason.strip(),
            duration_hours=duration_hours,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request)
        )

        return Response({
            'message': 'Emergency access request submitted successfully',
            'request_id': emergency_access.id,
            'status': emergency_access.status,
            'requested_role': {
                'id': requested_role.id,
                'name': requested_role.name,
                'full_name': requested_role.full_name
            },
            'duration_hours': duration_hours
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({
            'error': 'Failed to create emergency access request',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_emergency_access_requests(request):
    """List emergency access requests with filtering"""
    try:
        # Get filters
        status_filter = request.query_params.get('status')
        requester_filter = request.query_params.get('requester')
        view_type = request.query_params.get('view', 'my-requests')

        # Build queryset
        queryset = EmergencyAccess.objects.select_related(
            'requester', 'approver', 'requested_role'
        ).order_by('-created_at')

        # Apply status filter
        if status_filter:
            queryset = queryset.filter(status=status_filter.upper())

        # Determine which requests to show based on view type
        if view_type == 'all-requests':
            # Admin-only: Show all requests
            if not request.user.is_superuser and not request.user.is_staff:
                return Response({
                    'error': 'Permission denied',
                    'detail': 'Only administrators can view all requests'
                }, status=status.HTTP_403_FORBIDDEN)
            if requester_filter:
                queryset = queryset.filter(requester__username=requester_filter)
        else:
            # Default: Show only current user's own requests
            queryset = queryset.filter(requester=request.user)

        requests = queryset[:100]  # Limit to 100 most recent

        request_data = []
        for req in requests:
            request_data.append({
                'id': req.id,
                'requester': {
                    'username': req.requester.username,
                    'email': req.requester.email
                },
                'requested_role': {
                    'id': req.requested_role.id,
                    'name': req.requested_role.name,
                    'full_name': req.requested_role.full_name
                },
                'reason': req.reason,
                'status': req.status,
                'duration_hours': req.duration_hours,
                'created_at': req.created_at.isoformat(),
                'expires_at': req.expires_at.isoformat() if req.expires_at else None,
                'is_active': req.is_active(),
                'is_expired': req.is_expired(),
                'approver': req.approver.username if req.approver else None,
                'approval_reason': req.approval_reason
            })

        return Response({
            'requests': request_data,
            'total': len(request_data)
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            'error': 'Failed to fetch emergency access requests',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@audit_log(action='EMERGENCY_ACCESS_APPROVE', model_name='EmergencyAccess')
def approve_emergency_access(request, request_id):
    """Approve or deny an emergency access request"""
    try:
        # Only admins can approve
        if not request.user.is_staff and not request.user.is_superuser:
            return Response({
                'error': 'Permission denied',
                'detail': 'Only administrators can approve emergency access requests'
            }, status=status.HTTP_403_FORBIDDEN)

        action = request.data.get('action')
        reason = request.data.get('reason', '')

        if action not in ['approve', 'deny']:
            return Response({
                'error': 'Invalid action',
                'detail': 'Action must be either "approve" or "deny"'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Get the request
        try:
            emergency_request = EmergencyAccess.objects.get(id=request_id)
        except EmergencyAccess.DoesNotExist:
            return Response({
                'error': 'Request not found'
            }, status=status.HTTP_404_NOT_FOUND)

        # SECURITY: Prevent admins from approving their own requests
        if emergency_request.requester == request.user:
            return Response({
                'error': 'Self-approval not allowed',
                'detail': 'You cannot approve or deny your own emergency access request'
            }, status=status.HTTP_403_FORBIDDEN)

        # Check if request can be approved/denied
        if emergency_request.status != 'PENDING':
            return Response({
                'error': 'Request cannot be processed',
                'detail': f'Request status is {emergency_request.get_status_display()}'
            }, status=status.HTTP_400_BAD_REQUEST)

        if action == 'deny':
            emergency_request.status = 'DENIED'
            emergency_request.approver = request.user
            emergency_request.approval_reason = reason
            emergency_request.save()

            return Response({
                'message': 'Emergency access request denied',
                'request_id': emergency_request.id
            }, status=status.HTTP_200_OK)

        # Approve the request
        emergency_request.status = 'APPROVED'
        emergency_request.approver = request.user
        emergency_request.approval_reason = reason
        emergency_request.save()

        return Response({
            'message': 'Emergency access request approved',
            'request_id': emergency_request.id,
            'status': 'APPROVED',
            'note': 'Request must be activated by the requester to become active'
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            'error': 'Failed to process emergency access request',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@audit_log(action='EMERGENCY_ACCESS_ACTIVATE', model_name='EmergencyAccess')
def activate_emergency_access(request, request_id):
    """Activate an approved emergency access request"""
    try:
        # Get the request
        try:
            emergency_request = EmergencyAccess.objects.get(id=request_id)
        except EmergencyAccess.DoesNotExist:
            return Response({
                'error': 'Request not found'
            }, status=status.HTTP_404_NOT_FOUND)

        # Security: Only requester can activate their own request
        if emergency_request.requester != request.user:
            return Response({
                'error': 'Permission denied',
                'detail': 'You can only activate your own emergency access requests'
            }, status=status.HTTP_403_FORBIDDEN)

        # Check if request can be activated
        if emergency_request.status != 'APPROVED':
            return Response({
                'error': 'Request cannot be activated',
                'detail': f'Request status is {emergency_request.get_status_display()}'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Activate the emergency access
        emergency_request.activate()

        # Grant the role temporarily
        GlobalsHoldsdesignation.objects.create(
            user=emergency_request.requester,
            designation=emergency_request.requested_role,
            working=emergency_request.requester.id
        )

        return Response({
            'message': 'Emergency access activated successfully',
            'request_id': emergency_request.id,
            'status': 'ACTIVE',
            'expires_at': emergency_request.expires_at.isoformat(),
            'duration_hours': emergency_request.duration_hours,
            'role': {
                'id': emergency_request.requested_role.id,
                'name': emergency_request.requested_role.name,
                'full_name': emergency_request.requested_role.full_name
            }
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            'error': 'Failed to activate emergency access',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@audit_log(action='EMERGENCY_ACCESS_REVOKE', model_name='EmergencyAccess')
def revoke_emergency_access(request, request_id):
    """Revoke an active emergency access"""
    try:
        reason = request.data.get('reason', '')

        # Get the request
        try:
            emergency_request = EmergencyAccess.objects.get(id=request_id)
        except EmergencyAccess.DoesNotExist:
            return Response({
                'error': 'Request not found'
            }, status=status.HTTP_404_NOT_FOUND)

        # Security: Only approver (admin) or requester can revoke
        if (emergency_request.requester != request.user and
            emergency_request.approver != request.user and
            not request.user.is_superuser):
            return Response({
                'error': 'Permission denied',
                'detail': 'Only requester, approver, or superuser can revoke'
            }, status=status.HTTP_403_FORBIDDEN)

        # Check if request is active
        if emergency_request.status != 'ACTIVE':
            return Response({
                'error': 'Request is not active',
                'detail': f'Cannot revoke {emergency_request.get_status_display()} request'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Revoke the emergency access
        emergency_request.revoke(reason)

        # Remove the temporary role assignment
        GlobalsHoldsdesignation.objects.filter(
            user=emergency_request.requester,
            designation=emergency_request.requested_role
        ).delete()

        return Response({
            'message': 'Emergency access revoked successfully',
            'request_id': emergency_request.id,
            'status': 'REVOKED'
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            'error': 'Failed to revoke emergency access',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_expired_emergency_access(request):
    """Check and automatically expire any emergency access that has passed its end time"""
    try:
        expired_requests = EmergencyAccess.objects.filter(
            status='ACTIVE',
            access_end_time__lt=timezone.now()
        )

        count = expired_requests.count()

        # Auto-expire them
        for emergency_request in expired_requests:
            emergency_request.status = 'EXPIRED'
            emergency_request.save()

            # Remove the temporary role assignment
            GlobalsHoldsdesignation.objects.filter(
                user=emergency_request.requester,
                designation=emergency_request.requested_role
            ).delete()

        return Response({
            'message': f'Expired {count} emergency access requests',
            'expired_count': count
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            'error': 'Failed to check expired emergency access',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_handover_documents(request):
    """List all handover documents with filtering"""
    try:
        handovers = HandoverDocumentation.objects.all()

        # Filter by user
        user_filter = request.query_params.get('user')
        if user_filter:
            handovers = handovers.filter(
                Q(from_user__username__icontains=user_filter) |
                Q(to_user__username__icontains=user_filter)
            )

        # Filter by status
        status_filter = request.query_params.get('status')
        if status_filter:
            handovers = handovers.filter(status=status_filter)

        serializer = HandoverDocumentationSerializer(handovers, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            'error': 'Failed to retrieve handover documents',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_handover_document(request):
    """Create a new handover document"""
    try:
        data = request.data.copy()
        data['from_user'] = request.user.id

        serializer = HandoverDocumentationSerializer(data=data)
        if serializer.is_valid():
            handover = serializer.save()
            return Response({
                'message': 'Handover document created successfully',
                'data': HandoverDocumentationSerializer(handover).data
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        return Response({
            'error': 'Failed to create handover document',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def accept_handover(request, handover_id):
    """Accept a handover document"""
    try:
        handover = HandoverDocumentation.objects.get(id=handover_id)

        if handover.to_user != request.user:
            return Response({
                'error': 'Only the assigned user can accept this handover'
            }, status=status.HTTP_403_FORBIDDEN)

        if handover.status != 'PENDING':
            return Response({
                'error': 'Handover cannot be accepted in current status'
            }, status=status.HTTP_400_BAD_REQUEST)

        handover.status = 'IN_PROGRESS'
        handover.accepted_at = timezone.now()
        handover.to_user_confirmation = True
        handover.save()

        return Response({
            'message': 'Handover accepted successfully',
            'data': HandoverDocumentationSerializer(handover).data
        }, status=status.HTTP_200_OK)

    except HandoverDocumentation.DoesNotExist:
        return Response({
            'error': 'Handover document not found'
        }, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        return Response({
            'error': 'Failed to accept handover',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def complete_handover(request, handover_id):
    """Mark a handover as complete"""
    try:
        handover = HandoverDocumentation.objects.get(id=handover_id)

        # Check permissions
        if handover.from_user != request.user and handover.to_user != request.user:
            return Response({
                'error': 'You do not have permission to complete this handover'
            }, status=status.HTTP_403_FORBIDDEN)

        if handover.status != 'IN_PROGRESS':
            return Response({
                'error': 'Handover must be in progress to be completed'
            }, status=status.HTTP_400_BAD_REQUEST)

        handover.status = 'COMPLETED'
        handover.completed_at = timezone.now()
        handover.progress_percentage = 100
        handover.save()

        return Response({
            'message': 'Handover completed successfully',
            'data': HandoverDocumentationSerializer(handover).data
        }, status=status.HTTP_200_OK)

    except HandoverDocumentation.DoesNotExist:
        return Response({
            'error': 'Handover document not found'
        }, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        return Response({
            'error': 'Failed to complete handover',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cancel_handover(request, handover_id):
    """Cancel a handover document"""
    try:
        handover = HandoverDocumentation.objects.get(id=handover_id)

        # Only from_user or supervisor can cancel
        if handover.from_user != request.user and handover.supervisor != request.user:
            return Response({
                'error': 'You do not have permission to cancel this handover'
            }, status=status.HTTP_403_FORBIDDEN)

        if handover.status in ['COMPLETED', 'CANCELLED']:
            return Response({
                'error': 'Cannot cancel handover in current status'
            }, status=status.HTTP_400_BAD_REQUEST)

        handover.status = 'CANCELLED'
        handover.save()

        return Response({
            'message': 'Handover cancelled successfully',
            'data': HandoverDocumentationSerializer(handover).data
        }, status=status.HTTP_200_OK)

    except HandoverDocumentation.DoesNotExist:
        return Response({
            'error': 'Handover document not found'
        }, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        return Response({
            'error': 'Failed to cancel handover',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)