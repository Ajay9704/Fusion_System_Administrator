"""
Audit Views - Handles audit log retrieval and filtering
Extracted from the monolithic views.py for enterprise architecture
"""

from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from ..models import AuditLog
from ..serializers import AuditLogSerializer


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_audit_logs(request):
    """
    Retrieve audit logs with filtering support.
    ADMIN ONLY - Only staff/superusers can access audit logs
    Query params:
    - start_date: Filter logs from this date (YYYY-MM-DD)
    - end_date: Filter logs until this date (YYYY-MM-DD)
    - user: Filter by username
    - action: Filter by action type
    - status: Filter by status (SUCCESS/FAILED)
    - page: Page number (default 1)
    - page_size: Number of results per page (default 50, max 200)
    """
    # Restrict to admin users only
    if not request.user.is_staff and not request.user.is_superuser:
        return Response({
            'error': 'Permission denied',
            'detail': 'Only administrators can access audit logs'
        }, status=status.HTTP_403_FORBIDDEN)

    # Start with all logs
    logs = AuditLog.objects.all()

    # Apply filters
    start_date = request.query_params.get('start_date')
    if start_date:
        try:
            from datetime import datetime
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            logs = logs.filter(timestamp__gte=start_dt)
        except ValueError:
            return Response({
                "error": "Invalid start_date format. Use YYYY-MM-DD"
            }, status=status.HTTP_400_BAD_REQUEST)

    end_date = request.query_params.get('end_date')
    if end_date:
        try:
            from datetime import timedelta
            end_dt = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
            logs = logs.filter(timestamp__lt=end_dt)
        except ValueError:
            return Response({
                "error": "Invalid end_date format. Use YYYY-MM-DD"
            }, status=status.HTTP_400_BAD_REQUEST)

    username = request.query_params.get('user')
    if username:
        logs = logs.filter(user__username__icontains=username)

    action = request.query_params.get('action')
    if action:
        logs = logs.filter(action__icontains=action)

    status_filter = request.query_params.get('status')
    if status_filter:
        logs = logs.filter(status=status_filter.upper())

    # Pagination
    try:
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 50))
        page_size = min(page_size, 200)  # Max 200 per page
    except ValueError:
        return Response({
            "error": "Invalid page or page_size parameter"
        }, status=status.HTTP_400_BAD_REQUEST)

    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size

    # Get total count and paginated results
    total_count = logs.count()
    logs = logs[start_idx:end_idx]

    serializer = AuditLogSerializer(logs, many=True)

    return Response({
        'count': total_count,
        'page': page,
        'page_size': page_size,
        'total_pages': (total_count + page_size - 1) // page_size,
        'results': serializer.data
    }, status=status.HTTP_200_OK)