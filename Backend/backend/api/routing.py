"""
WebSocket routing for real-time updates
"""
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/emergency-access/$', consumers.EmergencyAccessConsumer.as_asgi()),
]
