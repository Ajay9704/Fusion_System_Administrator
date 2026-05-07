"""
Emergency Access (Just-In-Time Role Access) API Views
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import EmergencyAccessRequest, TemporaryRoleAssignment
from .services import EmergencyAccessService
from .audit import create_audit_log, get_client_ip, get_user_agent
from .error_handlers import (
    ErrorCodes,
    ErrorMessageBuilder,
    AuditMessageBuilder
)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_emergency_access_request(request):
    """Create a new emergency access request"""
    try:
        user = request.user
        role_id = request.data.get('role_id')
        duration = request.data.get('requested_duration')
        reason = request.data.get('reason')

        if not all([role_id, duration, reason]):
            return Response(
                ErrorMessageBuilder.validation_error(
                    ErrorCodes.VAL_MISSING_REQUIRED_FIELD,
                    "role_id, requested_duration, and reason are required"
                ),
                status=status.HTTP_400_BAD_REQUEST
            )

        emergency_request = EmergencyAccessService.create_request(
            user=user,
            role_id=role_id,
            duration=duration,
            reason=reason
        )

        create_audit_log(
            user=user,
            action='EMERGENCY_ACCESS_REQUEST_CREATED',
            model_name='EmergencyAccessRequest',
            object_id=str(emergency_request.id),
            description=f"User {user.username} requested emergency access for role {emergency_request.role.name}",
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
            status='SUCCESS'
        )

        # Broadcast real-time update using fire-and-forget pattern
        from .consumers import EmergencyAccessConsumer
        import threading

        def broadcast_update():
            """Run WebSocket broadcast in background thread to avoid blocking response"""
            try:
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(EmergencyAccessConsumer.broadcast_update(
                    'request_created',
                    {
                        'id': emergency_request.id,
                        'user': user.username,
                        'role': emergency_request.role.name,
                        'requested_duration': emergency_request.requested_duration,
                        'requested_at': emergency_request.requested_at.isoformat(),
                    }
                ))
                loop.close()
            except Exception as e:
                # Log but don't fail the request if WebSocket broadcast fails
                print(f"WebSocket broadcast failed: {e}")

        # Start broadcast in background thread (fire-and-forget)
        broadcast_thread = threading.Thread(target=broadcast_update, daemon=True)
        broadcast_thread.start()

        return Response({
            'id': emergency_request.id,
            'role': emergency_request.role.name,
            'requested_duration': emergency_request.requested_duration,
            'status': emergency_request.status,
            'requested_at': emergency_request.requested_at.isoformat(),
            'message': 'Emergency access request created successfully'
        }, status=status.HTTP_201_CREATED)

    except ValidationError as e:
        return Response(
            ErrorMessageBuilder.validation_error(
                ErrorCodes.VAL_INVALID_DATA_FORMAT,
                str(e)
            ),
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        create_audit_log(
            user=request.user,
            action='EMERGENCY_ACCESS_REQUEST_CREATED',
            model_name='EmergencyAccessRequest',
            description=f"Failed to create emergency access request: {str(e)}",
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
            status='FAILED'
        )
        return Response(
            ErrorMessageBuilder.system_error(str(e)),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_my_emergency_requests(request):
    """Get current user's emergency access requests"""
    try:
        user = request.user
        requests = EmergencyAccessService.get_user_requests(user)

        requests_data = [{
            'id': req.id,
            'role': req.role.name,
            'reason': req.reason,
            'requested_duration': req.requested_duration,
            'approved_duration': req.approved_duration,
            'status': req.status,
            'requested_at': req.requested_at.isoformat() if req.requested_at else None,
            'reviewed_at': req.reviewed_at.isoformat() if req.reviewed_at else None,
            'reviewed_by': req.reviewed_by.username if req.reviewed_by else None,
            'expires_at': req.expires_at.isoformat() if req.expires_at else None,
            'is_active': req.is_active()
        } for req in requests]

        return Response(requests_data, status=status.HTTP_200_OK)

    except Exception as e:
        return Response(
            ErrorMessageBuilder.system_error(str(e)),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_emergency_requests(request):
    """Get all emergency access requests (Admin only)"""
    try:
        limit = request.query_params.get('limit', 100)
        requests = EmergencyAccessService.get_all_requests(limit=int(limit))

        requests_data = [{
            'id': req.id,
            'user': req.user.username,
            'role': req.role.name,
            'reason': req.reason,
            'requested_duration': req.requested_duration,
            'approved_duration': req.approved_duration,
            'status': req.status,
            'requested_at': req.requested_at.isoformat() if req.requested_at else None,
            'reviewed_at': req.reviewed_at.isoformat() if req.reviewed_at else None,
            'reviewed_by': req.reviewed_by.username if req.reviewed_by else None,
            'expires_at': req.expires_at.isoformat() if req.expires_at else None,
            'rejection_reason': req.rejection_reason,
            'duration_modified_reason': req.duration_modified_reason,
        } for req in requests]

        return Response(requests_data, status=status.HTTP_200_OK)

    except Exception as e:
        return Response(
            ErrorMessageBuilder.system_error(str(e)),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_pending_emergency_requests(request):
    """Get all pending emergency access requests (Admin only)"""
    try:
        requests = EmergencyAccessService.get_pending_requests()

        requests_data = [{
            'id': req.id,
            'user': req.user.username,
            'user_email': req.user.email,
            'role': req.role.name,
            'reason': req.reason,
            'requested_duration': req.requested_duration,
            'requested_at': req.requested_at.isoformat() if req.requested_at else None,
        } for req in requests]

        return Response(requests_data, status=status.HTTP_200_OK)

    except Exception as e:
        return Response(
            ErrorMessageBuilder.system_error(str(e)),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_emergency_request_detail(request, request_id):
    """Get detailed information about a specific request"""
    try:
        req = EmergencyAccessService.get_request_detail(request_id)

        if not req:
            return Response(
                ErrorMessageBuilder.validation_error(
                    ErrorCodes.VAL_INVALID_DATA_FORMAT,
                    "Request not found"
                ),
                status=status.HTTP_404_NOT_FOUND
            )

        request_data = {
            'id': req.id,
            'user': {
                'username': req.user.username,
                'email': req.user.email,
                'first_name': req.user.first_name,
                'last_name': req.user.last_name,
            },
            'role': {
                'id': req.role.id,
                'name': req.role.name,
                'full_name': req.role.full_name,
            },
            'reason': req.reason,
            'requested_duration': req.requested_duration,
            'approved_duration': req.approved_duration,
            'status': req.status,
            'requested_at': req.requested_at.isoformat() if req.requested_at else None,
            'reviewed_at': req.reviewed_at.isoformat() if req.reviewed_at else None,
            'reviewed_by': {
                'username': req.reviewed_by.username,
                'email': req.reviewed_by.email,
            } if req.reviewed_by else None,
            'expires_at': req.expires_at.isoformat() if req.expires_at else None,
            'rejection_reason': req.rejection_reason,
            'duration_modified_reason': req.duration_modified_reason,
            'is_active': req.is_active(),
        }

        return Response(request_data, status=status.HTTP_200_OK)

    except Exception as e:
        return Response(
            ErrorMessageBuilder.system_error(str(e)),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def approve_emergency_request(request, request_id):
    """Approve an emergency access request (Admin only)"""
    try:
        admin_user = request.user
        approved_duration = request.data.get('approved_duration')
        duration_reason = request.data.get('duration_modified_reason')

        emergency_request = EmergencyAccessService.approve_request(
            request_id=request_id,
            admin_user=admin_user,
            approved_duration=approved_duration,
            duration_reason=duration_reason
        )

        action = 'EMERGENCY_ACCESS_REQUEST_APPROVED'
        if approved_duration is not None:
            action = 'EMERGENCY_ACCESS_REQUEST_APPROVED_MODIFIED'

        create_audit_log(
            user=admin_user,
            action=action,
            model_name='EmergencyAccessRequest',
            object_id=str(emergency_request.id),
            description=f"Admin {admin_user.username} approved emergency access request for {emergency_request.user.username} -> {emergency_request.role.name}",
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
            status='SUCCESS'
        )

        # Convert datetime to ISO format string for JSON serialization
        expires_at_str = emergency_request.expires_at.isoformat() if emergency_request.expires_at else None

        response_data = {
            'id': emergency_request.id,
            'user': emergency_request.user.username,
            'role': emergency_request.role.name,
            'requested_duration': emergency_request.requested_duration,
            'approved_duration': emergency_request.approved_duration,
            'expires_at': expires_at_str,
            'status': emergency_request.status,
            'message': 'Emergency access request approved successfully'
        }

        if approved_duration is not None:
            response_data['duration_modified'] = True
            response_data['duration_modified_reason'] = duration_reason

        # Broadcast real-time update
        from .consumers import EmergencyAccessConsumer
        import threading

        def broadcast_approval():
            try:
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(EmergencyAccessConsumer.broadcast_update(
                    'request_approved',
                    {
                        'id': emergency_request.id,
                        'user': emergency_request.user.username,
                        'role': emergency_request.role.name,
                        'approved_duration': emergency_request.approved_duration,
                        'expires_at': expires_at_str,
                        'approved_by': admin_user.username,
                    }
                ))
                loop.close()
            except Exception as e:
                print(f"WebSocket broadcast failed: {e}")

        broadcast_thread = threading.Thread(target=broadcast_approval, daemon=True)
        broadcast_thread.start()

        return Response(response_data, status=status.HTTP_200_OK)

    except ValidationError as e:
        return Response(
            ErrorMessageBuilder.validation_error(
                ErrorCodes.VAL_INVALID_DATA_FORMAT,
                str(e)
            ),
            status=status.HTTP_400_BAD_REQUEST
        )
    except EmergencyAccessRequest.DoesNotExist:
        return Response(
            ErrorMessageBuilder.validation_error(
                ErrorCodes.VAL_INVALID_DATA_FORMAT,
                "Request not found"
            ),
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        create_audit_log(
            user=request.user,
            action='EMERGENCY_ACCESS_REQUEST_APPROVED',
            model_name='EmergencyAccessRequest',
            object_id=str(request_id),
            description=f"Failed to approve emergency access request: {str(e)}",
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
            status='FAILED'
        )
        return Response(
            ErrorMessageBuilder.system_error(str(e)),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def reject_emergency_request(request, request_id):
    """Reject an emergency access request (Admin only)"""
    try:
        admin_user = request.user
        reason = request.data.get('rejection_reason')

        emergency_request = EmergencyAccessService.reject_request(
            request_id=request_id,
            admin_user=admin_user,
            reason=reason
        )

        create_audit_log(
            user=admin_user,
            action='EMERGENCY_ACCESS_REQUEST_REJECTED',
            model_name='EmergencyAccessRequest',
            object_id=str(emergency_request.id),
            description=f"Admin {admin_user.username} rejected emergency access request for {emergency_request.user.username} -> {emergency_request.role.name}",
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
            reason=reason,
            status='SUCCESS'
        )

        # Broadcast real-time update
        from .consumers import EmergencyAccessConsumer
        import threading

        def broadcast_rejection():
            try:
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(EmergencyAccessConsumer.broadcast_update(
                    'request_rejected',
                    {
                        'id': emergency_request.id,
                        'user': emergency_request.user.username,
                        'role': emergency_request.role.name,
                        'rejected_by': admin_user.username,
                    }
                ))
                loop.close()
            except Exception as e:
                print(f"WebSocket broadcast failed: {e}")

        broadcast_thread = threading.Thread(target=broadcast_rejection, daemon=True)
        broadcast_thread.start()

        return Response({
            'id': emergency_request.id,
            'user': emergency_request.user.username,
            'role': emergency_request.role.name,
            'status': emergency_request.status,
            'rejection_reason': emergency_request.rejection_reason,
            'message': 'Emergency access request rejected successfully'
        }, status=status.HTTP_200_OK)

    except ValidationError as e:
        return Response(
            ErrorMessageBuilder.validation_error(
                ErrorCodes.VAL_INVALID_DATA_FORMAT,
                str(e)
            ),
            status=status.HTTP_400_BAD_REQUEST
        )
    except EmergencyAccessRequest.DoesNotExist:
        return Response(
            ErrorMessageBuilder.validation_error(
                ErrorCodes.VAL_INVALID_DATA_FORMAT,
                "Request not found"
            ),
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        create_audit_log(
            user=request.user,
            action='EMERGENCY_ACCESS_REQUEST_REJECTED',
            model_name='EmergencyAccessRequest',
            object_id=str(request_id),
            description=f"Failed to reject emergency access request: {str(e)}",
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
            status='FAILED'
        )
        return Response(
            ErrorMessageBuilder.system_error(str(e)),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def withdraw_emergency_request(request, request_id):
    """Withdraw an approved emergency access request (Admin only)"""
    try:
        admin_user = request.user
        reason = request.data.get('revocation_reason')

        emergency_request = EmergencyAccessService.withdraw_request(
            request_id=request_id,
            admin_user=admin_user,
            reason=reason
        )

        create_audit_log(
            user=admin_user,
            action='EMERGENCY_ACCESS_WITHDRAWN',
            model_name='EmergencyAccessRequest',
            object_id=str(emergency_request.id),
            description=f"Admin {admin_user.username} withdrew emergency access for {emergency_request.user.username} -> {emergency_request.role.name}",
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
            reason=reason,
            status='SUCCESS'
        )

        # Broadcast real-time update
        from .consumers import EmergencyAccessConsumer
        import threading

        def broadcast_withdrawal():
            try:
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(EmergencyAccessConsumer.broadcast_update(
                    'request_withdrawn',
                    {
                        'id': emergency_request.id,
                        'user': emergency_request.user.username,
                        'role': emergency_request.role.name,
                        'withdrawn_by': admin_user.username,
                    }
                ))
                loop.close()
            except Exception as e:
                print(f"WebSocket broadcast failed: {e}")

        broadcast_thread = threading.Thread(target=broadcast_withdrawal, daemon=True)
        broadcast_thread.start()

        return Response({
            'id': emergency_request.id,
            'user': emergency_request.user.username,
            'role': emergency_request.role.name,
            'status': emergency_request.status,
            'message': 'Emergency access withdrawn successfully'
        }, status=status.HTTP_200_OK)

    except ValidationError as e:
        return Response(
            ErrorMessageBuilder.validation_error(
                ErrorCodes.VAL_INVALID_DATA_FORMAT,
                str(e)
            ),
            status=status.HTTP_400_BAD_REQUEST
        )
    except EmergencyAccessRequest.DoesNotExist:
        return Response(
            ErrorMessageBuilder.validation_error(
                ErrorCodes.VAL_INVALID_DATA_FORMAT,
                "Request not found"
            ),
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        create_audit_log(
            user=request.user,
            action='EMERGENCY_ACCESS_WITHDRAWN',
            model_name='EmergencyAccessRequest',
            object_id=str(request_id),
            description=f"Failed to withdraw emergency access: {str(e)}",
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
            status='FAILED'
        )
        return Response(
            ErrorMessageBuilder.system_error(str(e)),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def check_and_expire_roles(request):
    """Background job endpoint to check and expire temporary roles"""
    try:
        expired_count = EmergencyAccessService.check_and_expire_roles()

        return Response({
            'expired_count': expired_count,
            'message': f'Expired {expired_count} temporary role assignments'
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response(
            ErrorMessageBuilder.system_error(str(e)),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_active_temporary_roles(request):
    """Get current user's active temporary roles (auto-expires any expired roles first)"""
    try:
        # Auto-expire any expired roles before fetching
        EmergencyAccessService.check_and_expire_roles()
        
        user = request.user
        temp_roles = EmergencyAccessService.get_active_temporary_roles(user)

        roles_data = [{
            'id': role.id,
            'role_name': role.role.name,
            'role_full_name': role.role.full_name,
            'granted_at': role.granted_at,
            'expires_at': role.expires_at,
            'request_id': role.request.id,
            'is_active': role.is_valid(),
            'time_remaining_minutes': max(0, int((role.expires_at - timezone.now()).total_seconds() // 60)),
        } for role in temp_roles]

        return Response(roles_data, status=status.HTTP_200_OK)

    except Exception as e:
        return Response(
            ErrorMessageBuilder.system_error(str(e)),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
