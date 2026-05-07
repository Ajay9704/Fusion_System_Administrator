import csv
import datetime
from django.http import HttpResponse
from django.db.models import Max, Q
from django.db.models.functions import Upper
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from .models import GlobalsDesignation, GlobalsHoldsdesignation, GlobalsModuleaccess, AuthUser, Batch, Student, GlobalsDepartmentinfo, Programme, GlobalsFaculty, Staff, AuditLog, Discipline
from .serializers import GlobalExtraInfoSerializer, GlobalsDesignationSerializer, GlobalsModuleaccessSerializer, AuthUserSerializer, GlobalsHoldsDesignationSerializer, StudentSerializer, GlobalsFacultySerializer, GlobalsDepartmentinfoSerializer, BatchSerializer, ProgrammeSerializer, StaffSerializer, ViewStudentsWithFiltersSerializer, ViewStaffWithFiltersSerializer, ViewFacultyWithFiltersSerializer, AuditLogSerializer
from io import StringIO
from .helpers import create_password, send_email, mail_to_user, configure_password_mail, add_user_extra_info, add_user_designation_info, add_student_info, validate_personal_email, convert_to_iso
from django.contrib.auth.hashers import make_password, check_password

from django.conf import settings
from .audit import audit_log, create_audit_log, get_client_ip, log_failed_login, get_user_agent
from .services import UsernameGenerationService
from .error_handlers import (
    ErrorCodes, 
    ErrorMessageBuilder, 
    AuditMessageBuilder, 
    LogMessageBuilder
)


# Role conflict rules definition
# Format: (role_name, [conflicting_role_names])
ROLE_CONFLICT_RULES = {
    'director': ['dean', 'hod'],  # Director cannot also be Dean or HOD
    'dean': ['director', 'hod'],  # Dean cannot also be Director or HOD
    'hod': ['director', 'dean'],  # HOD cannot also be Director or Dean
    # Add more conflict rules as needed
}


def check_role_conflicts(user_id, new_designation_id):
    """
    Check if assigning a new role to a user conflicts with existing roles.
    Returns a list of conflicting role names, or empty list if no conflicts.
    """
    try:
        new_designation = GlobalsDesignation.objects.get(id=new_designation_id)
        user_roles = GlobalsHoldsdesignation.objects.filter(user_id=user_id).select_related('designation')
        
        existing_role_names = [entry.designation.name for entry in user_roles]
        conflicting_roles = []
        
        # Check if new role conflicts with any existing role
        if new_designation.name in ROLE_CONFLICT_RULES:
            for conflicting_role in ROLE_CONFLICT_RULES[new_designation.name]:
                if conflicting_role in existing_role_names:
                    conflicting_roles.append(conflicting_role)
        
        # Check if any existing role conflicts with the new role
        for existing_role in existing_role_names:
            if existing_role in ROLE_CONFLICT_RULES:
                if new_designation.name in ROLE_CONFLICT_RULES[existing_role]:
                    if new_designation.name not in conflicting_roles:
                        conflicting_roles.append(new_designation.name)
        
        return conflicting_roles
    except GlobalsDesignation.DoesNotExist:
        return []


@api_view(['GET'])
def get_all_departments(request):
    """
    Get all departments. 
    Use ?academic_only=true to exclude administrative departments.
    """
    academic_only = request.GET.get('academic_only', 'false').lower() == 'true'
    
    if academic_only:
        # List of administrative/non-academic departments to exclude
        EXCLUDED_DEPARTMENTS = [
            'Security', 'Central Mess', 'Register Office', 'Registrar', 'Registrar Office',
            'Administration', 'HR', 'Finance', 'Accounts', 'Finance and Accounts',
            'Medical Center', 'PHC', 'Guest House', 'Workshop',
            'Maintenance', 'Estate Office', 'Purchase Store', 'IWD', 'Purchase and Store',
            'General Administration', 'Directorate', 'Establishment',
            'Computer Center', 'Placement Cell', 'Student Affairs',
            'Office of The Dean R&D', 'Office of The Dean P&D',
            'Establishment & P&S', 'F&A & GA', 'Establishment, RTI and Rajbhasha',
            'Security and Central Mess', 'Academics'
        ]
        records = GlobalsDepartmentinfo.objects.exclude(
            name__in=EXCLUDED_DEPARTMENTS
        ).order_by('id')
    else:
        records = GlobalsDepartmentinfo.objects.all().order_by('id')
    
    serializer = GlobalsDepartmentinfoSerializer(records, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def get_all_batches(request):
    records = Batch.objects.distinct('year')
    serializer = BatchSerializer(records, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def get_departments_by_programme(request):
    """
    Get departments/disciplines available for a specific programme.
    This prevents selecting invalid department-programme combinations.
    Only returns academic departments, excluding administrative units.
    """
    programme = request.GET.get('programme')
    if not programme:
        return Response(
            ErrorMessageBuilder.validation_error(
                ErrorCodes.VAL_MISSING_REQUIRED_FIELD,
                "Programme parameter is required to fetch departments.",
                field="programme",
                solution="Please provide a programme name (e.g., 'B.Tech', 'M.Tech', 'PhD') in the query parameters."
            ),
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # List of administrative/non-academic departments to exclude
    EXCLUDED_DEPARTMENTS = [
        'Security', 'Central Mess', 'Register Office', 'Registrar', 'Registrar Office',
        'Administration', 'HR', 'Finance', 'Accounts', 'Finance and Accounts',
        'Medical Center', 'PHC', 'Guest House', 'Workshop',
        'Maintenance', 'Estate Office', 'Purchase Store', 'IWD', 'Purchase and Store',
        'General Administration', 'Directorate', 'Establishment',
        'Computer Center', 'Placement Cell', 'Student Affairs',
        'Office of The Dean R&D', 'Office of The Dean P&D',
        'Establishment & P&S', 'F&A & GA', 'Establishment, RTI and Rajbhasha',
        'Security and Central Mess', 'Academics'
    ]
    
    try:
        # Log the incoming programme request
        print(LogMessageBuilder.info(
            "DEPARTMENTS",
            f"Fetching departments for programme: '{programme}'"
        ))
        
        # Get the programme object - try exact match first
        programme_obj = Programme.objects.filter(name=programme).first()

        # If no exact match, try partial match (case-insensitive)
        if not programme_obj:
            programme_obj = Programme.objects.filter(name__icontains=programme).first()

        # If still no match, log warning and return all academic departments
        if not programme_obj:
            print(LogMessageBuilder.warning(
                "DEPARTMENTS",
                f"Programme '{programme}' not found in database. Returning all academic departments.",
                action_required="Verify programme name or add it to the database."
            ))
            departments = GlobalsDepartmentinfo.objects.exclude(
                name__in=EXCLUDED_DEPARTMENTS
            ).distinct().order_by('name')
            serializer = GlobalsDepartmentinfoSerializer(departments, many=True)
            print(LogMessageBuilder.info(
                "DEPARTMENTS",
                f"Returning {departments.count()} academic departments (fallback)"
            ))
            return Response(serializer.data)

        print(LogMessageBuilder.info(
            "DEPARTMENTS",
            f"Found programme: '{programme_obj.name}' (ID: {programme_obj.id})"
        ))

        # Get all disciplines that offer this programme
        disciplines = Discipline.objects.filter(programmes=programme_obj)
        
        print(LogMessageBuilder.info(
            "DEPARTMENTS",
            f"Found {disciplines.count()} disciplines for programme '{programme}'"
        ))
        
        # If no disciplines found for this programme, return all ACADEMIC departments as fallback
        if not disciplines.exists():
            print(LogMessageBuilder.warning(
                "DEPARTMENTS",
                f"No disciplines found for programme '{programme}'. Using all academic departments as fallback.",
                action_required="Consider adding disciplines to this programme in the database."
            ))
            departments = GlobalsDepartmentinfo.objects.exclude(
                name__in=EXCLUDED_DEPARTMENTS
            ).distinct().order_by('name')
            serializer = GlobalsDepartmentinfoSerializer(departments, many=True)
            print(LogMessageBuilder.info(
                "DEPARTMENTS",
                f"Returning {departments.count()} academic departments (fallback - no disciplines)"
            ))
            return Response(serializer.data)
        
        # Get departments that match these disciplines
        department_names = [disc.name for disc in disciplines]
        print(LogMessageBuilder.info(
            "DEPARTMENTS",
            f"Discipline names: {department_names}"
        ))
        
        # Find departments that match discipline names (automatically excludes admin depts)
        departments = GlobalsDepartmentinfo.objects.filter(
            name__in=department_names
        ).exclude(
            name__in=EXCLUDED_DEPARTMENTS
        ).distinct()
        
        print(LogMessageBuilder.info(
            "DEPARTMENTS",
            f"Found {departments.count()} matching departments"
        ))
        
        # If no matching departments found, return all academic departments as fallback
        if not departments.exists():
            print(LogMessageBuilder.warning(
                "DEPARTMENTS",
                f"No matching departments found for disciplines: {department_names}. Using all academic departments.",
                action_required="Verify discipline names match department names in database."
            ))
            departments = GlobalsDepartmentinfo.objects.exclude(
                name__in=EXCLUDED_DEPARTMENTS
            ).distinct().order_by('name')

        serializer = GlobalsDepartmentinfoSerializer(departments, many=True)
        print(LogMessageBuilder.info(
            "DEPARTMENTS",
            f"Returning {departments.count()} departments for programme '{programme}'"
        ))
        return Response(serializer.data)
    except Programme.DoesNotExist:
        return Response(
            ErrorMessageBuilder.database_error(
                ErrorCodes.DB_RECORD_NOT_FOUND,
                f"Programme '{programme}' does not exist in the system.",
                solution="Check the programme name or add it to the database if this is a new programme."
            ),
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            ErrorMessageBuilder.system_error(
                ErrorCodes.SYS_INTERNAL_ERROR,
                f"Unexpected error while fetching departments for programme '{programme}'.",
                solution="Check server logs for detailed error information."
            ),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
def get_all_programmes(request):
    records = Programme.objects.all().order_by('id')
    serializer = ProgrammeSerializer(records, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def get_user_role_by_username(request):
    username = request.query_params.get('username')

    if not username:
        return Response(
            ErrorMessageBuilder.validation_error(
                ErrorCodes.VAL_MISSING_REQUIRED_FIELD,
                "Username parameter is required to fetch user roles.",
                field="username",
                solution="Please provide a username in the query parameters."
            ),
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        from django.utils import timezone
        from .models import TemporaryRoleAssignment
        from .services import EmergencyAccessService
        
        # Auto-expire any expired temporary roles before fetching
        EmergencyAccessService.check_and_expire_roles()

        user = AuthUser.objects.get(username__iexact=username)
        holds_designation_entries = GlobalsHoldsdesignation.objects.filter(user=user)

        # Get permanent roles
        designation_ids = [entry.designation_id for entry in holds_designation_entries]
        roles = GlobalsDesignation.objects.filter(id__in=designation_ids)

        # Get active temporary roles (not expired) using TemporaryRoleAssignment
        now = timezone.now()
        active_temporary_assignments = TemporaryRoleAssignment.objects.filter(
            user=user,
            is_active=True,
            expires_at__gt=now
        ).select_related('role')

        # Build response roles list with role type information
        roles_data = []
        
        # Add permanent roles
        for role in roles:
            roles_data.append({
                'id': role.id,
                'name': role.name,
                'full_name': role.full_name,
                'category': role.category,
                'basic': role.basic,
                'is_singular': role.is_singular,
                'role_type': 'permanent',
                'is_emergency': False,
                'permanent_tag': 'PERMANENT',
                'display_label': role.name,
                'access_type': 'Permanent Role Assignment',
            })
        
        # Add active temporary roles
        for temp_assignment in active_temporary_assignments:
            time_remaining = temp_assignment.expires_at - now
            hours_remaining = int(time_remaining.total_seconds() // 3600)
            minutes_remaining = int((time_remaining.total_seconds() % 3600) // 60)
            
            if hours_remaining > 0:
                time_remaining_str = f"{hours_remaining}h {minutes_remaining}m"
            else:
                time_remaining_str = f"{minutes_remaining} minutes"
            
            # Check if this role is already in permanent roles
            is_duplicate = any(r['id'] == temp_assignment.role.id for r in roles_data)
            
            if not is_duplicate:
                roles_data.append({
                    'id': f"temp_{temp_assignment.id}",
                    'name': temp_assignment.role.name,
                    'full_name': temp_assignment.role.full_name,
                    'category': temp_assignment.role.category,
                    'basic': temp_assignment.role.basic,
                    'is_singular': temp_assignment.role.is_singular,
                    'role_type': 'temporary',
                    'is_emergency': True,
                    'temporary_tag': 'EMERGENCY ACCESS',
                    'display_label': f'{temp_assignment.role.name} (Emergency)',
                    'access_type': 'Temporary Emergency Access',
                    'expires_at': temp_assignment.expires_at.isoformat(),
                    'time_remaining': time_remaining_str,
                    'time_remaining_minutes': int(time_remaining.total_seconds() // 60),
                    'approved_duration_minutes': temp_assignment.request.approved_duration if temp_assignment.request.approved_duration else 60,
                    'assignment_id': temp_assignment.id,
                })

        if not roles_data:
            # Return user with empty roles instead of 404 - allows admin to assign first role
            return Response({
                "user": AuthUserSerializer(user).data,
                "roles": [],
            }, status=status.HTTP_200_OK)

        return Response({
            "user": AuthUserSerializer(user).data,
            "roles": roles_data,
        }, status=status.HTTP_200_OK)
        
    except AuthUser.DoesNotExist:
        return Response(
            ErrorMessageBuilder.database_error(
                ErrorCodes.DB_RECORD_NOT_FOUND,
                f"User '{username}' does not exist in the system.",
                solution="Verify the username or create the user if needed."
            ),
            status=status.HTTP_404_NOT_FOUND
        )

    except Exception as e:
        return Response(
            ErrorMessageBuilder.system_error(
                ErrorCodes.SYS_INTERNAL_ERROR,
                f"Unexpected error while fetching roles for user '{username}'.",
                solution="Check server logs for detailed error information."
            ),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
@audit_log(action='UPDATE_USER_ROLES', model_name='GlobalsHoldsdesignation')
def update_user_roles(request):
    username = request.data.get('username')
    roles_to_add = request.data.get('roles')

    if not username or not roles_to_add:
        return Response(
            ErrorMessageBuilder.validation_error(
                ErrorCodes.VAL_MISSING_REQUIRED_FIELD,
                "Username and roles are required to update user roles.",
                solution="Please provide both 'username' and 'roles' fields in the request body."
            ),
            status=status.HTTP_400_BAD_REQUEST
        )

    user = get_object_or_404(AuthUser, username__iexact=username)

    existing_roles = GlobalsHoldsdesignation.objects.filter(user=user)
    existing_role_names = set(existing_roles.values_list('designation__name', flat=True))

    processed_roles_to_add = set()

    for role in roles_to_add:
        if isinstance(role, dict):
            if 'name' in role:
                processed_roles_to_add.add(role['name'])
        elif isinstance(role, str):
            processed_roles_to_add.add(role)

    print(LogMessageBuilder.info("USER_ROLES", f"Processing role update for user '{username}'. Roles to add: {processed_roles_to_add}"))

    # Validate roles before assignment
    for role_name in processed_roles_to_add:
        if role_name not in existing_role_names:
            try:
                designation = GlobalsDesignation.objects.get(name=role_name)
                
                # Check singular role constraint
                if designation.is_singular:
                    other_users_with_role = GlobalsHoldsdesignation.objects.filter(
                        designation=designation
                    ).exclude(user=user)
                    
                    if other_users_with_role.exists():
                        other_user = other_users_with_role.first().user
                        return Response({
                            "error": f"Role '{role_name}' is a singular role and can only be assigned to one user at a time.",
                            "current_holder": other_user.username
                        }, status=status.HTTP_409_CONFLICT)
                
                # Check role conflicts
                conflicts = check_role_conflicts(user.id, designation.id)
                if conflicts:
                    return Response({
                        "error": f"Role '{role_name}' conflicts with existing roles: {', '.join(conflicts)}",
                        "conflicting_roles": conflicts
                    }, status=status.HTTP_409_CONFLICT)
                    
            except GlobalsDesignation.DoesNotExist:
                return Response(
                    ErrorMessageBuilder.database_error(
                        ErrorCodes.DB_RECORD_NOT_FOUND,
                        f"Role '{role_name}' does not exist in the system.",
                        solution="Verify the role name or create it if needed."
                    ),
                    status=status.HTTP_404_NOT_FOUND
                )

    roles_to_remove = existing_role_names - processed_roles_to_add

    GlobalsHoldsdesignation.objects.filter(user=user, designation__name__in=roles_to_remove).delete()

    for role_name in processed_roles_to_add:
        if role_name not in existing_role_names:
            designation = get_object_or_404(GlobalsDesignation, name=role_name)
            
            # Get optional start_date and end_date from request
            start_date = request.data.get('start_date')
            end_date = request.data.get('end_date')
            
            # Validate dates
            if start_date and end_date:
                from datetime import datetime
                start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
                end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()
                
                if end_dt <= start_dt:
                    return Response({
                        "error": "End date must be after start date."
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            GlobalsHoldsdesignation.objects.create(
                held_at=timezone.now(),
                designation=designation,
                user=user,
                working=user,
                start_date=start_date if start_date else None,
                end_date=end_date if end_date else None
            )

    return Response({"message": "User roles updated successfully."}, status=status.HTTP_200_OK)
        
@api_view(['GET'])
def global_designation_list(request):
    records = GlobalsDesignation.objects.all()
    serializer = GlobalsDesignationSerializer(records, many=True)
    return Response(serializer.data)

@api_view(['POST'])
def get_category_designations(request):
    category = request.data.get('category', 'student')
    basic = request.data.get('basic', True)
    records = GlobalsDesignation.objects.all().filter(category=category, basic=basic)
    serializer = GlobalsDesignationSerializer(records, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@audit_log(action='CREATE_ROLE', model_name='GlobalsDesignation')
def add_designation(request):
    try:
        serializer = GlobalsDesignationSerializer(data=request.data)
        if serializer.is_valid():
            role = serializer.save()
            max_id = GlobalsModuleaccess.objects.aggregate(Max('id'))['id__max']
            new_id = (max_id or 0) + 1
        data = {
            'id': new_id,
            'designation' : role.name,
            'program_and_curriculum' : False,
            'course_registration' : False,
            'course_management' : False,
            'other_academics' : False,
            'spacs' : False,
            'department' : False,
            'examinations' : False,
            'hr' : False,
            'iwd' : False,
            'complaint_management' : False,
            'fts' : False,
            'purchase_and_store' : False,
            'rspc' : False,
            'hostel_management' : False,
            'mess_management' : False,
            'gymkhana' : False,
            'placement_cell' : False,
            'visitor_hostel' : False,
            'phc' : False,
            'inventory_management': False,
        }
        module_serializer = GlobalsModuleaccessSerializer(data=data)
        if module_serializer.is_valid():
            module_serializer.save()
            return Response({'role': serializer.data, 'modules': module_serializer.data}, status.HTTP_201_CREATED)
        else:
            # If module creation fails, delete the created role
            role.delete()
            return Response({'role': serializer.data, 'modules': module_serializer.errors}, status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response(
            ErrorMessageBuilder.server_error(
                str(e),
                "Failed to create role"
            ),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
@audit_log(action='UPDATE_ROLE', model_name='GlobalsDesignation')
def update_designation(request):
    name = request.data.get('name')
    
    if not name:
        return Response(
            ErrorMessageBuilder.validation_error(
                ErrorCodes.VAL_MISSING_REQUIRED_FIELD,
                "Designation name is required to update role.",
                field="name",
                solution="Please provide the 'name' field in the request body."
            ),
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        designation = GlobalsDesignation.objects.get(name=name)
    except GlobalsDesignation.DoesNotExist:
        return Response(
            ErrorMessageBuilder.database_error(
                ErrorCodes.DB_RECORD_NOT_FOUND,
                f"Designation '{name}' not found in the system.",
                solution="Verify the designation name or create it if needed."
            ),
            status=status.HTTP_404_NOT_FOUND
        )
    
    partial = request.method == 'PATCH'
    serializer = GlobalsDesignationSerializer(designation, data=request.data, partial=partial)
    
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@audit_log(action='RESET_PASSWORD', model_name='AuthUser')
def reset_password(request):
    user_name = request.data.get('username')
    try:
        user = AuthUser.objects.annotate(username_upper=Upper('username')).get(username_upper=user_name.upper())
        
        # Generate a new password
        new_password = create_password(request.data)
        
        # Hash the password before saving to database
        user.password = make_password(new_password)
        user.save()
        
        try:
            subject = 'Your Password has been reset!!'
            message = f"This Mail is to notify you that your password has been reset by the System Administrator.\n\nPlease check out the new password below:  {new_password}\n\nRegards,\nSystem Administrator,\nIIITDM Jabalpur."
            recipient_list = [f"{user.email}" if settings.EMAIL_TEST_MODE == 0 else settings.EMAIL_TEST_USER]
            send_email(subject=subject, message=message, recipient_list=recipient_list)
        except Exception as email_error:
            print(LogMessageBuilder.error(
                "PASSWORD_RESET",
                f"Failed to send password reset email to user '{user_name}'",
                email_error
            ))
        finally:
            return Response({
                "password": new_password,
                "message": "Password reset successfully."
            }, status=status.HTTP_200_OK)
    except AuthUser.DoesNotExist:
        return Response(
            ErrorMessageBuilder.database_error(
                ErrorCodes.DB_RECORD_NOT_FOUND,
                f"User '{user_name}' does not exist in the system.",
                solution="Verify the username or create the user if needed."
            ),
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            ErrorMessageBuilder.system_error(
                ErrorCodes.SYS_INTERNAL_ERROR,
                f"Unexpected error while resetting password for user '{user_name}'.",
                solution="Check server logs for detailed error information."
            ),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
def get_module_access(request):
    role_name = request.query_params.get('designation')

    if not role_name:
        return Response(
            ErrorMessageBuilder.validation_error(
                ErrorCodes.VAL_MISSING_REQUIRED_FIELD,
                "Role designation name is required to fetch module access permissions.",
                field="designation",
                solution="Please provide a role designation name in the query parameters."
            ),
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        module_access = GlobalsModuleaccess.objects.get(designation=role_name)
    except GlobalsModuleaccess.DoesNotExist:
        return Response(
            ErrorMessageBuilder.database_error(
                ErrorCodes.DB_RECORD_NOT_FOUND,
                f"Module access configuration for designation '{role_name}' not found.",
                solution="Create module access configuration for this role designation."
            ),
            status=status.HTTP_404_NOT_FOUND
        )
    
    serializer = GlobalsModuleaccessSerializer(module_access)
    return Response(serializer.data, status=status.HTTP_200_OK)
    
@api_view(['PUT'])
@audit_log(action='MODIFY_MODULE_ACCESS', model_name='GlobalsModuleaccess')
def modify_moduleaccess(request):
    role_name = request.data.get('designation')
    
    if not role_name:
        return Response({"error": "No role provided."}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        designation = GlobalsModuleaccess.objects.get(designation=role_name)
    except GlobalsModuleaccess.DoesNotExist:
        return Response({"error": f"Designation with name '{role_name}' not found."}, status=status.HTTP_404_NOT_FOUND)

    serializer = GlobalsModuleaccessSerializer(designation, data=request.data, partial=True)
    
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@audit_log(action='CREATE_STUDENT', model_name='AuthUser')
def add_individual_student(request):
    """
    Create individual student with auto-generated username and personal email.
    Username (roll number) is auto-generated if not provided.
    Credentials are sent to personal email.
    """
    # Personal email is required
    personal_email = request.data.get('personal_email')
    if not personal_email:
        return Response({
            "error": "Personal email is required for credential delivery"
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Validate personal email
    is_valid, message = validate_personal_email(personal_email)
    if not is_valid:
        return Response({"error": message}, status=status.HTTP_400_BAD_REQUEST)
    
    # Required fields (username is now optional)
    required_fields = ["first_name", "last_name", "sex", "category", "father_name", "mother_name", "batch", "programme"]
    data = request.data
    missing_fields = [field for field in required_fields if field not in data or not data[field]]
    if missing_fields:
        return Response({
            "error": "Missing required fields.",
            "missing_fields": missing_fields
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Get department and discipline
    default_department = GlobalsDepartmentinfo.objects.get(name='CSE')
    department_id = data.get("department")
    
    # Validate department is provided
    if not department_id:
        return Response({
            "error": "Department is required.",
            "message": "Please select a valid department/discipline for the student."
        }, status=status.HTTP_400_BAD_REQUEST)
    
    department = GlobalsDepartmentinfo.objects.filter(id=department_id).first()
    if not department:
        return Response({
            "error": f"Department with ID {department_id} not found.",
            "message": "Please select a valid department from the available options."
        }, status=status.HTTP_400_BAD_REQUEST)
    
    print(LogMessageBuilder.info(
        "STUDENT_CREATION",
        f"Creating student with department: {department.name} (ID: {department.id})"
    ))
    
    # Auto-generate username if not provided
    username = data.get('username')
    if not username:
        try:
            # Get discipline acronym from Batch table
            batch_record = Batch.objects.filter(
                name=data.get('programme'),
                discipline__name__icontains=department.name,
                year=data.get('batch')
            ).first()
            
            discipline_acronym = batch_record.discipline.acronym if batch_record else department.name[:2].upper()
            
            username = UsernameGenerationService.generate_student_username(
                batch_year=data.get('batch'),
                programme=data.get('programme'),
                discipline_acronym=discipline_acronym
            )
        except Exception as e:
            return Response({
                "error": f"Failed to generate username: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        # Validate username uniqueness if provided
        if AuthUser.objects.filter(username__iexact=username.upper()).exists():
            return Response({
                "error": f"Username '{username}' already exists"
            }, status=status.HTTP_409_CONFLICT)
        username = username.upper()
    
    # Generate password and college email
    user_password = create_password({'username': username})
    college_email = UsernameGenerationService.generate_college_email(username)
    
    # Create AuthUser
    auth_user_data = {
        "password": make_password(user_password),
        "username": username,
        "first_name": data['first_name'],
        "last_name": data.get('last_name', ""),
        "email": college_email,
        "is_staff": False,
        "is_superuser": False,
        "is_active": True,
        "date_joined": datetime.datetime.now().strftime("%Y-%m-%d"),
    }
    auth_serializer = AuthUserSerializer(data=auth_user_data)
    if not auth_serializer.is_valid():
        print(LogMessageBuilder.error("STUDENT_CREATION", "Failed to create AuthUser record", auth_serializer.errors))
        return Response(
            ErrorMessageBuilder.validation_error(
                ErrorCodes.VAL_INVALID_DATA_FORMAT,
                "Failed to create student authentication record.",
                solution=f"Validation errors: {auth_serializer.errors}"
            ),
            status=status.HTTP_400_BAD_REQUEST
        )
    user = auth_serializer.save()
    print(LogMessageBuilder.success("STUDENT_CREATION", f"AuthUser record created for student: {username}"))

    # Create ExtraInfo
    extra_info_data = {
        'id': username,
        'title': data.get('title') if data.get('title') else 'Mr.' if data['sex'][0].upper() == 'M' else 'Ms.',
        'sex': data['sex'][0].upper(),
        'date_of_birth': data.get("dob") if data.get("dob") else "2025-01-01",
        'user_status': "PRESENT",
        'address': data.get("address") if data.get("address") else "NA",
        'phone_no': data.get("phone") if data.get("phone") else 9999999999,
        'about_me': "NA",
        'user_type': 'student',
        'profile_picture': None,
        'date_modified': datetime.datetime.now().strftime("%Y-%m-%d"),
        'department': department.id,
        'user': user.id,
    }
    extra_info_serializer = GlobalExtraInfoSerializer(data=extra_info_data)
    if not extra_info_serializer.is_valid():
        print(LogMessageBuilder.error("STUDENT_CREATION", "Failed to create ExtraInfo record", extra_info_serializer.errors))
        return Response(
            ErrorMessageBuilder.validation_error(
                ErrorCodes.VAL_INVALID_DATA_FORMAT,
                "Failed to create student extra information.",
                solution=f"Validation errors: {extra_info_serializer.errors}"
            ),
            status=status.HTTP_400_BAD_REQUEST
        )
    extra_info = extra_info_serializer.save()
    print(LogMessageBuilder.success("STUDENT_CREATION", f"ExtraInfo record created for student: {username}"))

    # Assign student designation
    designation_id = GlobalsDesignation.objects.get(name='student').id
    holds_designation_data = {
        'designation': designation_id,
        'user': user.id,
        'working': user.id,
    }
    holds_designation_serializer = GlobalsHoldsDesignationSerializer(data=holds_designation_data)
    if not holds_designation_serializer.is_valid():
        print(LogMessageBuilder.error("STUDENT_CREATION", "Failed to assign student designation", holds_designation_serializer.errors))
        return Response(
            ErrorMessageBuilder.validation_error(
                ErrorCodes.VAL_INVALID_DATA_FORMAT,
                "Failed to assign student designation.",
                solution=f"Validation errors: {holds_designation_serializer.errors}"
            ),
            status=status.HTTP_400_BAD_REQUEST
        )
    holds_designation_serializer.save()
    print(LogMessageBuilder.success("STUDENT_CREATION", f"Student designation assigned: {username}"))
    
    # Create student academic record
    batch = Batch.objects.filter(
        name=data.get('programme'), 
        discipline__acronym=department.name, 
        year=data.get('batch')
    ).first()
    
    student_data = {
        'id': extra_info.id,
        'programme': data.get('programme') if data.get('programme') else 'B.Tech',
        'batch': data.get('batch') if data.get('batch') else datetime.datetime.now().year,
        'batch_id': batch.id if batch else None,
        'cpi': 0.0,
        'category': data['category'].upper() if data['category'].upper() else 'GEN',
        'father_name': data.get('father_name') if data.get('father_name') else None,
        'mother_name': data.get('mother_name') if data.get('mother_name') else None,
        'hall_no': data.get('hall_no') if data.get('hall_no') else 3,
        'room_no': None,
        'specialization': None,
        'curr_semester_no': 2*(datetime.datetime.now().year - data.get('batch')) + datetime.datetime.now().month // 7,
    }
    student_data_serializer = StudentSerializer(data=student_data)
    if not student_data_serializer.is_valid():
        print(LogMessageBuilder.error("STUDENT_CREATION", "Failed to create student academic record", student_data_serializer.errors))
        return Response(
            ErrorMessageBuilder.validation_error(
                ErrorCodes.VAL_INVALID_DATA_FORMAT,
                "Failed to create student academic record.",
                solution=f"Validation errors: {student_data_serializer.errors}"
            ),
            status=status.HTTP_400_BAD_REQUEST
        )
    student_data_serializer.save()
    print(LogMessageBuilder.success("STUDENT_CREATION", f"Student academic record created: {username}"))
    
    # Send credentials to personal email
    try:
        from .helpers import mail_to_user_single
        mail_to_user_single({
            'username': username,
            'password': user_password,
            'email': personal_email,
            'college_email': college_email
        }, user_password)
        print(LogMessageBuilder.success("STUDENT_CREATION", f"Credentials email sent to {personal_email}"))
    except Exception as e:
        # Log error but don't fail the creation
        print(LogMessageBuilder.error("STUDENT_CREATION", f"Failed to send credentials email to {personal_email}", e))

    print(LogMessageBuilder.success("STUDENT_CREATION", f"Student '{username}' created successfully with email: {college_email}"))

    response_data = {
        "message": "Student created successfully. Credentials sent to personal email.",
        "username": username,
        "college_email": college_email,
        "personal_email": personal_email,
        "created_users": [auth_serializer.data],
        "skipped_users_count": 0,
    }

    return Response(response_data, status=status.HTTP_201_CREATED)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@audit_log(action='CREATE_STAFF', model_name='AuthUser')
def add_individual_staff(request):
    """
    Create individual staff member.
    Username is optional and will be auto-generated if not provided.
    """
    data = request.data

    # Validate personal email if provided
    personal_email = data.get('personal_email')
    if personal_email:
        is_valid, message = validate_personal_email(personal_email)
        if not is_valid:
            return Response({"error": message}, status=status.HTTP_400_BAD_REQUEST)

    # Required fields (username is now optional)
    required_fields = ["first_name", "last_name", "sex", "designation"]
    missing_fields = [field for field in required_fields if field not in data or not data[field]]
    if missing_fields:
        return Response({
            "error": "Missing required fields.",
            "missing_fields": missing_fields
        }, status=status.HTTP_400_BAD_REQUEST)

    # Auto-generate username if not provided
    username = data.get('username')
    if not username:
        import random
        import string
        first_initial = data['first_name'][0].lower()
        last_name_lower = data['last_name'].lower().replace(' ', '')
        random_suffix = ''.join(random.choices(string.digits, k=3))
        username = f"{first_initial}{last_name_lower}{random_suffix}"

        # Ensure uniqueness
        while AuthUser.objects.filter(username__iexact=username).exists():
            random_suffix = ''.join(random.choices(string.digits, k=3))
            username = f"{first_initial}{last_name_lower}{random_suffix}"
    else:
        # Validate username uniqueness if provided
        if AuthUser.objects.filter(username__iexact=username).exists():
            return Response({
                "error": f"Username '{username}' already exists"
            }, status=status.HTTP_409_CONFLICT)
        username = username.lower()

    user_password = create_password({**data, 'username': username})
    auth_user_data = {
        "password": make_password(user_password),
        "username": username,
        "first_name": data['first_name'].lower().capitalize(),
        "last_name": data.get('last_name').lower().capitalize(),
        "email": f"{username}@iiitdmj.ac.in",
        "is_staff": True,
        "is_superuser": False,
        "is_active": True,
        "date_joined": datetime.datetime.now().strftime("%Y-%m-%d"),
    }
    auth_serializer = AuthUserSerializer(data=auth_user_data)
    user = None
    if auth_serializer.is_valid():
        user = auth_serializer.save()
        print(LogMessageBuilder.success("STAFF_CREATION", f"AuthUser record created for staff: {username}"))
    else:
        print(LogMessageBuilder.error("STAFF_CREATION", "Failed to create AuthUser record", auth_serializer.errors))
        return Response(
            ErrorMessageBuilder.validation_error(
                ErrorCodes.VAL_INVALID_DATA_FORMAT,
                "Failed to create staff authentication record.",
                solution=f"Validation errors: {auth_serializer.errors}"
            ),
            status=status.HTTP_400_BAD_REQUEST
        )

    default_department = GlobalsDepartmentinfo.objects.get(name='CSE').id
    extra_info_data = {
        'id': username,
        'title': data.get('title') if data.get('title') else 'Mr.' if data['sex'][0].upper() == 'M' else 'Ms.',
        'sex': data['sex'][0].upper(),
        'date_of_birth': data.get("dob") if data.get("dob") else "2025-01-01",
        'user_status': "PRESENT",
        'address': data.get("address") if data.get("address") else "NA",
        'phone_no': data.get("phone") if data.get("phone") else 9999999999,
        'about_me': "NA",
        'user_type': 'staff',
        'profile_picture': None,
        'date_modified': datetime.datetime.now().strftime("%Y-%m-%d"),
        'department': data.get("department") if data.get("department") else default_department,
        'user': user.id,
    }
    extra_info_serializer = GlobalExtraInfoSerializer(data=extra_info_data)
    extra_info = None
    if extra_info_serializer.is_valid():
        extra_info = extra_info_serializer.save()
        print(LogMessageBuilder.success("STAFF_CREATION", f"ExtraInfo record created for staff: {username}"))
    else:
        print(LogMessageBuilder.error("STAFF_CREATION", "Failed to create ExtraInfo record", extra_info_serializer.errors))
        return Response(
            ErrorMessageBuilder.validation_error(
                ErrorCodes.VAL_INVALID_DATA_FORMAT,
                "Failed to create staff extra information.",
                solution=f"Validation errors: {extra_info_serializer.errors}"
            ),
            status=status.HTTP_400_BAD_REQUEST
        )

    holds_designation_data = {
        'designation' : data.get('designation'),
        'user' : user.id,
        'working' : user.id,
    }
    holds_designation_serializer = GlobalsHoldsDesignationSerializer(data=holds_designation_data)
    if holds_designation_serializer.is_valid():
        holds_designation_serializer.save()
        print(LogMessageBuilder.success("STAFF_CREATION", f"Designation assigned to staff: {username}"))
    else:
        print(LogMessageBuilder.error("STAFF_CREATION", "Failed to assign designation", holds_designation_serializer.errors))
        return Response(
            ErrorMessageBuilder.validation_error(
                ErrorCodes.VAL_INVALID_DATA_FORMAT,
                "Failed to assign designation to staff.",
                solution=f"Validation errors: {holds_designation_serializer.errors}"
            ),
            status=status.HTTP_400_BAD_REQUEST
        )
    
    staff_id = extra_info.id
    staff_data = {
        'id' : staff_id,
    }

    # CRITICAL FIX: Use StaffSerializer, not FacultySerializer!
    staff_serializer = StaffSerializer(data=staff_data)
    if staff_serializer.is_valid():
        staff_serializer.save()
        print(LogMessageBuilder.success("STAFF_CREATION", f"Staff record created: {username}"))
    else:
        print(LogMessageBuilder.error("STAFF_CREATION", "Failed to create staff record", staff_serializer.errors))
        return Response(
            ErrorMessageBuilder.validation_error(
                ErrorCodes.VAL_INVALID_DATA_FORMAT,
                "Failed to create staff record.",
                solution=f"Validation errors: {staff_serializer.errors}"
            ),
            status=status.HTTP_400_BAD_REQUEST
        )

    print(LogMessageBuilder.success("STAFF_CREATION", f"Staff member '{username}' created successfully with ID: {staff_id}"))

    return Response({
        "message": "Staff added successfully",
        "username": username,
        "college_email": f"{username}@iiitdmj.ac.in",
        "personal_email": personal_email,
        "staff_id": staff_id,
    }, status=status.HTTP_201_CREATED)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@audit_log(action='CREATE_FACULTY', model_name='AuthUser')
def add_individual_faculty(request):
    """
    Create individual faculty member.
    Username is optional and will be auto-generated if not provided.
    Personal email is optional - if provided, credentials will be sent there.
    Department is MANDATORY for faculty.
    """
    data = request.data

    # Validate personal email if provided
    personal_email = data.get('personal_email')
    if personal_email:
        is_valid, message = validate_personal_email(personal_email)
        if not is_valid:
            return Response({"error": message}, status=status.HTTP_400_BAD_REQUEST)

    # Required fields (username is now optional, department is MANDATORY)
    required_fields = ["first_name", "last_name", "sex", "designation", "department"]
    missing_fields = [field for field in required_fields if field not in data or not data[field]]
    if missing_fields:
        return Response(
            ErrorMessageBuilder.validation_error(
                ErrorCodes.VAL_MISSING_REQUIRED_FIELD,
                "Missing required fields for faculty creation.",
                field=",".join(missing_fields),
                solution=f"Faculty must be assigned to a department. Please provide: {', '.join(missing_fields)}."
            ),
            status=status.HTTP_400_BAD_REQUEST
        )

    # Auto-generate username if not provided
    username = data.get('username')
    if not username:
        import random
        import string
        first_initial = data['first_name'][0].lower()
        last_name_lower = data['last_name'].lower().replace(' ', '')
        random_suffix = ''.join(random.choices(string.digits, k=3))
        username = f"{first_initial}{last_name_lower}{random_suffix}"

        # Ensure uniqueness
        while AuthUser.objects.filter(username__iexact=username).exists():
            random_suffix = ''.join(random.choices(string.digits, k=3))
            username = f"{first_initial}{last_name_lower}{random_suffix}"
    else:
        # Validate username uniqueness if provided
        if AuthUser.objects.filter(username__iexact=username).exists():
            return Response({
                "error": f"Username '{username}' already exists"
            }, status=status.HTTP_409_CONFLICT)
        username = username.lower()
    user_password = create_password({**data, 'username': username})
    auth_user_data = {
        "password": make_password(user_password),
        "username": username,
        "first_name": data['first_name'].lower().capitalize(),
        "last_name": data.get('last_name').lower().capitalize(),
        "email": f"{username}@iiitdmj.ac.in",
        "is_staff": False,
        "is_superuser": False,
        "is_active": True,
        "date_joined": datetime.datetime.now().strftime("%Y-%m-%d"),
    }
    auth_serializer = AuthUserSerializer(data=auth_user_data)
    user = None
    if auth_serializer.is_valid():
        user = auth_serializer.save()
    else:
        return Response({
            "message": "Error in adding user to auth user table",
            "data": auth_serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    # Department is mandatory for faculty (validated above)
    department_id = data.get("department")
    if not department_id:
        return Response(
            ErrorMessageBuilder.validation_error(
                ErrorCodes.VAL_MISSING_REQUIRED_FIELD,
                "Department is required for faculty creation.",
                field="department",
                solution="Please select a department for the faculty member."
            ),
            status=status.HTTP_400_BAD_REQUEST
        )

    extra_info_data = {
        'id': username,
        'title': data.get('title') if data.get('title') else 'Mr.' if data['sex'][0].upper() == 'M' else 'Ms.',
        'sex': data['sex'][0].upper(),
        'date_of_birth': data.get("dob") if data.get("dob") else "2025-01-01",
        'user_status': "PRESENT",
        'address': data.get("address") if data.get("address") else "NA",
        'phone_no': data.get("phone") if data.get("phone") else 9999999999,
        'about_me': "NA",
        'user_type': 'faculty',
        'profile_picture': None,
        'date_modified': datetime.datetime.now().strftime("%Y-%m-%d"),
        'department': department_id,
        'user': user.id,
    }
    extra_info_serializer = GlobalExtraInfoSerializer(data=extra_info_data)
    extra_info = None
    if extra_info_serializer.is_valid():
        extra_info = extra_info_serializer.save()
        print(LogMessageBuilder.success("FACULTY_CREATION", f"ExtraInfo record created for faculty: {username}"))
    else:
        print(LogMessageBuilder.error("FACULTY_CREATION", "Failed to create ExtraInfo record", extra_info_serializer.errors))
        return Response(
            ErrorMessageBuilder.validation_error(
                ErrorCodes.VAL_INVALID_DATA_FORMAT,
                "Failed to create faculty extra information.",
                solution=f"Validation errors: {extra_info_serializer.errors}"
            ),
            status=status.HTTP_400_BAD_REQUEST
        )

    holds_designation_data = {
        'designation' : data.get('designation'),
        'user' : user.id,
        'working' : user.id,
    }
    holds_designation_serializer = GlobalsHoldsDesignationSerializer(data=holds_designation_data)
    if holds_designation_serializer.is_valid():
        holds_designation_serializer.save()
        print(LogMessageBuilder.success("FACULTY_CREATION", f"Designation assigned to faculty: {username}"))
    else:
        print(LogMessageBuilder.error("FACULTY_CREATION", "Failed to assign designation", holds_designation_serializer.errors))
        return Response(
            ErrorMessageBuilder.validation_error(
                ErrorCodes.VAL_INVALID_DATA_FORMAT,
                "Failed to assign designation to faculty.",
                solution=f"Validation errors: {holds_designation_serializer.errors}"
            ),
            status=status.HTTP_400_BAD_REQUEST
        )

    faculty_id = extra_info.id
    faculty_data = {
        'id' : faculty_id,
    }

    faculty_serializer = GlobalsFacultySerializer(data=faculty_data)
    if faculty_serializer.is_valid():
        faculty_serializer.save()
        print(LogMessageBuilder.success("FACULTY_CREATION", f"Faculty record created: {username}"))
    else:
        print(LogMessageBuilder.error("FACULTY_CREATION", "Failed to create faculty record", faculty_serializer.errors))
        return Response(
            ErrorMessageBuilder.validation_error(
                ErrorCodes.VAL_INVALID_DATA_FORMAT,
                "Failed to create faculty record.",
                solution=f"Validation errors: {faculty_serializer.errors}"
            ),
            status=status.HTTP_400_BAD_REQUEST
        )

    print(LogMessageBuilder.success("FACULTY_CREATION", f"Faculty member '{username}' created successfully with ID: {faculty_id}"))

    return Response({
        "message": "Faculty added successfully" + (f". Credentials sent to {personal_email}" if personal_email else ""),
        "username": username,
        "college_email": f"{username}@iiitdmj.ac.in",
        "personal_email": personal_email,
        "faculty_id": faculty_id,
    }, status=status.HTTP_201_CREATED)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@audit_log(action='BULK_IMPORT_USERS', model_name='AuthUser')
def bulk_import_users(request):
    """
    Bulk import students from CSV with detailed error reporting.
    CSV Headers: username(optional), first_name, last_name, sex, category, 
                 father_name, mother_name, batch, programme, title, dob, 
                 address, phone_no, department, personal_email(required)
    """
    if 'file' not in request.FILES:
        return Response({"error": "No file provided."}, status=status.HTTP_400_BAD_REQUEST)
    
    file = request.FILES['file']
    if not file.name.endswith('.csv'):
        return Response({"error": "Please upload a valid CSV file."}, status=status.HTTP_400_BAD_REQUEST)

    file_data = file.read().decode('utf-8')
    csv_data = csv.reader(StringIO(file_data))
    
    try:
        headers = next(csv_data)
    except StopIteration:
        return Response({"error": "CSV file is empty."}, status=status.HTTP_400_BAD_REQUEST)
    
    # Find column indices
    try:
        personal_email_idx = headers.index('personal_email')
        username_idx = headers.index('username') if 'username' in headers else -1
        first_name_idx = headers.index('first_name')
        last_name_idx = headers.index('last_name')
        sex_idx = headers.index('sex')
        category_idx = headers.index('category')
        father_name_idx = headers.index('father_name')
        mother_name_idx = headers.index('mother_name')
        batch_idx = headers.index('batch')
        programme_idx = headers.index('programme')
        department_idx = headers.index('department') if 'department' in headers else -1
    except ValueError as e:
        return Response({
            "error": f"Missing required column in CSV: {str(e)}"
        }, status=status.HTTP_400_BAD_REQUEST)
    
    created_users = []
    failed_users = []
    error_summary = {
        'invalid_email': 0,
        'missing_required': 0,
        'duplicate_username': 0,
        'invalid_data': 0,
        'database_error': 0
    }
    
    for row_num, row in enumerate(csv_data, start=2):  # Start from 2 (header is row 1)
        error_reason = ""
        
        try:
            # Skip empty rows
            if not any(field.strip() for field in row):
                continue
            
            # Validate minimum required fields
            if len(row) < max(first_name_idx, last_name_idx, sex_idx, batch_idx, programme_idx) + 1:
                failed_users.append(row + ["Missing required fields"])
                error_summary['missing_required'] += 1
                continue
            
            # Get personal email (required)
            personal_email = row[personal_email_idx].strip() if personal_email_idx < len(row) else ""
            if not personal_email:
                failed_users.append(row + ["Personal email is required"])
                error_summary['invalid_email'] += 1
                continue
            
            # Validate personal email
            is_valid, message = validate_personal_email(personal_email)
            if not is_valid:
                failed_users.append(row + [f"Invalid personal email: {message}"])
                error_summary['invalid_email'] += 1
                continue
            
            # Get or generate username
            username = row[username_idx].strip().upper() if username_idx >= 0 and username_idx < len(row) and row[username_idx].strip() else ""
            
            first_name = row[first_name_idx].strip()
            last_name = row[last_name_idx].strip() if last_name_idx < len(row) else ""
            sex = row[sex_idx].strip()
            category = row[category_idx].strip() if category_idx < len(row) else "GEN"
            father_name = row[father_name_idx].strip() if father_name_idx < len(row) else ""
            mother_name = row[mother_name_idx].strip() if mother_name_idx < len(row) else ""
            batch = row[batch_idx].strip()
            programme = row[programme_idx].strip()
            
            # Validate required fields
            if not first_name or not last_name or not sex or not batch or not programme:
                failed_users.append(row + ["Missing required fields (first_name, last_name, sex, batch, programme)"])
                error_summary['missing_required'] += 1
                continue
            
            # Get department
            department_name = row[department_idx].strip() if department_idx >= 0 and department_idx < len(row) and row[department_idx].strip() else "CSE"
            department = GlobalsDepartmentinfo.objects.filter(name__iexact=department_name).first()
            if not department:
                department = GlobalsDepartmentinfo.objects.filter(name='CSE').first()
            
            # Auto-generate username if not provided
            if not username:
                try:
                    batch_record = Batch.objects.filter(
                        name=programme,
                        discipline__name__icontains=department.name,
                        year=int(batch)
                    ).first()
                    
                    discipline_acronym = batch_record.discipline.acronym if batch_record else department.name[:2].upper()
                    
                    username = UsernameGenerationService.generate_student_username(
                        batch_year=int(batch),
                        programme=programme,
                        discipline_acronym=discipline_acronym
                    )
                except Exception as e:
                    failed_users.append(row + [f"Failed to generate username: {str(e)}"])
                    error_summary['invalid_data'] += 1
                    continue
            else:
                # Check if username already exists
                if AuthUser.objects.filter(username__iexact=username).exists():
                    failed_users.append(row + [f"Username '{username}' already exists"])
                    error_summary['duplicate_username'] += 1
                    continue
            
            # Generate password and college email
            user_password = create_password({'username': username})
            college_email = UsernameGenerationService.generate_college_email(username)
            
            # Create AuthUser
            auth_user_data = {
                'password': make_password(user_password),
                'username': username,
                'first_name': first_name.lower().capitalize(),
                'last_name': last_name.lower().capitalize(),
                'email': college_email,
                'is_staff': False,
                'is_superuser': False,
                'is_active': True,
                'date_joined': datetime.datetime.now().strftime("%Y-%m-%d"),
            }
            serializer = AuthUserSerializer(data=auth_user_data)
            if not serializer.is_valid():
                failed_users.append(row + [f"Invalid user data: {str(serializer.errors)}"])
                error_summary['invalid_data'] += 1
                continue
            
            user = serializer.save()
            
            # Create ExtraInfo
            extra_info_data = {
                'id': username,
                'title': row[9].capitalize() if len(row) > 9 and row[9] else ('Mr.' if sex[0].upper() == 'M' else 'Ms.'),
                'sex': sex[0].upper(),
                'date_of_birth': convert_to_iso(row[10]) if len(row) > 10 and row[10] else "2025-01-01",
                'user_status': "PRESENT",
                'address': row[11].lower().capitalize() if len(row) > 11 and row[11] else 'NA',
                'phone_no': row[12] if len(row) > 12 and row[12] else 9999999999,
                'about_me': 'NA',
                'user_type': 'student',
                'profile_picture': None,
                'date_modified': datetime.datetime.now().strftime("%Y-%m-%d"),
                'department': department.id,
                'user': user.id,
            }
            extra_info_serializer = GlobalExtraInfoSerializer(data=extra_info_data)
            if not extra_info_serializer.is_valid():
                user.delete()  # Rollback
                failed_users.append(row + [f"Extra info error: {str(extra_info_serializer.errors)}"])
                error_summary['database_error'] += 1
                continue
            extra_info = extra_info_serializer.save()
            
            # Assign student designation
            designation_id = GlobalsDesignation.objects.get(name='student').id
            holds_data = {
                'designation': designation_id,
                'user': user.id,
                'working': user.id,
            }
            holds_serializer = GlobalsHoldsDesignationSerializer(data=holds_data)
            if not holds_serializer.is_valid():
                user.delete()  # Rollback
                extra_info.delete()  # Rollback
                failed_users.append(row + [f"Designation error: {str(holds_serializer.errors)}"])
                error_summary['database_error'] += 1
                continue
            holds_serializer.save()
            
            # Create student academic record
            batch_record = Batch.objects.filter(
                name=programme,
                discipline__acronym=department.name,
                year=int(batch)
            ).first()
            
            student_data = {
                'id': extra_info.id,
                'programme': programme,
                'batch': int(batch),
                'batch_id': batch_record.id if batch_record else None,
                'cpi': 0.0,
                'category': category.upper(),
                'father_name': father_name.lower().capitalize() if father_name else 'NA',
                'mother_name': mother_name.lower().capitalize() if mother_name else 'NA',
                'hall_no': 3,
                'room_no': None,
                'specialization': None,
                'curr_semester_no': 2 * (datetime.datetime.now().year - int(batch)) + datetime.datetime.now().month // 7,
            }
            student_serializer = StudentSerializer(data=student_data)
            if not student_serializer.is_valid():
                user.delete()  # Rollback
                extra_info.delete()  # Rollback
                failed_users.append(row + [f"Student record error: {str(student_serializer.errors)}"])
                error_summary['database_error'] += 1
                continue
            student_serializer.save()
            
            # Success
            created_users.append({
                'username': username,
                'email': college_email,
                'personal_email': personal_email,
                'first_name': first_name,
                'last_name': last_name
            })
            
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            failed_users.append(row + [error_msg])
            error_summary['database_error'] += 1
            print(LogMessageBuilder.error("BULK_IMPORT", f"Error processing row {row_num} in CSV file", e))
    
    # Send credentials to created users
    if len(created_users) > 0:
        try:
            for user_data in created_users:
                mail_to_user_single({
                    'username': user_data['username'],
                    'password': "Generated",  # Password already set
                    'email': user_data['personal_email'],
                    'college_email': user_data['email']
                }, "Generated")
        except Exception as e:
            print(LogMessageBuilder.error("BULK_IMPORT", "Failed to send credential emails for imported users", e))
    
    # Build response
    response_data = {
        "message": f"{len(created_users)} student(s) created successfully.",
        "created_count": len(created_users),
        "failed_count": len(failed_users),
        "failure_reasons": error_summary if failed_users else {}
    }
    
    # Generate failed CSV with error reasons
    if failed_users:
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(headers + ['error_reason'])
        
        for failed_user in failed_users:
            writer.writerow(failed_user)
        
        output.seek(0)
        response_data["failed_csv"] = output.getvalue()
    
    return Response(response_data, status=status.HTTP_201_CREATED)

@api_view(['GET'])
def bulk_export_users(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="users_export.csv"'

    writer = csv.writer(response)
    writer.writerow(['username', 'first_name', 'last_name', 'email', 'is_staff', 'is_superuser'])
    users = AuthUser.objects.all()
    
    for user in users:
        writer.writerow([user.username, user.first_name, user.last_name, user.email, user.is_staff, user.is_superuser])
    
    return response

@api_view(['POST'])
def mail_to_whole_batch(request):
    emails = EMAIL_TEST_ARRAY
    email_list = emails.split(',')
    if(len(email_list) != 1):
        students = Student.objects.filter(batch=request.data.get('batch'), id__user__email__in=email_list)
    else:
        students = Student.objects.filter(batch=request.data.get('batch'))
        
    students_data = [student.id.user for student in students]
    try:
        configure_password_mail(students_data)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    return Response({"message": "Mail sent to whole batch successfully."}, status=status.HTTP_200_OK)

def download_sample_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="sample.csv"'

    writer = csv.writer(response)
    writer.writerow([
        "username", "first_name", "last_name", "sex", "category",
        "father_name", "mother_name", "batch", "programme", "title",
        "dob", "address", "phone_no", "department", "personal_email"
    ])
    return response

class UserListView(APIView):
    def get(self, request):
        user_type = request.GET.get('type')
        serializer = None

        if user_type == "student":
            students = Student.objects.select_related('id__user', 'id__department', 'batch_id')
            programme = request.GET.get("programme")
            batch = request.GET.get("batch")
            discipline = request.GET.get("discipline")
            category = request.GET.get("category")
            gender = request.GET.get("gender")

            if programme:
                students = students.filter(programme__iexact=programme)
            if batch:
                students = students.filter(batch=batch)
            if discipline:
                students = students.filter(batch_id__discipline__name__iexact=discipline)
            if category:
                students = students.filter(category__iexact=category)
            if gender:
                students = students.filter(id__sex__iexact=gender)

            serializer = ViewStudentsWithFiltersSerializer(students, many=True)

        elif user_type == "faculty":
            faculty = GlobalsFaculty.objects.select_related('id__user', 'id__department').prefetch_related('id__user__holds_designations__designation')
            designation = request.GET.get("designation")
            gender = request.GET.get("gender")

            if designation:
                faculty = faculty.filter(id__user__holds_designations__designation__name__iexact=designation).distinct()
            if gender:
                faculty = faculty.filter(id__sex__iexact=gender)

            serializer = ViewFacultyWithFiltersSerializer(faculty, many=True)

        elif user_type == "staff":
            staff = Staff.objects.select_related("id__user", "id__department").prefetch_related('id__user__holds_designations__designation')
            designation = request.GET.get("designation")
            gender = request.GET.get("gender")

            if designation:
                staff = staff.filter(id__user__holds_designations__designation__name__iexact=designation).distinct()
            if gender:
                staff = staff.filter(id__sex__iexact=gender)

            serializer = ViewStaffWithFiltersSerializer(staff, many=True)

        else:
            return Response(
                ErrorMessageBuilder.validation_error(
                    ErrorCodes.VAL_INVALID_DATA_FORMAT,
                    "Invalid or missing user type parameter.",
                    field="type",
                    solution="Please provide a valid user type: 'student', 'faculty', or 'staff'."
                ),
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@audit_log(action='ARCHIVE_USER', model_name='AuthUser')
def archive_user(request, username):
    """
    Archive a user account (deactivate account).
    Note: Since this uses an existing database table, we use is_active flag.
    """
    try:
        user = get_object_or_404(AuthUser, username=username)

        # Check if user is already archived (inactive)
        if not user.is_active:
            return Response({
                "error": "User is already archived (inactive)"
            }, status=status.HTTP_400_BAD_REQUEST)

        # Check 30-day minimum period
        if user.date_joined:
            days_since_joined = (timezone.now() - user.date_joined).days
            if days_since_joined < 30:
                return Response({
                    "error": f"User must be at least 30 days old to archive. Current age: {days_since_joined} days"
                }, status=status.HTTP_400_BAD_REQUEST)

        # Archive the user (deactivate)
        user.is_active = False
        user.save()

        create_audit_log(
            user=request.user,
            action='ARCHIVE_USER',
            model_name='AuthUser',
            object_id=str(user.id),
            description=f"User {user.username} archived (deactivated) by {request.user.username}",
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
            status='SUCCESS'
        )

        return Response({
            "message": f"User {user.username} archived successfully"
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            "error": f"Failed to archive user: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@audit_log(action='RESTORE_USER', model_name='AuthUser')
def restore_user(request, username):
    """
    Restore an archived user account (reactivate account).
    """
    try:
        user = get_object_or_404(AuthUser, username=username)

        # Check if user is active (not archived)
        if user.is_active:
            return Response({
                "error": "User is not archived (already active)"
            }, status=status.HTTP_400_BAD_REQUEST)

        # Restore the user (activate)
        user.is_active = True
        user.save()

        create_audit_log(
            user=request.user,
            action='RESTORE_USER',
            model_name='AuthUser',
            object_id=str(user.id),
            description=f"User {user.username} restored (reactivated) by {request.user.username}",
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
            status='SUCCESS'
        )

        return Response({
            "message": f"User {user.username} restored successfully"
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            "error": f"Failed to restore user: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_audit_logs(request):
    """
    Retrieve audit logs with filtering support.
    Query params:
    - start_date: Filter logs from this date (YYYY-MM-DD)
    - end_date: Filter logs until this date (YYYY-MM-DD)
    - user: Filter by username
    - action: Filter by action type
    - status: Filter by status (SUCCESS/FAILED)
    - page: Page number (default 1)
    - page_size: Number of results per page (default 50, max 200)
    """
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
            return Response({"error": "Invalid start_date format. Use YYYY-MM-DD"}, status=status.HTTP_400_BAD_REQUEST)
    
    end_date = request.query_params.get('end_date')
    if end_date:
        try:
            from datetime import datetime, timedelta
            end_dt = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
            logs = logs.filter(timestamp__lt=end_dt)
        except ValueError:
            return Response({"error": "Invalid end_date format. Use YYYY-MM-DD"}, status=status.HTTP_400_BAD_REQUEST)
    
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
        return Response({"error": "Invalid page or page_size parameter"}, status=status.HTTP_400_BAD_REQUEST)
    
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


# ==================== AUTHENTICATION VIEWS ====================

from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView
from datetime import timedelta, datetime as dt
from backend.settings import MAX_FAILED_LOGIN_ATTEMPTS, FAILED_LOGIN_ATTEMPT_DURATION


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    """
    Change password for authenticated user.
    Requires current password for verification.
    """
    user = request.user
    current_password = request.data.get('current_password')
    new_password = request.data.get('new_password')
    
    if not current_password or not new_password:
        return Response(
            {"error": "Current password and new password are required"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Verify current password
    if not check_password(current_password, user.password):
        return Response(
            {"error": "Current password is incorrect"},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    # Validate new password
    if len(new_password) < 8:
        return Response(
            {"error": "New password must be at least 8 characters long"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if current_password == new_password:
        return Response(
            {"error": "New password must be different from current password"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Update password
    user.password = make_password(new_password)
    user.save()
    
    # Audit log
    create_audit_log(
        user=user,
        action='PASSWORD_CHANGE',
        model_name='AuthUser',
        object_id=str(user.id),
        description=f"User {user.username} changed their password",
        ip_address=get_client_ip(request),
        status='SUCCESS'
    )
    
    return Response(
        {"message": "Password changed successfully"},
        status=status.HTTP_200_OK
    )


@api_view(['POST'])
def login_view(request):
    username_or_email = request.data.get('username')
    password = request.data.get('password')
    
    if not username_or_email or not password:
        return Response(
            ErrorMessageBuilder.validation_error(
                ErrorCodes.VAL_MISSING_REQUIRED_FIELD,
                "Username/email and password are required to log in.",
                solution="Please enter both your username (or email) and password."
            ),
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Try to find user by username or email
        if '@' in username_or_email:
            user = AuthUser.objects.get(email__iexact=username_or_email)
            print(LogMessageBuilder.info("LOGIN", f"Found user by email: {user.username}"))
        else:
            user = AuthUser.objects.get(username__iexact=username_or_email)
            print(LogMessageBuilder.info("LOGIN", f"Found user by username: {user.username}"))

        # Check for account lockout due to failed login attempts
        from backend.settings import LOGIN_LOCKOUT_ENABLED, MAX_FAILED_LOGIN_ATTEMPTS, FAILED_LOGIN_ATTEMPT_DURATION
        if LOGIN_LOCKOUT_ENABLED:
            lockout_window = timezone.now() - timedelta(seconds=FAILED_LOGIN_ATTEMPT_DURATION)
            recent_failures = AuditLog.objects.filter(
                action='FAILED_LOGIN',
                description__contains=username_or_email,
                timestamp__gte=lockout_window
            ).count()

            if recent_failures >= MAX_FAILED_LOGIN_ATTEMPTS:
                print(LogMessageBuilder.warning(
                    "LOGIN", 
                    f"Account locked for {username_or_email} due to {recent_failures} failed attempts",
                    f"User must wait {FAILED_LOGIN_ATTEMPT_DURATION // 60} minutes before retrying"
                ))
                return Response(
                    ErrorMessageBuilder.authentication_error(
                        ErrorCodes.AUTH_ACCOUNT_DISABLED,
                        f"Account temporarily locked due to {MAX_FAILED_LOGIN_ATTEMPTS} failed login attempts.",
                        solution=f"Please wait {FAILED_LOGIN_ATTEMPT_DURATION // 60} minutes before trying again, or contact system administrator for immediate assistance."
                    ),
                    status=status.HTTP_429_TOO_MANY_REQUESTS
                )

    except AuthUser.DoesNotExist:
        print(LogMessageBuilder.warning("LOGIN", f"Login failed - user not found: {username_or_email}"))
        # Log failed login attempt
        try:
            log_failed_login(
                username_or_email=username_or_email,
                reason='User account does not exist',
                ip_address=get_client_ip(request),
                user_agent=get_user_agent(request)
            )
        except Exception as e:
            print(LogMessageBuilder.error("LOGIN", "Failed to log failed login attempt", e))
        return Response(
            ErrorMessageBuilder.authentication_error(
                ErrorCodes.AUTH_INVALID_CREDENTIALS,
                "Invalid username/email or password.",
                solution="Please check your credentials and try again. If you've forgotten your password, contact system administrator."
            ),
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    # Check password
    if not check_password(password, user.password):
        print(LogMessageBuilder.warning("LOGIN", f"Invalid password for user: {user.username}"))
        # Log failed login attempt
        try:
            log_failed_login(
                username_or_email=username_or_email,
                reason='Incorrect password provided',
                ip_address=get_client_ip(request),
                user_agent=get_user_agent(request)
            )
        except Exception as e:
            print(LogMessageBuilder.error("LOGIN", "Failed to log failed login attempt", e))
        return Response(
            ErrorMessageBuilder.authentication_error(
                ErrorCodes.AUTH_INVALID_CREDENTIALS,
                "Invalid username/email or password.",
                solution="Please check your password and try again. Password is case-sensitive."
            ),
            status=status.HTTP_401_UNAUTHORIZED
        )
        
    
    if not user.is_active:
        print(f"[LOGIN] Account disabled for user: {user.username}")
        try:
            log_failed_login(
                username_or_email=username_or_email,
                reason='Account is disabled',
                ip_address=get_client_ip(request),
                user_agent=get_user_agent(request)
            )
        except Exception as e:
            print(LogMessageBuilder.error("LOGIN", "Failed to log failed login attempt", e))
        return Response(
            ErrorMessageBuilder.authentication_error(
                ErrorCodes.AUTH_ACCOUNT_DISABLED,
                "Account is disabled",
                solution="Contact system administrator"
            ),
            status=status.HTTP_403_FORBIDDEN
        )

    # Check if user is blocked (RBAC - independent of roles)
    # BLOCKED status prevents ALL users from logging in (including staff/admins)
    # Only superusers can bypass block check (for emergency system access)
    try:
        from .models import GlobalsExtrainfo
        
        # ONLY superusers bypass block check - staff/admins do NOT bypass
        if not user.is_superuser:
            extra_info = GlobalsExtrainfo.objects.get(user=user)

            if extra_info.user_status == 'BLOCKED':
                print(f"[LOGIN] Account BLOCKED for user: {user.username}")
                log_failed_login(
                    username_or_email=username_or_email,
                    reason='User is blocked by administrator',
                    ip_address=get_client_ip(request),
                    user_agent=get_user_agent(request)
                )
                return Response(
                    ErrorMessageBuilder.authentication_error(
                        ErrorCodes.AUTH_ACCOUNT_DISABLED,
                        "Your account has been blocked. Please contact the Super Administrator for assistance.",
                        solution="Contact Super Administrator to resolve this issue. No access is granted when account is blocked."
                    ),
                    status=status.HTTP_403_FORBIDDEN
                )
            elif extra_info.user_status == 'SUSPENDED':
                print(f"[LOGIN] Account SUSPENDED for user: {user.username}")
                return Response(
                    ErrorMessageBuilder.authentication_error(
                        ErrorCodes.AUTH_ACCOUNT_DISABLED,
                        "Your account has been suspended. Please contact the administrator.",
                        solution="Contact administrator to resolve this issue."
                    ),
                    status=status.HTTP_403_FORBIDDEN
                )
    except GlobalsExtrainfo.DoesNotExist:
        # User without GlobalsExtrainfo - allow login if they have valid credentials
        print(LogMessageBuilder.warning("LOGIN", f"No GlobalsExtrainfo for {user.username}, allowing login"))
    except Exception as e:
        print(LogMessageBuilder.warning("LOGIN", f"Could not check block status for {user.username}", e))
    
    # CHECK ADMIN ROLE ACCESS - Only users with admin roles can login
    # This includes: superusers, permanent admin roles, and temporary emergency admin roles
    try:
        # Superusers always have access
        if not user.is_superuser:
            # Get permanent roles
            permanent_roles = GlobalsHoldsdesignation.objects.filter(user=user).select_related('designation')
            permanent_role_names = [entry.designation.name.lower() for entry in permanent_roles]
            
            # Get active emergency roles (temporary admin access)
            from .models import EmergencyAccessRequest
            now = timezone.now()
            active_emergency = EmergencyAccessRequest.objects.filter(
                user=user,
                status='APPROVED',
                reviewed_at__isnull=False
            ).all()
            
            emergency_role_names = []
            for emergency in active_emergency:
                if emergency.reviewed_at and emergency.approved_duration:
                    expiry_time = emergency.reviewed_at + timedelta(minutes=emergency.approved_duration)
                    if now < expiry_time:
                        emergency_role_names.append(emergency.role.name.lower())
            
            # Combine all roles
            all_roles = permanent_role_names + emergency_role_names
            
            # Define admin role patterns (case-insensitive)
            admin_role_patterns = ['admin', 'administrator', 'super_admin', 'system_administrator', 'director']
            
            # Check if user has any admin role
            has_admin_role = any(
                admin_pattern in role_name 
                for role_name in all_roles 
                for admin_pattern in admin_role_patterns
            )
            
            if not has_admin_role:
                print(f"[LOGIN] Access denied for {user.username} - no admin role. Roles: {all_roles}")
                # Log failed login attempt
                try:
                    log_failed_login(
                        username_or_email=username_or_email,
                        reason='User does not have admin role',
                        ip_address=get_client_ip(request),
                        user_agent=get_user_agent(request)
                    )
                except Exception as e:
                    print(LogMessageBuilder.error("LOGIN", "Failed to log failed login attempt", e))
                
                return Response(
                    ErrorMessageBuilder.authentication_error(
                        ErrorCodes.AUTH_UNAUTHORIZED,
                        "Access denied. Only users with administrator roles can log into this system.",
                        solution="Contact the system administrator if you believe you should have access."
                    ),
                    status=status.HTTP_403_FORBIDDEN
                )
            
            print(f"[LOGIN] Admin role verified for {user.username}. Roles: {all_roles}")
    except Exception as e:
        print(LogMessageBuilder.error("LOGIN", f"Error checking admin roles for {user.username}", e))
        return Response(
            ErrorMessageBuilder.authentication_error(
                ErrorCodes.AUTH_UNAUTHORIZED,
                "Error verifying access permissions. Please contact system administrator.",
                solution="System encountered an error while checking your access rights."
            ),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    # Generate tokens
    try:
        refresh = RefreshToken.for_user(user)
        user.last_login = timezone.now()
        user.save()

        # Get permanent roles with enhanced metadata
        user_roles = GlobalsHoldsdesignation.objects.filter(user=user).select_related('designation')
        roles = []
        for entry in user_roles:
            roles.append({
                'name': entry.designation.name,
                'full_name': entry.designation.full_name,
                'role_type': 'permanent',
                'is_emergency': False,
                'display_label': entry.designation.name
            })

        # Add active emergency roles with enhanced metadata
        from .models import EmergencyAccessRequest
        now = timezone.now()
        active_emergency = EmergencyAccessRequest.objects.filter(
            user=user,
            status='APPROVED',
            reviewed_at__isnull=False
        ).all()

        for emergency in active_emergency:
            if emergency.reviewed_at and emergency.approved_duration:
                expiry_time = emergency.reviewed_at + timedelta(minutes=emergency.approved_duration)
                if now < expiry_time:
                    # Calculate time remaining
                    time_remaining = expiry_time - now
                    hours_remaining = int(time_remaining.total_seconds() // 3600)
                    minutes_remaining = int((time_remaining.total_seconds() % 3600) // 60)

                    if hours_remaining > 0:
                        time_remaining_str = f"{hours_remaining}h {minutes_remaining}m"
                    else:
                        time_remaining_str = f"{minutes_remaining} minutes"

                    # Add emergency role with enhanced indicators
                    roles.append({
                        'name': emergency.role.name,
                        'full_name': emergency.role.full_name,
                        'role_type': 'temporary',
                        'is_emergency': True,
                        'display_label': f'{emergency.role.name} (Emergency)',
                        'temporary_tag': 'EMERGENCY ACCESS',
                        'time_remaining': time_remaining_str,
                        'expires_at': expiry_time.isoformat(),
                    })

        print(f"[LOGIN] Successful login for: {user.username}, roles: {roles}")
        
        create_audit_log(
            user=user,
            action='USER_LOGIN',
            model_name='AuthUser',
            object_id=str(user.id),
            description=f"User {user.username} logged in successfully",
            ip_address=get_client_ip(request),
            status='SUCCESS'
        )
        
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'roles': [role['name'] if isinstance(role, dict) else role for role in roles],  # Backward compatible
                'roles_detailed': roles,  # New detailed format with temporary indicators
                'is_staff': user.is_staff,
                'is_superuser': user.is_superuser
            }
        }, status=status.HTTP_200_OK)
    except Exception as e:
        print(f"[LOGIN] Error generating tokens for {user.username}: {str(e)}")
        return Response(
            {"error": "Failed to generate authentication tokens", "detail": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class CustomTokenRefreshView(TokenRefreshView):
    """Custom token refresh that returns user data and verifies admin access"""
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        
        if response.status_code == 200:
            try:
                refresh = RefreshToken(request.data.get('refresh'))
                user_id = refresh['user_id']
                user = AuthUser.objects.get(id=user_id)
                
                # CHECK ADMIN ROLE ACCESS - Verify user still has admin role
                if not user.is_superuser:
                    # Get permanent roles
                    permanent_roles = GlobalsHoldsdesignation.objects.filter(user=user).select_related('designation')
                    permanent_role_names = [entry.designation.name.lower() for entry in permanent_roles]
                    
                    # Get active emergency roles
                    from .models import EmergencyAccessRequest
                    now = timezone.now()
                    active_emergency = EmergencyAccessRequest.objects.filter(
                        user=user,
                        status='APPROVED',
                        reviewed_at__isnull=False
                    ).all()
                    
                    emergency_role_names = []
                    for emergency in active_emergency:
                        if emergency.reviewed_at and emergency.approved_duration:
                            expiry_time = emergency.reviewed_at + timedelta(minutes=emergency.approved_duration)
                            if now < expiry_time:
                                emergency_role_names.append(emergency.role.name.lower())
                    
                    # Combine all roles
                    all_roles = permanent_role_names + emergency_role_names
                    
                    # Define admin role patterns
                    admin_role_patterns = ['admin', 'administrator', 'super_admin', 'system_administrator', 'director']
                    
                    # Check if user has any admin role
                    has_admin_role = any(
                        admin_pattern in role_name 
                        for role_name in all_roles 
                        for admin_pattern in admin_role_patterns
                    )
                    
                    if not has_admin_role:
                        print(f"[TOKEN_REFRESH] Access denied for {user.username} - no admin role")
                        return Response(
                            ErrorMessageBuilder.authentication_error(
                                ErrorCodes.AUTH_UNAUTHORIZED,
                                "Access denied. Admin role required.",
                                solution="Your admin access may have been revoked. Contact system administrator."
                            ),
                            status=status.HTTP_403_FORBIDDEN
                        )
                
                # Get permanent roles
                user_roles = GlobalsHoldsdesignation.objects.filter(user=user).select_related('designation')
                roles = [entry.designation.name for entry in user_roles]

                # Add active emergency roles
                from .models import EmergencyAccessRequest
                now = timezone.now()
                active_emergency = EmergencyAccessRequest.objects.filter(
                    user=user,
                    status='APPROVED',
                    reviewed_at__isnull=False
                ).all()

                for emergency in active_emergency:
                    if emergency.reviewed_at and emergency.approved_duration:
                        expiry_time = emergency.reviewed_at + timedelta(minutes=emergency.approved_duration)
                        if now < expiry_time:
                            if emergency.role.name not in roles:
                                roles.append(emergency.role.name)

                response.data['user'] = {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'roles': roles,
                    'is_staff': user.is_staff,
                }
            except Exception as e:
                print(f"Error getting user data: {e}")
        
        return response


@api_view(['POST'])
def logout_view(request):
    """Log out user and record audit trail"""
    user = request.user
    
    if user.is_authenticated:
        create_audit_log(
            user=user,
            action='USER_LOGOUT',
            model_name='AuthUser',
            object_id=str(user.id),
            description=f"User {user.username} logged out",
            ip_address=get_client_ip(request),
            status='SUCCESS'
        )
        
        return Response({"message": "Successfully logged out"}, status=status.HTTP_200_OK)
    
    return Response(
        ErrorMessageBuilder.authentication_error(
            ErrorCodes.AUTH_UNAUTHORIZED,
            "Authentication required to access this resource.",
            solution="Please log in and provide a valid authentication token."
        ),
        status=status.HTTP_401_UNAUTHORIZED
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_current_user(request):
    """Get current authenticated user's information"""
    user = request.user
    
    try:
        # Get permanent roles
        user_roles = GlobalsHoldsdesignation.objects.filter(user=user).select_related('designation')
        roles = [entry.designation.name for entry in user_roles]

        # Add active emergency roles
        from .models import EmergencyAccessRequest
        now = timezone.now()
        active_emergency = EmergencyAccessRequest.objects.filter(
            user=user,
            status='APPROVED',
            reviewed_at__isnull=False
        ).all()

        for emergency in active_emergency:
            if emergency.reviewed_at and emergency.approved_duration:
                expiry_time = emergency.reviewed_at + timedelta(minutes=emergency.approved_duration)
                if now < expiry_time:
                    if emergency.role.name not in roles:
                        roles.append(emergency.role.name)

        return Response({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'roles': roles,
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser,
            'last_login': user.last_login
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            'error': 'Failed to fetch user information',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

