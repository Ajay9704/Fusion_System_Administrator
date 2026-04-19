"""
Emergency Access Model
Provides temporary role escalation functionality
"""

from django.db import models
from django.utils import timezone
from datetime import timedelta

class EmergencyAccess(models.Model):
    """Emergency access requests for temporary role escalation"""

    # Request details
    requester = models.ForeignKey('AuthUser', on_delete=models.CASCADE, related_name='emergency_requests')
    requested_role = models.ForeignKey('GlobalsDesignation', on_delete=models.CASCADE)
    reason = models.TextField()
    duration_hours = models.IntegerField(default=24)

    # Status tracking
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('DENIED', 'Denied'),
        ('ACTIVE', 'Active'),
        ('EXPIRED', 'Expired'),
        'REVOKED', 'Revoked'),
    ]

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')

    # Approval details
    reviewer = models.ForeignKey('AuthUser', on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_emergency_requests')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    approval_action = models.CharField(max_length=20, null=True, blank=True)  # 'approve' or 'deny'
    approval_reason = models.TextField(blank=True)

    # Active period tracking
    activated_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    revoke_reason = models.TextField(blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'emergency_access'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.requester.username} - {self.requested_role.full_name} ({self.status})"

    def is_active(self):
        """Check if emergency access is currently active"""
        if self.status != 'ACTIVE':
            return False

        if self.expires_at and timezone.now() > self.expires_at:
            # Auto-expire if past expiration time
            self.status = 'EXPIRED'
            self.save()
            return False

        return True

    def can_activate(self):
        """Check if this request can be activated"""
        return self.status == 'APPROVED' and not self.activated_at

    def expire(self):
        """Mark this emergency access as expired"""
        self.status = 'EXPIRED'
        self.save()
