"""
Enterprise View Architecture - Master Module
Provides backward compatibility while using new modular structure.
"""

# Core authentication views
from .auth_views import login_view, logout_view, CustomTokenRefreshView, get_current_user

# User management views
from .user_views import *

# Role management views
from .role_views import (
    global_designation_list, get_category_designations, add_designation,
    update_designation, modify_moduleaccess, get_module_access,
    get_user_available_roles, switch_user_role, get_current_active_role
)

# Department management views
from .department_views import (
    get_all_departments, get_all_departments_admin, get_departments_by_programme,
    get_all_departments_with_hierarchy, get_department_tree,
    create_department, update_department, delete_department
)

# Academic data views
from .academic_views import get_all_batches, get_all_programmes

# Emergency access and handover views
from .emergency_views import (
    request_emergency_access, list_emergency_access_requests,
    approve_emergency_access, activate_emergency_access,
    revoke_emergency_access, check_expired_emergency_access,
    list_handover_documents, create_handover_document,
    accept_handover, complete_handover, cancel_handover
)

# Audit and logging views
from .audit_views import get_audit_logs

# Bulk operations views
from .bulk_views import (
    bulk_import_users, bulk_export_users, mail_to_whole_batch,
    download_sample_csv, UserListView
)

__all__ = [
    # Authentication
    'login_view', 'logout_view', 'CustomTokenRefreshView', 'get_current_user',

    # User Management
    'get_user_role_by_username', 'update_user_roles',
    'add_individual_student', 'add_individual_staff', 'add_individual_faculty',
    'reset_password', 'archive_user', 'restore_user',

    # Role Management
    'global_designation_list', 'get_category_designations', 'add_designation',
    'update_designation', 'modify_moduleaccess', 'get_module_access',
    'get_user_available_roles', 'switch_user_role', 'get_current_active_role',

    # Department Management
    'get_all_departments', 'get_all_departments_admin', 'get_departments_by_programme',
    'get_all_departments_with_hierarchy', 'get_department_tree',
    'create_department', 'update_department', 'delete_department',

    # Academic Data
    'get_all_batches', 'get_all_programmes',

    # Emergency Access & Handovers
    'request_emergency_access', 'list_emergency_access_requests',
    'approve_emergency_access', 'activate_emergency_access', 'revoke_emergency_access',
    'check_expired_emergency_access',
    'list_handover_documents', 'create_handover_document',
    'accept_handover', 'complete_handover', 'cancel_handover',

    # Audit & Bulk Operations
    'get_audit_logs',
    'bulk_import_users', 'bulk_export_users', 'mail_to_whole_batch', 'download_sample_csv',
    'UserListView',
]