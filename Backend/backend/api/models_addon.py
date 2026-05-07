"""
Additional RBAC Models for proper database storage
"""

from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone


class RoleEligibilityRule(models.Model):
    """
    Defines which user types are eligible for which roles
    Replaces JSON storage with proper relational model
    """
    id = models.AutoField(primary_key=True)
    role_name = models.CharField(max_length=100, unique=True)
    eligible_user_types = models.JSONField(default=list)  # ['student', 'faculty', 'staff']
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'rbac_role_eligibility'
        verbose_name = 'Role Eligibility Rule'
        verbose_name_plural = 'Role Eligibility Rules'

    def __str__(self):
        return f"{self.role_name} -> {self.eligible_user_types}"


class RoleConflictRule(models.Model):
    """
    Defines which roles conflict with each other
    Replaces JSON storage with proper relational model
    """
    id = models.AutoField(primary_key=True)
    role_name = models.CharField(max_length=100, unique=True)
    conflicts_with = models.JSONField(default=list)  # ['dean', 'hod', 'student']
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'rbac_role_conflicts'
        verbose_name = 'Role Conflict Rule'
        verbose_name_plural = 'Role Conflict Rules'

    def __str__(self):
        return f"{self.role_name} conflicts with {self.conflicts_with}"


class RoleEditHistory(models.Model):
    """
    Track changes to roles for audit
    """
    id = models.AutoField(primary_key=True)
    role = models.ForeignKey('GlobalsDesignation', on_delete=models.CASCADE, related_name='edit_history')
    edited_by = models.ForeignKey('AuthUser', on_delete=models.SET_NULL, null=True, related_name='role_edits')
    action = models.CharField(max_length=50)  # 'created', 'updated', 'deleted'
    changes = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'rbac_role_edit_history'
        verbose_name = 'Role Edit History'
        verbose_name_plural = 'Role Edit Histories'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.role.name} - {self.action} by {self.edited_by}"


class EmergencyAccessRequest(models.Model):
    """
    Emergency/Just-In-Time role access requests
    """
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'
        EXPIRED = 'EXPIRED', 'Expired'
        WITHDRAWN = 'WITHDRAWN', 'Withdrawn'

    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(
        'AuthUser',
        on_delete=models.CASCADE,
        related_name='emergency_requests',
        null=False
    )
    role = models.ForeignKey(
        'GlobalsDesignation',
        on_delete=models.CASCADE,
        related_name='emergency_requests',
        null=False
    )
    reason = models.TextField(
        help_text="Reason for requesting emergency access",
        null=False,
        blank=False
    )
    requested_duration = models.PositiveIntegerField(
        help_text="Requested duration in minutes",
        validators=[MinValueValidator(1)],
        null=False
    )
    approved_duration = models.PositiveIntegerField(
        help_text="Approved duration in minutes (may differ from requested)",
        null=True,
        blank=True
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True
    )
    requested_at = models.DateTimeField(auto_now_add=True, db_index=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        'AuthUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_emergency_requests'
    )
    expires_at = models.DateTimeField(null=True, blank=True, db_index=True)
    rejection_reason = models.TextField(blank=True, null=True)
    duration_modified_reason = models.TextField(
        blank=True,
        null=True,
        help_text="Reason if admin modified the approved duration"
    )

    class Meta:
        db_table = 'emergency_access_requests'
        verbose_name = 'Emergency Access Request'
        verbose_name_plural = 'Emergency Access Requests'
        ordering = ['-requested_at']
        indexes = [
            models.Index(fields=['-requested_at']),
            models.Index(fields=['user', '-requested_at']),
            models.Index(fields=['status', '-requested_at']),
            models.Index(fields=['expires_at']),
            models.Index(fields=['role', '-requested_at']),
        ]

    def __str__(self):
        return f"{self.user.username} -> {self.role.name} ({self.status})"

    def is_active(self):
        """Check if this request grants active access"""
        return (
            self.status == self.Status.APPROVED and
            self.expires_at and
            self.expires_at > timezone.now()
        )

    def has_expired(self):
        """Check if this request has expired"""
        return (
            self.status == self.Status.APPROVED and
            self.expires_at and
            self.expires_at <= timezone.now()
        )


class TemporaryRoleAssignment(models.Model):
    """
    Tracks temporary role assignments from emergency access
    """
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(
        'AuthUser',
        on_delete=models.CASCADE,
        related_name='temporary_roles',
        null=False
    )
    role = models.ForeignKey(
        'GlobalsDesignation',
        on_delete=models.CASCADE,
        related_name='temporary_assignments',
        null=False
    )
    request = models.ForeignKey(
        EmergencyAccessRequest,
        on_delete=models.CASCADE,
        related_name='assignments',
        null=False
    )
    granted_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=False, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    revoked_by = models.ForeignKey(
        'AuthUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='revoked_temporary_roles'
    )
    revocation_reason = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'temporary_role_assignments'
        verbose_name = 'Temporary Role Assignment'
        verbose_name_plural = 'Temporary Role Assignments'
        ordering = ['-granted_at']
        unique_together = [['user', 'role', 'request']]
        indexes = [
            models.Index(fields=['-granted_at']),
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['expires_at']),
            models.Index(fields=['is_active', 'expires_at']),
        ]

    def __str__(self):
        return f"{self.user.username} -> {self.role.name} (expires: {self.expires_at})"

    def is_valid(self):
        """Check if this assignment is currently valid"""
        return self.is_active and self.expires_at > timezone.now()

    def revoke(self, revoked_by_user, reason=None):
        """Revoke this temporary role assignment"""
        from django.utils import timezone
        self.is_active = False
        self.revoked_at = timezone.now()
        self.revoked_by = revoked_by_user
        self.revocation_reason = reason
        self.save()


class EmergencyAccessPolicy(models.Model):
    """
    Policy settings for emergency access requests
    """
    id = models.AutoField(primary_key=True)
    role = models.ForeignKey(
        'GlobalsDesignation',
        on_delete=models.CASCADE,
        related_name='emergency_policies',
        null=True,
        blank=True,
        help_text="If set, policy applies only to this role. If null, applies to all roles."
    )
    max_duration_minutes = models.PositiveIntegerField(
        help_text="Maximum allowed duration in minutes",
        default=480,  # 8 hours default
        validators=[MinValueValidator(1)]
    )
    requires_justification = models.BooleanField(
        default=True,
        help_text="If true, users must provide a detailed reason"
    )
    min_justification_length = models.PositiveIntegerField(
        default=10,
        help_text="Minimum characters for justification",
        validators=[MinValueValidator(1)]
    )
    allow_self_approval = models.BooleanField(
        default=False,
        help_text="If false, admins cannot approve their own requests"
    )
    auto_approve_eligible = models.BooleanField(
        default=False,
        help_text="Auto-approve if user meets eligibility criteria"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'AuthUser',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_emergency_policies'
    )

    class Meta:
        db_table = 'emergency_access_policies'
        verbose_name = 'Emergency Access Policy'
        verbose_name_plural = 'Emergency Access Policies'
        indexes = [
            models.Index(fields=['role']),
        ]

    def __str__(self):
        role_name = self.role.name if self.role else "All Roles"
        return f"{role_name} - Max {self.max_duration_minutes} mins"
