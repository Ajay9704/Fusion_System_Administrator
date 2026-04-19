"""
Custom permission classes for System Admin module
Implements role-based access control (RBAC)
"""
from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied
from .models import GlobalsHoldsdesignation, GlobalsDesignation


class IsSuperAdmin(permissions.BasePermission):
    """
    Permission check for super admin users only.
    BR-SA-004: Only super admins can access critical system functions
    """
    message = "Super Admin privileges required"

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Check if user has super admin designation
        try:
            super_admin_designation = GlobalsDesignation.objects.get(name='super_admin')
            return GlobalsHoldsdesignation.objects.filter(
                user=request.user,
                designation=super_admin_designation,
                working=request.user
            ).exists()
        except GlobalsDesignation.DoesNotExist:
            # Fallback: check is_superuser flag
            return request.user.is_superuser


class IsAdminUser(permissions.BasePermission):
    """
    Permission check for admin users (super_admin or admin designations)
    UC: All admin use cases require admin privileges
    """
    message = "Admin privileges required"

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Check for admin designations
        admin_designations = GlobalsDesignation.objects.filter(
            name__in=['super_admin', 'admin']
        )
        
        return GlobalsHoldsdesignation.objects.filter(
            user=request.user,
            designation__in=admin_designations,
            working=request.user
        ).exists() or request.user.is_superuser


class CanManageUsers(permissions.BasePermission):
    """
    Permission to manage users (create, update, delete, archive)
    UC-SA-001: Manage User Account
    """
    message = "User management privileges required"

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Super admins and admins with HR module access
        if request.user.is_superuser:
            return True
        
        # Check if user has admin designation
        admin_designations = GlobalsDesignation.objects.filter(
            name__in=['super_admin', 'admin', 'establishment']
        )
        
        return GlobalsHoldsdesignation.objects.filter(
            user=request.user,
            designation__in=admin_designations,
            working=request.user
        ).exists()


class CanManageRoles(permissions.BasePermission):
    """
    Permission to manage roles and permissions
    UC-SA-003: Manage Roles & Permissions
    """
    message = "Role management privileges required"

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        return request.user.is_superuser or GlobalsHoldsdesignation.objects.filter(
            user=request.user,
            designation__name='super_admin',
            working=request.user
        ).exists()


class CanViewAuditLogs(permissions.BasePermission):
    """
    Permission to view audit logs
    UC-SA-005: View System Audit Log
    """
    message = "Audit log viewing privileges required"

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Admin users can view audit logs
        return request.user.is_superuser or GlobalsHoldsdesignation.objects.filter(
            user=request.user,
            designation__name__in=['super_admin', 'admin'],
            working=request.user
        ).exists()


class CanManageDepartments(permissions.BasePermission):
    """
    Permission to manage departments
    UC-SA-007: Manage Department Hierarchy
    """
    message = "Department management privileges required"

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        return request.user.is_superuser or GlobalsHoldsdesignation.objects.filter(
            user=request.user,
            designation__name__in=['super_admin', 'admin', 'academics'],
            working=request.user
        ).exists()


class CanBulkImport(permissions.BasePermission):
    """
    Permission for bulk user import
    UC-SA-006: Bulk Upload Users
    """
    message = "Bulk import privileges required"

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        return request.user.is_superuser or GlobalsHoldsdesignation.objects.filter(
            user=request.user,
            designation__name__in=['super_admin', 'admin', 'establishment'],
            working=request.user
        ).exists()


class CanManageEmergencyAccess(permissions.BasePermission):
    """
    Permission to manage emergency access requests
    UC-SA-022: Emergency Access System
    """
    message = "Emergency access management privileges required"

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Only super admins can approve/deny emergency access
        if request.method in ['PUT', 'PATCH', 'DELETE']:
            return request.user.is_superuser or GlobalsHoldsdesignation.objects.filter(
                user=request.user,
                designation__name='super_admin',
                working=request.user
            ).exists()
        
        # All authenticated users can request emergency access
        return True


class CanManageHandover(permissions.BasePermission):
    """
    Permission to manage handover documentation
    WF-SA-05: Handover Documentation System
    """
    message = "Handover management privileges required"

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Admin users can manage all handovers
        # Regular users can only manage their own handovers
        if request.method in ['GET', 'POST']:
            return True  # All authenticated users can view/create handovers
        
        return request.user.is_superuser or GlobalsHoldsdesignation.objects.filter(
            user=request.user,
            designation__name__in=['super_admin', 'admin'],
            working=request.user
        ).exists()
