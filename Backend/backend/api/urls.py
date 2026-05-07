from django.urls import path
from . import views
from . import update_global_db
from .views import login_view, logout_view, get_current_user, CustomTokenRefreshView, change_password
from . import rbac_views
from . import emergency_access_views

urlpatterns = [
    # Authentication endpoints
    path('auth/login/', login_view, name='login'),
    path('auth/logout/', logout_view, name='logout'),
    path('auth/token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('auth/me/', get_current_user, name='current_user'),
    path('auth/change-password/', change_password, name='change_password'),
    
    # Existing endpoints
    path('departments/', views.get_all_departments ,name='get_all_departments'),
    path('departments/by-programme/', views.get_departments_by_programme, name='get_departments_by_programme'),
    path('batches/', views.get_all_batches ,name='get_all_batches'),
    path('programmes/', views.get_all_programmes ,name='get_all_programmes'),
    path('get-user-roles-by-username/', views.get_user_role_by_username ,name='get_user_role_by_username'),
    path('update-user-roles/', views.update_user_roles ,name='update_user_roles'),
    path('view-roles/', views.global_designation_list ,name='global_designation_list'),
    path('view-designations/', views.get_category_designations ,name='get_category_designations'),
    path('create-role/', views.add_designation ,name='add_designation'),
    path('modify-role/', views.update_designation ,name='update_designation'),
    path('get-module-access/', views.get_module_access, name='get_module_access'),
    path('modify-roleaccess/', views.modify_moduleaccess ,name='modify_moduleaccess'),
    path('users/add-student/', views.add_individual_student, name='add_individual_student'),
    path('users/add-staff/', views.add_individual_staff, name='add_individual_staff'),
    path('users/add-faculty/', views.add_individual_faculty, name='add_individual_faculty'),
    path('users/reset_password/', views.reset_password, name='reset-password'),
    path('users/import/', views.bulk_import_users, name='bulk-import-users'),
    path('users/export/', views.bulk_export_users, name='bulk-export-users'),
    path('users/mail-batch/', views.mail_to_whole_batch, name='mail-to-whole-batch'),
    path('update-globals-db/', update_global_db.update_globals_db, name='update_globals_db'),
    path('download-sample-csv/', views.download_sample_csv, name='download_sample_csv'),
    path("users/", views.UserListView.as_view(), name='user-list'),
    path('audit-logs/', views.get_audit_logs, name='get_audit_logs'),
    path('users/<str:username>/archive/', views.archive_user, name='archive_user'),
    path('users/<str:username>/restore/', views.restore_user, name='restore_user'),

    # ==================== RBAC (Role-Based Access Control) ====================
    path('rbac/roles/', rbac_views.rbac_get_user_roles, name='rbac_get_user_roles'),
    path('rbac/roles/assign/', rbac_views.rbac_assign_role, name='rbac_assign_role'),
    path('rbac/roles/remove/', rbac_views.rbac_remove_role, name='rbac_remove_role'),
    path('rbac/roles/replace/', rbac_views.rbac_replace_roles, name='rbac_replace_roles'),

    path('rbac/users/status/', rbac_views.rbac_get_user_status, name='rbac_get_user_status'),
    path('rbac/users/block/', rbac_views.rbac_block_user, name='rbac_block_user'),
    path('rbac/users/unblock/', rbac_views.rbac_unblock_user, name='rbac_unblock_user'),
    path('rbac/users/blocked/', rbac_views.rbac_list_blocked_users, name='rbac_list_blocked_users'),
    path('rbac/users/check-access/', rbac_views.rbac_check_access, name='rbac_check_access'),

    path('rbac/config/conflicts/', rbac_views.rbac_get_conflicts, name='rbac_get_conflicts'),
    path('rbac/config/eligibility/', rbac_views.rbac_get_eligibility, name='rbac_get_eligibility'),
    path('rbac/config/update/', rbac_views.rbac_update_config, name='rbac_update_config'),
    path('rbac/config/eligibility/manage/', rbac_views.rbac_manage_eligibility, name='rbac_manage_eligibility'),
    path('rbac/config/conflicts/manage/', rbac_views.rbac_manage_conflicts, name='rbac_manage_conflicts'),

    # ==================== Emergency Access (Just-In-Time) ====================
    path('emergency-access/requests/create/', emergency_access_views.create_emergency_access_request, name='emergency_create_request'),
    path('emergency-access/requests/my/', emergency_access_views.get_my_emergency_requests, name='emergency_my_requests'),
    path('emergency-access/requests/all/', emergency_access_views.get_all_emergency_requests, name='emergency_all_requests'),
    path('emergency-access/requests/pending/', emergency_access_views.get_pending_emergency_requests, name='emergency_pending_requests'),
    path('emergency-access/requests/<int:request_id>/', emergency_access_views.get_emergency_request_detail, name='emergency_request_detail'),
    path('emergency-access/requests/<int:request_id>/approve/', emergency_access_views.approve_emergency_request, name='emergency_approve_request'),
    path('emergency-access/requests/<int:request_id>/reject/', emergency_access_views.reject_emergency_request, name='emergency_reject_request'),
    path('emergency-access/requests/<int:request_id>/withdraw/', emergency_access_views.withdraw_emergency_request, name='emergency_withdraw_request'),
    path('emergency-access/expire-roles/', emergency_access_views.check_and_expire_roles, name='emergency_expire_roles'),
    path('emergency-access/my-temporary-roles/', emergency_access_views.get_active_temporary_roles, name='emergency_my_temporary_roles'),
]
