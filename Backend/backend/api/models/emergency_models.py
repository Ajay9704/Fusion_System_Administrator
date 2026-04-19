"""
Emergency access and handover related models.
Handles temporary role escalation, emergency access, and task handover workflows.
"""

from django.db import models


class EmergencyAccess(models.Model):
    """
    Emergency access system for temporary role escalation
    Allows requesting temporary elevated permissions with approval workflow
    """

    STATUS_CHOICES = [
        ('PENDING', 'Pending Approval'),
        ('APPROVED', 'Approved'),
        ('ACTIVE', 'Active'),
        ('EXPIRED', 'Expired'),
        ('REVOKED', 'Revoked'),
        ('DENIED', 'Denied'),
    ]

    id = models.AutoField(primary_key=True)
    requester = models.ForeignKey(
        'AuthUser',
        on_delete=models.CASCADE,
        related_name='emergency_requests'
    )
    approver = models.ForeignKey(
        'AuthUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_emergencies'
    )

    # Request details
    requested_role = models.ForeignKey(
        'GlobalsDesignation',
        on_delete=models.CASCADE,
        related_name='emergency_access_requests'
    )
    reason = models.TextField(help_text="Reason for emergency access request")

    # Approval details
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    approval_reason = models.TextField(
        blank=True,
        null=True,
        help_text="Reason for approval/denial"
    )

    # Temporal constraints
    created_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    activated_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)

    # Duration in hours (default 24 hours)
    duration_hours = models.IntegerField(
        default=24,
        help_text="Access duration in hours"
    )

    # Tracking
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'emergency_access'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['requester', '-created_at']),
            models.Index(fields=['expires_at']),
        ]

    def __str__(self):
        return f"Emergency Access #{self.id} - {self.requester.username} -> {self.requested_role.name} ({self.status})"

    def is_active(self):
        """Check if emergency access is currently active"""
        from django.utils import timezone
        now = timezone.now()

        if self.status != 'ACTIVE':
            return False

        if self.activated_at and self.expires_at:
            return self.activated_at <= now <= self.expires_at

        return False

    def is_expired(self):
        """Check if emergency access has expired"""
        from django.utils import timezone
        now = timezone.now()

        if self.expires_at and now > self.expires_at:
            return True

        return False

    def activate(self):
        """Activate the emergency access"""
        from django.utils import timezone
        from datetime import timedelta

        self.status = 'ACTIVE'
        self.activated_at = timezone.now()

        # Calculate expiration time
        if not self.expires_at:
            self.expires_at = self.activated_at + timedelta(hours=self.duration_hours)

        self.save()

    def revoke(self, reason=''):
        """Revoke the emergency access"""
        from django.utils import timezone

        self.status = 'REVOKED'
        self.revoked_at = timezone.now()
        if reason:
            self.approval_reason = reason
        self.save()

    def expire(self):
        """Mark as expired"""
        self.status = 'EXPIRED'
        self.save()


class HandoverDocumentation(models.Model):
    """
    Handover documentation system for task transfers and role transitions
    Tracks handover tasks, responsibilities, and completion status
    """

    STATUS_CHOICES = [
        ('PENDING', 'Pending Acceptance'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]

    PRIORITY_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
    ]

    id = models.AutoField(primary_key=True)

    # People involved
    from_user = models.ForeignKey(
        'AuthUser',
        on_delete=models.CASCADE,
        related_name='handovers_sent'
    )
    to_user = models.ForeignKey(
        'AuthUser',
        on_delete=models.CASCADE,
        related_name='handovers_received'
    )
    supervisor = models.ForeignKey(
        'AuthUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='supervised_handovers'
    )

    # Handover details
    title = models.CharField(max_length=200)
    description = models.TextField(
        help_text="Description of tasks and responsibilities being handed over"
    )
    department = models.ForeignKey(
        'GlobalsDepartmentinfo',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    # Categorization
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='MEDIUM')
    category = models.CharField(
        max_length=100,
        blank=True,
        help_text="e.g., Role Transition, Project Transfer, Administrative Tasks"
    )

    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    progress_percentage = models.IntegerField(
        default=0,
        help_text="Completion progress (0-100)"
    )

    # Dates
    created_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    deadline = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Expected completion date"
    )

    # Documentation
    responsibilities = models.TextField(
        blank=True,
        help_text="List of responsibilities being transferred"
    )
    resources = models.TextField(
        blank=True,
        help_text="Resources, files, and access credentials"
    )
    notes = models.TextField(
        blank=True,
        help_text="Additional notes and instructions"
    )

    # Completion confirmation
    from_user_confirmation = models.BooleanField(default=False)
    to_user_confirmation = models.BooleanField(default=False)
    supervisor_confirmation = models.BooleanField(default=False)

    # Audit trail
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'handover_documentation'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['from_user', '-created_at']),
            models.Index(fields=['to_user', '-created_at']),
            models.Index(fields=['deadline']),
        ]

    def __str__(self):
        return f"Handover: {self.title} ({self.from_user.username} → {self.to_user.username})"

    def is_overdue(self):
        """Check if handover is overdue"""
        from django.utils import timezone
        if self.deadline and self.status in ['PENDING', 'IN_PROGRESS']:
            return timezone.now() > self.deadline
        return False

    def accept(self):
        """Accept the handover"""
        from django.utils import timezone
        self.status = 'IN_PROGRESS'
        self.accepted_at = timezone.now()
        self.save()

    def complete(self):
        """Mark handover as completed"""
        from django.utils import timezone
        self.status = 'COMPLETED'
        self.completed_at = timezone.now()
        self.progress_percentage = 100
        self.save()

    def cancel(self):
        """Cancel the handover"""
        self.status = 'CANCELLED'
        self.save()