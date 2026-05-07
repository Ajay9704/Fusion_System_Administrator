"""
WebSocket consumers for real-time Emergency Access updates
"""
import json
import channels
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone

from .models import EmergencyAccessRequest, TemporaryRoleAssignment


class EmergencyAccessConsumer(AsyncJsonWebsocketConsumer):
    """
    WebSocket consumer for real-time emergency access updates
    Broadcasts updates to all connected admin users
    """

    async def connect(self):
        """Handle WebSocket connection"""
        await self.accept()
        self.user = self.scope["user"]

        # Send initial data
        await self.send_initial_data()

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        pass

    async def receive(self, text_data):
        """Handle incoming WebSocket messages"""
        data = json.loads(text_data)

        if data.get('type') == 'refresh':
            # Client is requesting a refresh
            await self.send_initial_data()

    async def send_initial_data(self):
        """Send initial data when client connects"""
        try:
            # Get current stats
            stats = await self.get_emergency_access_stats()

            # Get pending requests
            pending_requests = await self.get_pending_requests()

            # Get recent activity
            recent_activity = await self.get_recent_activity()

            await self.send_json({
                'type': 'initial_data',
                'stats': stats,
                'pending_requests': pending_requests,
                'recent_activity': recent_activity,
            })
        except Exception as e:
            await self.send_json({
                'type': 'error',
                'message': str(e),
            })

    @database_sync_to_async
    def get_emergency_access_stats(self):
        """Get current statistics"""
        from django.contrib.auth import get_user_model

        User = get_user_model()

        return {
            'pending_count': EmergencyAccessRequest.objects.filter(
                status=EmergencyAccessRequest.Status.PENDING
            ).count(),
            'approved_count': EmergencyAccessRequest.objects.filter(
                status=EmergencyAccessRequest.Status.APPROVED
            ).count(),
            'active_count': TemporaryRoleAssignment.objects.filter(
                is_active=True,
                expires_at__gt=timezone.now()
            ).count(),
            'total_requests': EmergencyAccessRequest.objects.count(),
            'total_users': User.objects.filter(is_active=True).count(),
        }

    @database_sync_to_async
    def get_pending_requests(self):
        """Get all pending requests with full details"""
        pending = EmergencyAccessRequest.objects.filter(
            status=EmergencyAccessRequest.Status.PENDING
        ).select_related('user', 'role').order_by('-requested_at')

        return [{
            'id': req.id,
            'user': {
                'id': req.user.id,
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
            'requested_at': req.requested_at.isoformat(),
        } for req in pending]

    @database_sync_to_async
    def get_recent_activity(self):
        """Get recent emergency access activity"""
        recent = EmergencyAccessRequest.objects.select_related(
            'user', 'role', 'reviewed_by'
        ).order_by('-requested_at')[:20]

        activity = []
        for req in recent:
            activity.append({
                'id': req.id,
                'user': req.user.username,
                'role': req.role.name,
                'status': req.status,
                'requested_at': req.requested_at.isoformat(),
                'reviewed_at': req.reviewed_at.isoformat() if req.reviewed_at else None,
                'reviewed_by': req.reviewed_by.username if req.reviewed_by else None,
                'expires_at': req.expires_at.isoformat() if req.expires_at else None,
                'requested_duration': req.requested_duration,
                'approved_duration': req.approved_duration,
                'rejection_reason': req.rejection_reason,
            })

        return activity

    @classmethod
    async def broadcast_update(cls, event_type, data):
        """
        Broadcast updates to all connected WebSocket clients

        This is a class method that can be called from views/services
        to send real-time updates to all connected clients.
        """
        # Get the channel layer
        channel_layer = channels.layers.get_channel_layer()

        # Broadcast to all clients in the 'emergency_access' group
        await channel_layer.group_send(
            'emergency_access',
            {
                'type': 'emergency_access.update',
                'event_type': event_type,
                'data': data,
            }
        )

    async def emergency_access_update(self, event):
        """
        Handle broadcast updates from the channel layer
        This method is called when an event is broadcast to the group
        """
        # Send the update to this specific client
        await self.send_json({
            'type': event['event_type'],
            'data': event['data'],
        })
