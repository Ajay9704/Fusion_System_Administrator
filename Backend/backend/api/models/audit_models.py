"""
Audit and logging related models.
Handles system audit trails, action logging, and compliance tracking.
"""

from django.db import models


class AuditLog(models.Model):
    """
    Comprehensive audit log for tracking all system actions
    Records user actions with timestamp, IP, user agent, and status
    """

    id = models.AutoField(primary_key=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        'AuthUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    action = models.CharField(
        max_length=100,
        help_text="e.g., 'CREATE_USER', 'UPDATE_ROLE', 'ARCHIVE_USER'"
    )
    model_name = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="e.g., 'AuthUser', 'GlobalsDesignation'"
    )
    object_id = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )
    description = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Track browser/client"
    )
    reason = models.TextField(blank=True, null=True)
    status = models.CharField(
        max_length=20,
        default='SUCCESS',
        help_text="'SUCCESS' or 'FAILED'"
    )

    class Meta:
        managed = True
        db_table = 'audit_log'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['action', '-timestamp']),
            models.Index(fields=['status', '-timestamp']),
        ]

    def __str__(self):
        user_name = self.user.username if self.user else 'Unknown'
        return f"{self.timestamp} - {user_name} - {self.action}"