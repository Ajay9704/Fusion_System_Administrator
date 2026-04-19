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
from .models import GlobalsDesignation, GlobalsHoldsdesignation, GlobalsModuleaccess, AuthUser, Batch, Student, GlobalsDepartmentinfo, Programme, GlobalsFaculty, Staff, AuditLog, EmergencyAccess, HandoverDocumentation
from .serializers import GlobalExtraInfoSerializer, GlobalsDesignationSerializer, GlobalsModuleaccessSerializer, AuthUserSerializer, GlobalsHoldsDesignationSerializer, StudentSerializer, GlobalsFacultySerializer, GlobalsDepartmentinfoSerializer, BatchSerializer, ProgrammeSerializer, StaffSerializer, ViewStudentsWithFiltersSerializer, ViewStaffWithFiltersSerializer, ViewFacultyWithFiltersSerializer, AuditLogSerializer
from .emergency_handover_serializers import EmergencyAccessSerializer, HandoverDocumentationSerializer
from io import StringIO
from .helpers import create_password, send_email, mail_to_user, mail_to_user_single, configure_password_mail, add_user_extra_info, add_user_designation_info, add_student_info, generate_student_username, generate_staff_faculty_username
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from django.conf import settings
from .audit import audit_log, create_audit_log, get_client_ip, log_failed_login, get_user_agent


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
    academic_departments = ['CSE', 'ECE', 'ME', 'MT', 'SM', 'CSE M.Tech', 'CSE Ph.D', 'CSE B.Tech', 'ECE M.Tech', 'ECE Ph.D', 'ECE B.Tech', 'Natural Science', 'Mechatronics', 'Design', 'Workshop']
    records = GlobalsDepartmentinfo.objects.filter(name__in=academic_departments).order_by('id')
    serializer = GlobalsDepartmentinfoSerializer(records, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def get_all_departments_admin(request):
    """All departments including administrative ones — used for staff assignment."""
    records = GlobalsDepartmentinfo.objects.all().order_by('name')
    serializer = GlobalsDepartmentinfoSerializer(records, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def get_departments_by_programme(request):
    """
    Get departments filtered by programme
    Query param: programme (B.Tech, M.Tech, Ph.D, etc.)
    """
    programme = request.query_params.get('programme')
    academic_departments = ['CSE', 'ECE', 'ME', 'MT', 'SM', 'CSE M.Tech', 'CSE Ph.D', 'CSE B.Tech', 'ECE M.Tech', 'ECE Ph.D', 'ECE B.Tech', 'Natural Science', 'Mechatronics', 'Design', 'Workshop']
    
    if not programme:
        # If no programme specified, return all academic departments
        depts = academic_departments
    else:
        # Filter departments based on programme
        programme_dept_mapping = {
            'B.Tech': ['CSE', 'ECE', 'ME', 'MT', 'SM', 'CSE B.Tech', 'ECE B.Tech', 'Natural Science', 'Mechatronics', 'Workshop'],
            'M.Tech': ['CSE M.Tech', 'ECE M.Tech'],
            'Ph.D': ['CSE Ph.D', 'ECE Ph.D'],
            'PhD': ['CSE Ph.D', 'ECE Ph.D'],
            'B.Des': ['Design'],
            'M.Des': ['Design'],
        }
        depts = programme_dept_mapping.get(programme, academic_departments)
    
    records = GlobalsDepartmentinfo.objects.filter(name__in=depts).order_by('name')
    serializer = GlobalsDepartmentinfoSerializer(records, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def get_all_batches(request):
    # distinct('field') is PostgreSQL-only — use values/distinct for SQLite compatibility
    years = Batch.objects.values_list('year', flat=True).distinct().order_by('year')
    records = [Batch.objects.filter(year=y).first() for y in years]
    serializer = BatchSerializer(records, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def get_all_programmes(request):
    records = Programme.objects.all().order_by('id')
    serializer = ProgrammeSerializer(records, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def get_user_role_by_username(request):
    username = request.query_params.get('username')

    if not username:
        return Response({"error": "Username parameter is required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = AuthUser.objects.get(username__iexact=username)
        holds_designation_entries = GlobalsHoldsdesignation.objects.filter(user=user)

        if not holds_designation_entries.exists():
            return Response({"error": "User has no designations."}, status=status.HTTP_404_NOT_FOUND)

        designation_ids = [entry.designation_id for entry in holds_designation_entries]

        roles = GlobalsDesignation.objects.filter(id__in=designation_ids)
        roles_serializer = GlobalsDesignationSerializer(roles, many=True)

        # Get user data and add user_type from GlobalsExtrainfo
        user_data = AuthUserSerializer(user).data
        try:
            extrainfo = GlobalsExtrainfo.objects.get(user=user)
            user_data['user_type'] = extrainfo.user_type
        except GlobalsExtrainfo.DoesNotExist:
            user_data['user_type'] = None

        return Response({
            "user": user_data,
            "roles": roles_serializer.data,
        }, status=status.HTTP_200_OK)

    except AuthUser.DoesNotExist:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
@audit_log(action='UPDATE_USER_ROLES', model_name='GlobalsHoldsdesignation')
def update_user_roles(request):
    username = request.data.get('username')
    roles_to_add = request.data.get('roles')

    if not username or not roles_to_add:
        return Response({"error": "Username and roles are required."}, status=status.HTTP_400_BAD_REQUEST)

    user = get_object_or_404(AuthUser, username__iexact=username)

    # Determine user_type for eligibility check
    from .models import GlobalsExtrainfo
    try:
        user_type = GlobalsExtrainfo.objects.get(user=user).user_type  # 'student', 'faculty', 'staff'
    except GlobalsExtrainfo.DoesNotExist:
        user_type = None

    # Roles that are off-limits based on user_type
    # A student can only hold student-category roles
    # A faculty can hold faculty-category or None-category (administrative) roles
    # A staff can hold staff-category or None-category (administrative) roles
    ELIGIBLE_CATEGORIES = {
        'student': ['student', None],
        'faculty': ['faculty', None],
        'staff':   ['staff', None],
    }

    existing_roles = GlobalsHoldsdesignation.objects.filter(user=user)
    existing_role_names = set(existing_roles.values_list('designation__name', flat=True))

    processed_roles_to_add = set()

    for role in roles_to_add:
        if isinstance(role, dict):
            if 'name' in role:
                processed_roles_to_add.add(role['name'])
        elif isinstance(role, str):
            processed_roles_to_add.add(role)

    # Validate roles before assignment
    for role_name in processed_roles_to_add:
        if role_name not in existing_role_names:
            try:
                designation = GlobalsDesignation.objects.get(name=role_name)

                # Check user_type eligibility
                if user_type and user_type in ELIGIBLE_CATEGORIES:
                    allowed = ELIGIBLE_CATEGORIES[user_type]
                    if designation.category not in allowed:
                        return Response({
                            "error": f"Role '{role_name}' (category: {designation.category}) cannot be assigned to a {user_type}.",
                            "eligible_categories": [c for c in allowed if c is not None],
                            "user_type": user_type,
                        }, status=status.HTTP_403_FORBIDDEN)
                
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
                return Response({"error": f"Role '{role_name}' does not exist."}, status=status.HTTP_404_NOT_FOUND)

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
    else :
        return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)
    
@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
@audit_log(action='UPDATE_ROLE', model_name='GlobalsDesignation')
def update_designation(request):
    name = request.data.get('name')
    
    if not name:
        return Response({"error": "No name provided."}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        designation = GlobalsDesignation.objects.get(name=name)
    except GlobalsDesignation.DoesNotExist:
        return Response({"error": f"Designation with name '{name}' not found."}, status=status.HTTP_404_NOT_FOUND)
    
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
        new_password = create_password(request.data)
        while new_password == user.password:
            new_password = create_password(request.data)
        
        user.password = new_password
        user.save()
        
        try:
            subject = 'Your Password has been reset!!'
            message = f"This Mail is to notify you that your password has been reset by the System Administrator.\n\nPlease check out the new password below:  {new_password}\n\nRegards,\nSystem Administrator,\nIIITDM Jabalpur."
            recipient_list = [f"{user.email}" if settings.EMAIL_TEST_MODE == 0 else settings.EMAIL_TEST_USER]
            send_email(subject=subject, message=message, recipient_list=recipient_list)
        except:
            print(e)
        finally:
            return Response({"password": new_password,"message": "Password reset successfully."}, status=status.HTTP_200_OK)
    except AuthUser.DoesNotExist:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def get_module_access(request):
    role_name = request.query_params.get('designation')
    
    if not role_name:
        return Response({"error": "No role provided."}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        module_access = GlobalsModuleaccess.objects.get(designation=role_name)
    except GlobalsModuleaccess.DoesNotExist:
        return Response({"error": f"Module access for designation '{role_name}' not found."}, status=status.HTTP_404_NOT_FOUND)
    
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
    required_fields = ["username", "first_name", "last_name", "sex", "category", "father_name", "mother_name", "batch", "programme", "department"]
    data = request.data.copy()
    
    # Map frontend field names to backend expected names
    field_mappings = {
        'rollNumber': 'username',
        'roll_number': 'username',
        'firstName': 'first_name',
        'lastName': 'last_name',
        'gender': 'sex',
        'fatherName': 'father_name',
        'motherName': 'mother_name',
        'email': 'personal_email',
        'personalEmail': 'personal_email',
        'phoneNumber': 'phone',
        'dateOfBirth': 'dob',
        'address': 'address'
    }
    
    for frontend_key, backend_key in field_mappings.items():
        if frontend_key in data and backend_key not in data:
            data[backend_key] = data[frontend_key]

    # Normalize gender values to match backend validation
    if 'sex' in data:
        gender_mapping = {
            'male': 'M', 'm': 'M', 'M': 'M',
            'female': 'F', 'f': 'F', 'F': 'F',
            'other': 'O', 'o': 'O', 'O': 'O'
        }
        data['sex'] = gender_mapping.get(data['sex'].lower(), data['sex'])

    print(f"\n[STUDENT CREATION] Received data: {data}")
    print(f"[STUDENT CREATION] Data keys: {list(data.keys())}")

    # Auto-generate roll number if not provided
    if not data.get('username') or not str(data['username']).strip():
        data['username'] = generate_student_username(data)
        print(f"[STUDENT CREATION] Auto-generated username: {data['username']}")
    else:
        data['username'] = str(data['username']).strip().upper()
    
    missing_fields = [field for field in required_fields if field not in data or not data[field]]
    if missing_fields:
        print(f"[STUDENT CREATION] Missing fields: {missing_fields}")
        return Response({
            "error": "Validation failed",
            "message": "Please correct the following errors:",
            "validation_errors": {
                "missing_fields": missing_fields,
                "non_field_errors": [f"The following required fields are empty: {', '.join(missing_fields)}"]
            }
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Validate department-programme compatibility
    programme = data.get('programme')
    department_input = data.get('department')
    if programme and department_input:
        try:
            # Handle department input as either ID or name
            if isinstance(department_input, str) and not department_input.isdigit():
                # Assume it's a name
                department = GlobalsDepartmentinfo.objects.get(name=department_input)
            else:
                # Assume it's an ID
                department = GlobalsDepartmentinfo.objects.get(id=department_input)
            
            programme_dept_mapping = {
                'B.Tech': ['CSE', 'ECE', 'ME', 'MT', 'SM', 'CSE B.Tech', 'ECE B.Tech', 'Natural Science', 'Mechatronics', 'Workshop'],
                'M.Tech': ['CSE M.Tech', 'ECE M.Tech'],
                'Ph.D': ['CSE Ph.D', 'ECE Ph.D'],
                'PhD': ['CSE Ph.D', 'ECE Ph.D'],
                'B.Des': ['Design'],
                'M.Des': ['Design'],
            }
            allowed_depts = programme_dept_mapping.get(programme, [])
            if department.name not in allowed_depts:
                print(f"[STUDENT CREATION] Invalid department '{department.name}' for programme '{programme}'. Allowed: {allowed_depts}")
                return Response({
                    "errors": {
                        "department": [f"'{department.name}' is not valid for '{programme}' programme. Please select from: {', '.join(allowed_depts)}"],
                        "allowed_departments": allowed_depts,
                        "selected_programme": programme,
                        "selected_department": department.name
                    }
                }, status=status.HTTP_400_BAD_REQUEST)
        except GlobalsDepartmentinfo.DoesNotExist:
            print(f"[STUDENT CREATION] Department not found: {department_input}")
            return Response({
                "errors": {
                    "department": [f"Selected department '{department_input}' does not exist in the system."]
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(f"[STUDENT CREATION] Department validation error: {str(e)}")
            return Response({
                "errors": {
                    "non_field_errors": ["Error validating department selection."],
                    "detail": str(e)
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    try:
        user_password = create_password(data)
    except Exception as e:
        print(f"[STUDENT CREATION] Password creation error: {str(e)}")
        return Response({
            "errors": {
                "non_field_errors": ["Password creation failed"],
                "detail": str(e)
            }
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    auth_user_data = {
        "password": make_password(user_password),
        "username": data['username'].upper(),
        "first_name": data.get('first_name', '').lower().capitalize(),
        "last_name": data.get('last_name', '').lower().capitalize() if data.get('last_name') else '',
        "email": f"{data['username'].lower()}@iiitdmj.ac.in",
        "is_staff": False,
        "is_superuser": False,
        "is_active": True,
        "date_joined": datetime.datetime.now().strftime("%Y-%m-%d"),
    }
    
    print(f"[STUDENT CREATION] Auth user data: {auth_user_data}")
    
    auth_serializer = AuthUserSerializer(data=auth_user_data)
    user = None
    if auth_serializer.is_valid():
        try:
            user = auth_serializer.save()
            print(f"[STUDENT CREATION] User created successfully: {user.username}")
        except Exception as e:
            print(f"[STUDENT CREATION] Failed to save user: {str(e)}")
            return Response({
                "error": "Failed to create user account",
                "detail": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        # Format validation errors for better user experience
        error_details = []
        for field, errors in auth_serializer.errors.items():
            error_details.append(f"{field.replace('_', ' ').title()}: {', '.join(str(e) for e in errors)}")
        
        print(f"[STUDENT CREATION] Auth validation errors: {auth_serializer.errors}")

        return Response({
            "errors": auth_serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    default_department = GlobalsDepartmentinfo.objects.get(name='CSE').id
    # Ensure title is within 20 character limit
    title_value = data.get('title', '')
    if not title_value or len(title_value) > 20:
        title_value = 'Mr.' if data['sex'][0].upper() == 'M' else 'Ms.'
    
    extra_info_data = {
        'id': data['username'].upper(),
        'title': title_value,
        'sex': data['sex'][0].upper(),
        'date_of_birth': data.get("dob") if data.get("dob") else "2025-01-01",
        'user_status': "PRESENT",
        'address': data.get("address") if data.get("address") else "NA",
        'phone_no': data.get("phone") if data.get("phone") else 9999999999,
        'about_me': "NA",
        'user_type': 'student',
        'profile_picture': None,
        'date_modified': datetime.datetime.now().strftime("%Y-%m-%d"),
        'department': data.get("department") if data.get("department") else default_department,
        'user': user.id,
    }
    extra_info_serializer = GlobalExtraInfoSerializer(data=extra_info_data)
    extra_info = None
    if extra_info_serializer.is_valid():
        extra_info = extra_info_serializer.save()
    else:
        return Response({
            "message": "Error in adding user to globals extra info table",
            "data": extra_info_serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    designation_id = GlobalsDesignation.objects.get(name='student').id
    holds_designation_data = {
        'designation' : designation_id,
        'user' : user.id,
        'working' : user.id,
    }
    holds_designation_serializer = GlobalsHoldsDesignationSerializer(data=holds_designation_data)
    if holds_designation_serializer.is_valid():
        holds_designation_serializer.save()
    else:
        return Response({
            "message": "Error in adding user to globals holds designation table",
            "data": holds_designation_serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    batch = Batch.objects.filter(name = data.get('programme'), discipline__acronym = extra_info.department.name, year = data.get('batch')).first()
    
    # Ensure programme is within 10 character limit
    programme_value = data.get('programme', 'B.Tech')
    if len(programme_value) > 10:
        programme_value = programme_value[:10]
    
    # Ensure category is within 10 character limit
    category_value = data.get('category', 'GEN').upper()
    if len(category_value) > 10:
        category_value = category_value[:10]
    
    student_data = {
        'id' : extra_info.id,
        'programme' : programme_value,
        'batch' : int(data.get('batch')) if data.get('batch') else datetime.datetime.now().year,
        'batch_id' : batch.id if batch else None,
        'cpi': 0.0,
        'category' : category_value,
        'father_name' : data.get('father_name') if data.get('father_name') else None,
        'mother_name' : data.get('mother_name') if data.get('mother_name') else None,
        'hall_no': data.get('hall_no') if data.get('hall_no') else 3,
        'room_no': None,
        'specialization': None,
        'curr_semester_no' : max(1, 2*(datetime.datetime.now().year - int(data.get('batch', datetime.datetime.now().year))) + datetime.datetime.now().month // 7),
    }
    student_data_serializer = StudentSerializer(data=student_data)
    if student_data_serializer.is_valid():
        student_data_serializer.save()
    else:
        return Response({
            "message": "Error in adding user to academic information student table",
            "data": student_data_serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    response_data = {
        "message": f"1 user created successfully.",
        "created_users": [auth_serializer.data],
        "skipped_users_count": 0,
    }

    return Response(response_data, status=status.HTTP_201_CREATED)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@audit_log(action='CREATE_STAFF', model_name='AuthUser')
def add_individual_staff(request):
    required_fields = ["first_name", "last_name", "sex", "designation"]
    data = request.data.copy()
    print(f"\n[STAFF CREATION] Received data: {data}")

    # Normalize gender values to match backend validation
    if 'sex' in data:
        gender_mapping = {
            'male': 'M', 'm': 'M', 'M': 'M',
            'female': 'F', 'f': 'F', 'F': 'F',
            'other': 'O', 'o': 'O', 'O': 'O'
        }
        data['sex'] = gender_mapping.get(data['sex'].lower(), data['sex'])

    # Auto-generate username if not provided
    if not data.get('username') or not str(data['username']).strip():
        data['username'] = generate_staff_faculty_username(data)
        print(f"[STAFF CREATION] Auto-generated username: {data['username']}")
    else:
        data['username'] = str(data['username']).strip().lower()

    missing_fields = [field for field in required_fields if field not in data or not data[field]]
    if missing_fields:
        print(f"[STAFF CREATION] Missing fields: {missing_fields}")
        return Response({
            "error": "Missing required fields.",
            "missing_fields": missing_fields
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user_password = create_password(data)
    except Exception as e:
        print(f"[STAFF CREATION] Password creation error: {str(e)}")
        return Response({
            "error": "Password creation failed",
            "detail": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    auth_user_data = {
        "password": make_password(user_password),
        "username": data['username'].lower(),
        "first_name": data.get('first_name', '').lower().capitalize(),
        "last_name": data.get('last_name', '').lower().capitalize() if data.get('last_name') else '',
        "email": f"{data['username'].lower()}@iiitdmj.ac.in",
        "is_staff": True,
        "is_superuser": False,
        "is_active": True,
        "date_joined": datetime.datetime.now().strftime("%Y-%m-%d"),
    }
    
    auth_serializer = AuthUserSerializer(data=auth_user_data)
    user = None
    if auth_serializer.is_valid():
        try:
            user = auth_serializer.save()
            print(f"[STAFF CREATION] User created successfully: {user.username}")
        except Exception as e:
            return Response({"error": "Failed to create user account", "detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        print(f"[STAFF CREATION] Auth validation errors: {auth_serializer.errors}")
        return Response({"error": "User validation failed", "fields": auth_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    # Safe department default
    try:
        default_department = GlobalsDepartmentinfo.objects.get(name='CSE').id
    except GlobalsDepartmentinfo.DoesNotExist:
        default_department = GlobalsDepartmentinfo.objects.first().id

    title_value = data.get('title', '')
    if not title_value or len(title_value) > 20:
        title_value = 'Mr.' if data['sex'][0].upper() == 'M' else 'Ms.'
    
    extra_info_data = {
        'id': data['username'].lower(),
        'title': title_value,
        'sex': data['sex'][0].upper(),
        'date_of_birth': data.get("dob") if data.get("dob") else "2000-01-01",
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
    else:
        return Response({"message": "Error in extra info table", "data": extra_info_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    holds_designation_data = {
        'designation': data.get('designation'),
        'user': user.id,
        'working': user.id,
    }
    holds_designation_serializer = GlobalsHoldsDesignationSerializer(data=holds_designation_data)
    if holds_designation_serializer.is_valid():
        holds_designation_serializer.save()
    else:
        return Response({"message": "Error in holds designation table", "data": holds_designation_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    staff_serializer = StaffSerializer(data={'id': extra_info.id})
    if staff_serializer.is_valid():
        staff_serializer.save()
    else:
        return Response({"message": "Error in staff table", "data": staff_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    # Send credentials to personal email
    personal_email = data.get('personal_email', '').strip()
    try:
        mail_to_user_single(
            {'username': user.username, 'email': user.email},
            user_password,
            recipient_email=personal_email if personal_email else user.email
        )
    except Exception as e:
        print(f"[STAFF CREATION] Email send failed: {str(e)}")

    return Response({
        "message": "Staff added successfully",
        "username": user.username,
        "email": user.email,
    }, status=status.HTTP_201_CREATED)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@audit_log(action='CREATE_FACULTY', model_name='AuthUser')
def add_individual_faculty(request):
    required_fields = ["first_name", "last_name", "sex", "designation", "department"]
    data = request.data.copy()
    print(f"\n[FACULTY CREATION] Received data: {data}")

    # Normalize gender values to match backend validation
    if 'sex' in data:
        gender_mapping = {
            'male': 'M', 'm': 'M', 'M': 'M',
            'female': 'F', 'f': 'F', 'F': 'F',
            'other': 'O', 'o': 'O', 'O': 'O'
        }
        data['sex'] = gender_mapping.get(data['sex'].lower(), data['sex'])

    # Auto-generate username if not provided
    if not data.get('username') or not str(data['username']).strip():
        data['username'] = generate_staff_faculty_username(data)
        print(f"[FACULTY CREATION] Auto-generated username: {data['username']}")
    else:
        data['username'] = str(data['username']).strip().lower()

    missing_fields = [field for field in required_fields if field not in data or not data[field]]
    if missing_fields:
        print(f"[FACULTY CREATION] Missing fields: {missing_fields}")
        return Response({
            "error": "Validation failed",
            "message": "Please correct the following errors:",
            "validation_errors": {
                "missing_fields": missing_fields,
                "non_field_errors": [f"The following required fields are empty: {', '.join(missing_fields)}"]
            }
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        user_password = create_password(data)
    except Exception as e:
        return Response({
            "error": "Password generation failed",
            "message": "Could not generate secure password. Please try again.",
            "suggestion": "Contact the administrator if this problem persists."
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    auth_user_data = {
        "password": make_password(user_password),
        "username": data['username'].lower(),
        "first_name": data.get('first_name', '').lower().capitalize(),
        "last_name": data.get('last_name', '').lower().capitalize() if data.get('last_name') else '',
        "email": f"{data['username'].lower()}@iiitdmj.ac.in",
        "is_staff": False,
        "is_superuser": False,
        "is_active": True,
        "date_joined": datetime.datetime.now().strftime("%Y-%m-%d"),
    }

    auth_serializer = AuthUserSerializer(data=auth_user_data)
    user = None
    if auth_serializer.is_valid():
        try:
            user = auth_serializer.save()
        except Exception as e:
            return Response({"error": "Failed to create user account", "detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        return Response({"error": "User validation failed", "fields": auth_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    title_value = data.get('title', '')
    if not title_value or len(title_value) > 20:
        title_value = 'Mr.' if data['sex'][0].upper() == 'M' else 'Ms.'

    extra_info_data = {
        'id': data['username'].lower(),
        'title': title_value,
        'sex': data['sex'][0].upper(),
        'date_of_birth': data.get("dob") if data.get("dob") else "2000-01-01",
        'user_status': "PRESENT",
        'address': data.get("address") if data.get("address") else "NA",
        'phone_no': data.get("phone") if data.get("phone") else 9999999999,
        'about_me': "NA",
        'user_type': 'faculty',
        'profile_picture': None,
        'date_modified': datetime.datetime.now().strftime("%Y-%m-%d"),
        'department': data.get("department"),
        'user': user.id,
    }
    extra_info_serializer = GlobalExtraInfoSerializer(data=extra_info_data)
    extra_info = None
    if extra_info_serializer.is_valid():
        extra_info = extra_info_serializer.save()
    else:
        return Response({"message": "Error in extra info table", "data": extra_info_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    holds_designation_data = {
        'designation': data.get('designation'),
        'user': user.id,
        'working': user.id,
    }
    holds_designation_serializer = GlobalsHoldsDesignationSerializer(data=holds_designation_data)
    if holds_designation_serializer.is_valid():
        holds_designation_serializer.save()
    else:
        return Response({"message": "Error in holds designation table", "data": holds_designation_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    faculty_serializer = GlobalsFacultySerializer(data={'id': extra_info.id})
    if faculty_serializer.is_valid():
        faculty_serializer.save()
    else:
        return Response({"message": "Error in faculty table", "data": faculty_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    # Send credentials to personal email
    personal_email = data.get('personal_email', '').strip()
    try:
        mail_to_user_single(
            {'username': user.username, 'email': user.email},
            user_password,
            recipient_email=personal_email if personal_email else user.email
        )
    except Exception as e:
        print(f"[FACULTY CREATION] Email send failed: {str(e)}")

    return Response({
        "message": "Faculty added successfully",
        "username": user.username,
        "email": user.email,
    }, status=status.HTTP_201_CREATED)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@audit_log(action='BULK_IMPORT_USERS', model_name='AuthUser')
def bulk_import_users(request):
    """
    Enterprise-grade bulk user import with comprehensive validation
    CSV file headers:
    1 username, 2 first_name, 3 last_name, 4 sex, 5 category, 6 father_name,
    7 mother_name, 8 batch, 9 programme, 10 title, 11 dob, 12 address,
    13 phone_no, 14 department
    """
    # Configuration
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
    MAX_RECORDS = 1000
    CHUNK_SIZE = 50  # Process in chunks of 50 records
    REQUIRED_COLUMNS = 9  # Minimum required columns

    # Validation: File presence
    if 'file' not in request.FILES:
        return Response({
            "error": "No file provided.",
            "detail": "Please upload a CSV file."
        }, status=status.HTTP_400_BAD_REQUEST)

    file = request.FILES['file']

    # Validation: File extension
    if not file.name.lower().endswith('.csv'):
        return Response({
            "error": "Invalid file format.",
            "detail": "Please upload a valid CSV file (.csv extension required)."
        }, status=status.HTTP_400_BAD_REQUEST)

    # Validation: File size
    if file.size > MAX_FILE_SIZE:
        size_mb = file.size / (1024 * 1024)
        return Response({
            "error": "File too large.",
            "detail": f"File size ({size_mb:.2f}MB) exceeds maximum allowed size (5MB)."
        }, status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)

    try:
        # Read and parse CSV
        file_data = file.read().decode('utf-8')
        csv_reader = csv.reader(StringIO(file_data))

        # Read headers
        try:
            headers = next(csv_reader)
        except StopIteration:
            return Response({
                "error": "Empty CSV file.",
                "detail": "The uploaded file contains no data."
            }, status=status.HTTP_400_BAD_REQUEST)

        # Count total rows
        all_rows = list(csv_reader)
        total_rows = len(all_rows)

        # Validation: Row count
        if total_rows == 0:
            return Response({
                "error": "No data rows.",
                "detail": "CSV file contains headers but no data rows."
            }, status=status.HTTP_400_BAD_REQUEST)

        if total_rows > MAX_RECORDS:
            return Response({
                "error": "Too many records.",
                "detail": f"File contains {total_rows} records. Maximum allowed is {MAX_RECORDS}. Please split your file into smaller batches."
            }, status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)

        # Processing variables
        created_users = []
        failed_users = []
        validation_errors = []

        # Process rows in chunks
        for chunk_start in range(0, total_rows, CHUNK_SIZE):
            chunk_end = min(chunk_start + CHUNK_SIZE, total_rows)
            chunk_rows = all_rows[chunk_start:chunk_end]

            for row_number, row in enumerate(chunk_rows, start=chunk_start + 1):  # +1 for header row
                # Validation: Row has enough columns
                if len(row) < REQUIRED_COLUMNS:
                    error_msg = f"Row {row_number}: Insufficient columns. Expected at least {REQUIRED_COLUMNS}, got {len(row)}"
                    validation_errors.append({
                        'row': row_number,
                        'username': row[0] if len(row) > 0 else 'N/A',
                        'error': 'INSUFFICIENT_COLUMNS',
                        'message': f"Only {len(row)} columns found. Need at least {REQUIRED_COLUMNS}."
                    })
                    failed_users.append(row)
                    continue

                # Validation: Username presence
                if not row[0] or not row[0].strip():
                    validation_errors.append({
                        'row': row_number,
                        'username': 'N/A',
                        'error': 'MISSING_USERNAME',
                        'message': 'Username cannot be empty.'
                    })
                    failed_users.append(row)
                    continue

                username = row[0].strip()

                # Validation: Username format (alphanumeric)
                if not username.replace('_', '').replace('-', '').isalnum():
                    validation_errors.append({
                        'row': row_number,
                        'username': username,
                        'error': 'INVALID_USERNAME_FORMAT',
                        'message': 'Username must contain only letters, numbers, underscores, and hyphens.'
                    })
                    failed_users.append(row)
                    continue

                # Check for duplicate username in batch
                if any(u['username'] == username.upper() for u in created_users):
                    validation_errors.append({
                        'row': row_number,
                        'username': username,
                        'error': 'DUPLICATE_USERNAME',
                        'message': 'Username already exists in this batch.'
                    })
                    failed_users.append(row)
                    continue

                # Check if user already exists in database
                if AuthUser.objects.filter(username__iexact=username).exists():
                    validation_errors.append({
                        'row': row_number,
                        'username': username,
                        'error': 'USER_EXISTS',
                        'message': 'User with this username already exists in database.'
                    })
                    failed_users.append(row)
                    continue

                # Validation: Required fields presence
                missing_fields = []
                if not row[1] or not row[1].strip(): missing_fields.append('first_name')
                if not row[4] or not row[4].strip(): missing_fields.append('category')
                if not row[8] or not row[8].strip(): missing_fields.append('batch')
                if not row[9] or not row[9].strip(): missing_fields.append('programme')

                if missing_fields:
                    validation_errors.append({
                        'row': row_number,
                        'username': username,
                        'error': 'MISSING_REQUIRED_FIELDS',
                        'message': f"Missing required fields: {', '.join(missing_fields)}"
                    })
                    failed_users.append(row)
                    continue

                # Validation: Date format
                if len(row) > 10 and row[10] and row[10].strip():
                    dob = row[10].strip()
                    try:
                        # Try to parse date using multiple formats
                        from .helpers import convert_to_iso
                        convert_to_iso(dob)
                    except Exception:
                        validation_errors.append({
                            'row': row_number,
                            'username': username,
                            'error': 'INVALID_DATE_FORMAT',
                            'message': f"Date of birth '{dob}' is not in a valid format (use DD-MM-YYYY or DD/MM/YYYY)"
                        })
                        failed_users.append(row)
                        continue

                # All validations passed, create user
                try:
                    user_data = {
                        'password': make_password("user@123"),
                        'username': username.upper(),
                        'first_name': row[1].strip().lower().capitalize() if row[1].strip() else 'NA',
                        'last_name': row[2].strip().lower().capitalize() if len(row) > 2 and row[2].strip() else 'NA',
                        'email': f"{username.lower()}@iiitdmj.ac.in",
                        'is_staff': False,
                        'is_superuser': False,
                        'is_active': True,
                    }

                    serializer = AuthUserSerializer(data=user_data)
                    if serializer.is_valid():
                        user = serializer.save()
                    else:
                        validation_errors.append({
                            'row': row_number,
                            'username': username,
                            'error': 'SERIALIZATION_ERROR',
                            'message': str(serializer.errors)
                        })
                        failed_users.append(row)
                        continue

                    # Create extra info
                    extra_info_serializer = add_user_extra_info(row, user)
                    if not extra_info_serializer or not extra_info_serializer.is_valid():
                        validation_errors.append({
                            'row': row_number,
                            'username': username,
                            'error': 'EXTRA_INFO_ERROR',
                            'message': str(extra_info_serializer.errors) if extra_info_serializer else 'Failed to create extra info'
                        })
                        failed_users.append(row)
                        continue

                    extra_serializer = extra_info_serializer.save()

                    # Add role
                    role_serializer = add_user_designation_info(user.id)
                    if not role_serializer or not role_serializer.is_valid():
                        validation_errors.append({
                            'row': row_number,
                            'username': username,
                            'error': 'ROLE_ERROR',
                            'message': 'Failed to assign student role'
                        })
                        failed_users.append(row)
                        continue

                    role_serializer.save()

                    # Add student info
                    student_serializer = add_student_info(row, extra_serializer)
                    if not student_serializer or not student_serializer.is_valid():
                        validation_errors.append({
                            'row': row_number,
                            'username': username,
                            'error': 'STUDENT_INFO_ERROR',
                            'message': str(student_serializer.errors) if student_serializer else 'Failed to create student info'
                        })
                        failed_users.append(row)
                        continue

                    student_serializer.save()

                    # Success! Add to created list
                    created_users.append({
                        'username': user.username,
                        'email': user.email,
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                        'row': row_number
                    })

                except Exception as e:
                    validation_errors.append({
                        'row': row_number,
                        'username': username,
                        'error': 'INTERNAL_ERROR',
                        'message': f"Unexpected error: {str(e)}"
                    })
                    failed_users.append(row)
                    continue

        # Send emails to successfully created users
        if len(created_users) > 0:
            mail_to_user(created_users)

        # Prepare response
        response_data = {
            "success": True,
            "message": f"Import completed: {len(created_users)} users created successfully.",
            "summary": {
                "total_rows": total_rows,
                "created": len(created_users),
                "failed": len(failed_users),
                "success_rate": f"{(len(created_users) / total_rows * 100):.1f}%"
            },
            "created_users": created_users,
            "skipped_users_count": len(failed_users),
            "validation_errors": validation_errors
        }

        # Generate failed users CSV for download
        if failed_users:
            output = StringIO()
            writer = csv.writer(output)
            writer.writerow(headers)
            for failed_user in failed_users:
                writer.writerow(failed_user)
            output.seek(0)
            response_data["skipped_users_csv"] = output.getvalue()

        return Response(response_data, status=status.HTTP_201_CREATED)

    except UnicodeDecodeError:
        return Response({
            "error": "File encoding error.",
            "detail": "Unable to read file. Please ensure it's encoded in UTF-8 format."
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({
            "error": "Import failed.",
            "detail": f"An unexpected error occurred: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
        "dob", "address", "phone_no", "department"
    ])
    return response

class UserListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            # Debug: Log the incoming request
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"UserListView called with user: {request.user}, params: {request.GET}")

            user_type = request.GET.get('type')
            serializer = None

            if not user_type:
                return Response({"error": "Missing 'type' parameter"}, status=status.HTTP_400_BAD_REQUEST)

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
                return Response({"error": "Invalid or missing user type."}, status=status.HTTP_400_BAD_REQUEST)

            return Response(serializer.data)

        except Exception as e:
            import traceback
            return Response({
                "error": f"Internal server error: {str(e)}",
                "detail": traceback.format_exc()
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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

        # TRIGGER: User archived event for notifications/integration
        try:
            from .integration_events import trigger_user_archived
            trigger_user_archived(
                user=user,
                user_type='user',  # Can be refined based on user type detection
                archived_by=request.user,
                reason='User archived via admin panel'
            )
        except Exception as e:
            # Don't fail the operation if notification trigger fails
            print(f"[INTEGRATION EVENT] User archived trigger failed: {e}")

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

        # TRIGGER: User restored event for notifications/integration
        try:
            from .integration_events import trigger_user_restored
            trigger_user_restored(
                user=user,
                user_type='user',
                restored_by=request.user
            )
        except Exception as e:
            # Don't fail the operation if notification trigger fails
            print(f"[INTEGRATION EVENT] User restored trigger failed: {e}")

        return Response({
            "message": f"User {user.username} restored successfully"
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            "error": f"Failed to restore user: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_audit_logs(request):
    """
    Retrieve audit logs with filtering support.
    ADMIN ONLY - Only staff/superusers can access audit logs
    Query params:
    - start_date: Filter logs from this date (YYYY-MM-DD)
    - end_date: Filter logs until this date (YYYY-MM-DD)
    - user: Filter by username
    - action: Filter by action type
    - status: Filter by status (SUCCESS/FAILED)
    - page: Page number (default 1)
    - page_size: Number of results per page (default 50, max 200)
    """
    # Restrict to admin users only
    if not request.user.is_staff and not request.user.is_superuser:
        return Response({
            'error': 'Permission denied',
            'detail': 'Only administrators can access audit logs'
        }, status=status.HTTP_403_FORBIDDEN)
    
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
from django.contrib.auth.hashers import check_password
from django.utils import timezone
from datetime import timedelta, datetime as dt
from backend.settings import MAX_FAILED_LOGIN_ATTEMPTS, FAILED_LOGIN_ATTEMPT_DURATION


@api_view(['POST'])
def login_view(request):
    """
    Authenticate user and return JWT tokens.
    Accepts username OR email + password.
    """
    username_or_email = request.data.get('username')
    password = request.data.get('password')
    
    if not username_or_email or not password:
        return Response(
            {"error": "Username/email and password are required"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Try to find user by username or email
        if '@' in username_or_email:
            user = AuthUser.objects.get(email__iexact=username_or_email)
            print(f"[LOGIN] Found user by email: {user.username}")
        else:
            user = AuthUser.objects.get(username__iexact=username_or_email)
            print(f"[LOGIN] Found user by username: {user.username}")

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
                print(f"[LOGIN] Account locked for {username_or_email} due to {recent_failures} failed attempts")
                return Response({
                    "error": f"Account locked due to multiple failed login attempts. Please try again after {FAILED_LOGIN_ATTEMPT_DURATION // 60} minutes."
                }, status=status.HTTP_429_TOO_MANY_REQUESTS)

    except AuthUser.DoesNotExist:
        print(f"[LOGIN] User not found: {username_or_email}")
        # Log failed login attempt
        try:
            log_failed_login(
                username_or_email=username_or_email,
                reason='User does not exist',
                ip_address=get_client_ip(request),
                user_agent=get_user_agent(request)
            )
        except Exception as e:
            print(f"[ERROR] Failed to log failed login: {e}")
        return Response(
            {"error": "Invalid credentials"},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    # Check password
    if not check_password(password, user.password):
        print(f"[LOGIN] Invalid password for user: {user.username}")
        # Log failed login attempt
        try:
            log_failed_login(
                username_or_email=username_or_email,
                reason='Invalid password',
                ip_address=get_client_ip(request),
                user_agent=get_user_agent(request)
            )
        except Exception as e:
            print(f"[ERROR] Failed to log failed login: {e}")
        return Response(
            {"error": "Invalid credentials"},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    if not user.is_active:
        print(f"[LOGIN] Account disabled for user: {user.username}")
        # Log failed login attempt
        try:
            log_failed_login(
                username_or_email=username_or_email,
                reason='Account is disabled',
                ip_address=get_client_ip(request),
                user_agent=get_user_agent(request)
            )
        except Exception as e:
            print(f"[ERROR] Failed to log failed login: {e}")
        return Response(
            {"error": "Account is disabled"},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # SYSTEM ADMIN RESTRICTION: Only admin users (is_staff or is_superuser) can access System Admin
    if not user.is_staff and not user.is_superuser:
        print(f"[LOGIN] Non-admin user attempted to access System Admin: {user.username}")
        try:
            log_failed_login(
                username_or_email=username_or_email,
                reason='Non-admin user attempted to access System Admin',
                ip_address=get_client_ip(request),
                user_agent=get_user_agent(request)
            )
        except Exception as e:
            print(f"[ERROR] Failed to log failed login: {e}")
        return Response(
            {"error": "Access denied. System Admin is restricted to administrators only."},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Generate tokens
    try:
        refresh = RefreshToken.for_user(user)
        user.last_login = timezone.now()
        user.save()
        
        user_roles = GlobalsHoldsdesignation.objects.filter(user=user).select_related('designation')
        roles = [entry.designation.name for entry in user_roles]
        
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
                'roles': roles,
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
    """Custom token refresh that returns user data"""
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        
        if response.status_code == 200:
            try:
                refresh = RefreshToken(request.data.get('refresh'))
                user_id = refresh['user_id']
                user = AuthUser.objects.get(id=user_id)
                
                user_roles = GlobalsHoldsdesignation.objects.filter(user=user).select_related('designation')
                roles = [entry.designation.name for entry in user_roles]
                
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
    
    return Response({"error": "Not authenticated"}, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_current_user(request):
    """Get current authenticated user's information"""
    user = request.user
    
    try:
        user_roles = GlobalsHoldsdesignation.objects.filter(user=user).select_related('designation')
        roles = [entry.designation.name for entry in user_roles]
        
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


# ==============================================================================
# DEPARTMENT MANAGEMENT ENDPOINTS
# ==============================================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_departments_with_hierarchy(request):
    """
    Get all departments with hierarchy information
    Returns tree structure of departments
    """
    try:
        departments = GlobalsDepartmentinfo.objects.all().order_by('name')

        # Build department lookup
        dept_dict = {}
        for dept in departments:
            dept_dict[dept.id] = dept
        
        department_data = []
        for dept in departments:
            # Get parent information
            parent_id = None
            parent_name = None
            if hasattr(dept, 'parent_department_id') and dept.parent_department_id:
                parent_id = dept.parent_department_id
                if dept.parent_department_id in dept_dict:
                    parent_name = dept_dict[dept.parent_department_id].name
            
            # Calculate hierarchy level
            level = 0
            current_dept = dept
            visited = set()
            while hasattr(current_dept, 'parent_department_id') and current_dept.parent_department_id:
                if current_dept.parent_department_id in visited:
                    break  # Prevent infinite loop on circular references
                visited.add(current_dept.id)
                level += 1
                current_dept = dept_dict.get(current_dept.parent_department_id)
                if not current_dept:
                    break
            
            # Check if has children
            has_children = False
            if hasattr(dept, 'child_departments'):
                try:
                    has_children = dept.child_departments.exists()
                except:
                    has_children = False
            
            department_data.append({
                'id': dept.id,
                'name': dept.name,
                'parent_id': parent_id,
                'parent_name': parent_name,
                'level': level,
                'has_children': has_children,
            })

        return Response(department_data, status=status.HTTP_200_OK)

    except Exception as e:
        print(f"[DEPARTMENT HIERARCHY] Error: {str(e)}")
        return Response({
            'error': 'Failed to fetch departments',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@audit_log(action='CREATE_DEPARTMENT', model_name='GlobalsDepartmentinfo')
def create_department(request):
    """
    Create a new department
    Body: {
        "name": "Computer Science",
        "parent_id": 1  # optional
    }
    """
    try:
        name = request.data.get('name')
        parent_id = request.data.get('parent_id')

        if not name:
            return Response({
                'error': 'Department name is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Check if department already exists
        if GlobalsDepartmentinfo.objects.filter(name=name).exists():
            return Response({
                'error': f'Department with name "{name}" already exists'
            }, status=status.HTTP_409_CONFLICT)

        # Validate parent department (note: parent_department field doesn't exist in current schema)
        # Skipping parent validation for now as the field is not in the database
        parent_dept = None
        if parent_id:
            print(f"[DEPARTMENT CREATE] Warning: parent_department field not available in current schema")

        # Create department (without parent_department as it doesn't exist)
        department = GlobalsDepartmentinfo.objects.create(
            name=name
        )

        return Response({
            'message': 'Department created successfully',
            'department': {
                'id': department.id,
                'name': department.name,
            }
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({
            'error': 'Failed to create department',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
@audit_log(action='UPDATE_DEPARTMENT', model_name='GlobalsDepartmentinfo')
def update_department(request, department_id):
    """
    Update a department
    Body: {
        "name": "Computer Science",  # optional
        "parent_id": 1  # optional
    }
    """
    try:
        try:
            department = GlobalsDepartmentinfo.objects.get(id=department_id)
        except GlobalsDepartmentinfo.DoesNotExist:
            return Response({
                'error': f'Department with id {department_id} not found'
            }, status=status.HTTP_404_NOT_FOUND)

        name = request.data.get('name')
        parent_id = request.data.get('parent_id')

        # Check for cycle if parent is being changed
        if parent_id:
            try:
                new_parent = GlobalsDepartmentinfo.objects.get(id=parent_id)

                # Prevent setting self as parent
                if new_parent.id == department.id:
                    return Response({
                        'error': 'Cannot set department as its own parent'
                    }, status=status.HTTP_400_BAD_REQUEST)

                # Check for cycles: new_parent cannot be a descendant of department
                descendants = department.get_descendants()
                if any(d.id == new_parent.id for d in descendants):
                    return Response({
                        'error': 'Cannot create cycle in hierarchy: parent department cannot be a descendant'
                    }, status=status.HTTP_409_CONFLICT)

            except GlobalsDepartmentinfo.DoesNotExist:
                return Response({
                    'error': f'Parent department with id {parent_id} does not exist'
                }, status=status.HTTP_404_NOT_FOUND)

        # Update name if provided
        if name:
            # Check if another department with this name exists
            existing = GlobalsDepartmentinfo.objects.filter(name=name).exclude(id=department_id)
            if existing.exists():
                return Response({
                    'error': f'Department with name "{name}" already exists'
                }, status=status.HTTP_409_CONFLICT)
            department.name = name

        # Update parent if provided
        if parent_id is not None:  # Check for None to allow removing parent
            if parent_id == '':  # Empty string means remove parent
                department.parent_department = None
            else:
                department.parent_department = GlobalsDepartmentinfo.objects.get(id=parent_id)

        department.save()

        return Response({
            'message': 'Department updated successfully',
            'department': {
                'id': department.id,
                'name': department.name,
                'parent_id': department.parent_department.id if department.parent_department else None,
            }
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            'error': 'Failed to update department',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
@audit_log(action='DELETE_DEPARTMENT', model_name='GlobalsDepartmentinfo')
def delete_department(request, department_id):
    """
    Delete a department
    Checks if department has children or is in use before deleting
    """
    try:
        try:
            department = GlobalsDepartmentinfo.objects.get(id=department_id)
        except GlobalsDepartmentinfo.DoesNotExist:
            return Response({
                'error': f'Department with id {department_id} not found'
            }, status=status.HTTP_404_NOT_FOUND)

        # Check if department has children
        if department.child_departments.exists():
            return Response({
                'error': 'Cannot delete department with child departments',
                'detail': 'Please reassign or delete child departments first'
            }, status=status.HTTP_409_CONFLICT)

        # Check if department is in use by any designation
        if GlobalsDesignation.objects.filter(dept_if_not_basic=department).exists():
            return Response({
                'error': 'Cannot delete department that is in use',
                'detail': 'Department is referenced by one or more designations'
            }, status=status.HTTP_409_CONFLICT)

        # Store name for response
        dept_name = department.name

        # Delete the department
        department.delete()

        return Response({
            'message': f'Department "{dept_name}" deleted successfully'
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            'error': 'Failed to delete department',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_department_tree(request):
    """
    Get department hierarchy as a tree structure
    Useful for visualization and dropdowns
    """
    try:
        # Get all departments
        departments = GlobalsDepartmentinfo.objects.all().order_by('name')
        
        # Build a dictionary of all departments
        dept_dict = {}
        for dept in departments:
            dept_dict[dept.id] = {
                'id': dept.id,
                'name': dept.name,
                'parent_id': dept.parent_department_id if hasattr(dept, 'parent_department_id') else None,
                'children': []
            }
        
        # Build the tree structure
        tree = []
        for dept_id, dept_data in dept_dict.items():
            if dept_data['parent_id'] is None:
                # This is a root department
                tree.append(dept_data)
            else:
                # This is a child department, add to parent's children
                if dept_data['parent_id'] in dept_dict:
                    dept_dict[dept_data['parent_id']]['children'].append(dept_data)
        
        # Sort children at each level
        def sort_children(node):
            node['children'].sort(key=lambda x: x['name'])
            for child in node['children']:
                sort_children(child)
        
        for root in tree:
            sort_children(root)

        return Response({
            'tree': tree,
            'total_count': len(dept_dict)
        }, status=status.HTTP_200_OK)

    except Exception as e:
        print(f"[DEPARTMENT TREE] Error: {str(e)}")
        return Response({
            'error': 'Failed to fetch department tree',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==============================================================================
# ROLE SWITCHING ENDPOINTS
# ==============================================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_available_roles(request):
    """
    Get all roles available to the current user
    Returns list of designations held by the user with their details
    """
    try:
        user = request.user

        # Get all role assignments for this user
        role_assignments = GlobalsHoldsdesignation.objects.filter(
            user=user
        ).select_related('designation').order_by('designation__name')

        roles = []
        for assignment in role_assignments:
            designation = assignment.designation

            # Check if role is currently active
            is_active = True  # You can add logic to determine active role

            # Check temporal constraints
            is_valid = True
            validity_info = None
            if assignment.start_date or assignment.end_date:
                from datetime import date
                today = date.today()

                if assignment.start_date and today < assignment.start_date:
                    is_valid = False
                    validity_info = f"Starts on {assignment.start_date}"

                if assignment.end_date and today > assignment.end_date:
                    is_valid = False
                    validity_info = f"Expired on {assignment.end_date}"

            roles.append({
                'id': designation.id,
                'name': designation.name,
                'full_name': designation.full_name,
                'type': designation.type,
                'category': designation.category,
                'is_active': is_active,
                'is_valid': is_valid,
                'validity_info': validity_info,
                'start_date': assignment.start_date,
                'end_date': assignment.end_date,
            })

        return Response({
            'roles': roles,
            'total_roles': len(roles)
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            'error': 'Failed to fetch user roles',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@audit_log(action='SWITCH_ROLE', model_name='AuthUser')
def switch_user_role(request):
    """
    Switch the user's active role
    Body: {
        "role_id": 123
    }
    """
    try:
        role_id = request.data.get('role_id')

        if not role_id:
            return Response({
                'error': 'Role ID is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        user = request.user

        # Check if user has this role
        try:
            role_assignment = GlobalsHoldsdesignation.objects.get(
                user=user,
                designation_id=role_id
            )
        except GlobalsHoldsdesignation.DoesNotExist:
            return Response({
                'error': 'You do not have this role'
            }, status=status.HTTP_403_FORBIDDEN)

        # Check if role is valid (temporal constraints)
        from datetime import date
        today = date.today()

        if role_assignment.start_date and today < role_assignment.start_date:
            return Response({
                'error': 'This role has not started yet',
                'detail': f'Role starts on {role_assignment.start_date}'
            }, status=status.HTTP_403_FORBIDDEN)

        if role_assignment.end_date and today > role_assignment.end_date:
            return Response({
                'error': 'This role has expired',
                'detail': f'Role expired on {role_assignment.end_date}'
            }, status=status.HTTP_403_FORBIDDEN)

        # Update session with active role (in a real app, you'd store this in session)
        # For now, we'll return the role info to be stored in frontend
        designation = role_assignment.designation

        return Response({
            'message': 'Role switched successfully',
            'active_role': {
                'id': designation.id,
                'name': designation.name,
                'full_name': designation.full_name,
                'type': designation.type,
            }
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            'error': 'Failed to switch role',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_current_active_role(request):
    """
    Get the currently active role for the user
    This would typically check session storage
    """
    try:
        user = request.user

        # Get primary role (first role or most recently used)
        # In a real implementation, this would check session
        role_assignment = GlobalsHoldsdesignation.objects.filter(
            user=user
        ).select_related('designation').first()

        if not role_assignment:
            return Response({
                'active_role': None,
                'message': 'No active role found'
            }, status=status.HTTP_200_OK)

        designation = role_assignment.designation

        return Response({
            'active_role': {
                'id': designation.id,
                'name': designation.name,
                'full_name': designation.full_name,
                'type': designation.type,
            }
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            'error': 'Failed to fetch active role',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==============================================================================
# EMERGENCY ACCESS ENDPOINTS
# ==============================================================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@audit_log(action='EMERGENCY_ACCESS_REQUEST', model_name='EmergencyAccess')
def request_emergency_access(request):
    """
    Request emergency access to a role
    Body: {
        "role_id": 123,
        "reason": "Need to handle critical incident",
        "duration_hours": 24  # optional, default 24
    }
    """
    try:
        from .models import EmergencyAccess
    except ImportError:
        return Response({
            'error': 'Emergency Access feature not available',
            'detail': 'Table not created yet. Run create_emergency_access_table.py script.'
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    try:
        # Extract data from request
        role_id = request.data.get('role_id')
        reason = request.data.get('reason')
        duration_hours = request.data.get('duration_hours', 24)
        
        print(f"[EMERGENCY ACCESS] Request received - role_id: {role_id}, reason: {reason}")

        # Validation
        if not role_id:
            return Response({
                'error': 'Role ID is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        if not reason or not reason.strip():
            return Response({
                'error': 'Reason is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Check if role exists
        try:
            requested_role = GlobalsDesignation.objects.get(id=role_id)
        except GlobalsDesignation.DoesNotExist:
            return Response({
                'error': 'Role not found'
            }, status=status.HTTP_404_NOT_FOUND)

        # Check if user already has this role
        user = request.user
        if GlobalsHoldsdesignation.objects.filter(user=user, designation=requested_role).exists():
            return Response({
                'error': 'You already have this role',
                'detail': 'Emergency access is not needed for roles you already possess'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Check if there's already a pending or active request for this role
        existing_request = EmergencyAccess.objects.filter(
            requester=user,
            requested_role=requested_role,
            status__in=['PENDING', 'APPROVED', 'ACTIVE']
        ).first()

        if existing_request:
            return Response({
                'error': 'Existing request found',
                'detail': f'You already have a {existing_request.get_status_display()} request for this role'
            }, status=status.HTTP_409_CONFLICT)

        # Create emergency access request
        emergency_access = EmergencyAccess.objects.create(
            requester=user,
            requested_role=requested_role,
            reason=reason.strip(),
            duration_hours=duration_hours,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request)
        )

        return Response({
            'message': 'Emergency access request submitted successfully',
            'request_id': emergency_access.id,
            'status': emergency_access.status,
            'requested_role': {
                'id': requested_role.id,
                'name': requested_role.name,
                'full_name': requested_role.full_name
            },
            'duration_hours': duration_hours
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({
            'error': 'Failed to create emergency access request',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_emergency_access_requests(request):
    """
    List emergency access requests with filtering
    Query params:
    - status: PENDING, APPROVED, ACTIVE, EXPIRED, REVOKED, DENIED
    - requester: username (for filtering specific user)
    - view: 'my-requests' (default) or 'all-requests' (admin only)
    """
    try:
        from .models import EmergencyAccess

        # Get filters
        status_filter = request.query_params.get('status')
        requester_filter = request.query_params.get('requester')
        view_type = request.query_params.get('view', 'my-requests')  # Default to my-requests

        # Build queryset
        queryset = EmergencyAccess.objects.select_related(
            'requester', 'approver', 'requested_role'
        ).order_by('-created_at')

        # Apply status filter
        if status_filter:
            queryset = queryset.filter(status=status_filter.upper())

        # Determine which requests to show based on view type
        if view_type == 'all-requests':
            # Admin-only: Show all requests (for approval dashboard)
            if not request.user.is_superuser and not request.user.is_staff:
                return Response({
                    'error': 'Permission denied',
                    'detail': 'Only administrators can view all requests'
                }, status=status.HTTP_403_FORBIDDEN)
            # Admins can see all requests, but can optionally filter by requester
            if requester_filter:
                queryset = queryset.filter(requester__username=requester_filter)
        else:
            # Default: Show only current user's own requests (for everyone including admins)
            queryset = queryset.filter(requester=request.user)

        requests = queryset[:100]  # Limit to 100 most recent

        request_data = []
        for req in requests:
            request_data.append({
                'id': req.id,
                'requester': {
                    'username': req.requester.username,
                    'email': req.requester.email
                },
                'requested_role': {
                    'id': req.requested_role.id,
                    'name': req.requested_role.name,
                    'full_name': req.requested_role.full_name
                },
                'reason': req.reason,
                'status': req.status,
                'duration_hours': req.duration_hours,
                'created_at': req.created_at.isoformat(),
                'expires_at': req.expires_at.isoformat() if req.expires_at else None,
                'is_active': req.is_active(),
                'reviewer': req.approver.username if req.approver else None,
                'reviewed_at': req.approved_at.isoformat() if req.approved_at else None,
                'approval_action': req.approval_action,
                'approval_reason': req.approval_reason,
                'activated_at': req.activated_at.isoformat() if req.activated_at else None,
                'revoked_at': req.revoked_at.isoformat() if req.revoked_at else None,
                'revoke_reason': req.revoke_reason if hasattr(req, 'revoke_reason') else ''
            })

        return Response({
            'requests': request_data,
            'total': len(request_data)
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            'error': 'Failed to fetch emergency access requests',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])  # In production, restrict to admins only
@audit_log(action='EMERGENCY_ACCESS_APPROVE', model_name='EmergencyAccess')
def approve_emergency_access(request, request_id):
    """
    Approve an emergency access request
    Body: {
        "action": "approve" | "deny",
        "reason": "Approval/denial reason"
    }
    """
    try:
        from .models import EmergencyAccess

        # Only admins can approve (in production, check proper permissions)
        if not request.user.is_staff and not request.user.is_superuser:
            return Response({
                'error': 'Permission denied',
                'detail': 'Only administrators can approve emergency access requests'
            }, status=status.HTTP_403_FORBIDDEN)

        action = request.data.get('action')
        reason = request.data.get('reason', '')

        if action not in ['approve', 'deny']:
            return Response({
                'error': 'Invalid action',
                'detail': 'Action must be either "approve" or "deny"'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Get the request
        try:
            emergency_request = EmergencyAccess.objects.get(id=request_id)
        except EmergencyAccess.DoesNotExist:
            return Response({
                'error': 'Request not found'
            }, status=status.HTTP_404_NOT_FOUND)

        # SECURITY: Prevent admins from approving their own requests
        if emergency_request.requester == request.user:
            return Response({
                'error': 'Self-approval not allowed',
                'detail': 'You cannot approve or deny your own emergency access request. Another administrator must review it.'
            }, status=status.HTTP_403_FORBIDDEN)

        # Check if request can be approved/denied
        if emergency_request.status != 'PENDING':
            return Response({
                'error': 'Request cannot be processed',
                'detail': f'Request status is {emergency_request.get_status_display()}'
            }, status=status.HTTP_400_BAD_REQUEST)

        if action == 'deny':
            emergency_request.status = 'DENIED'
            emergency_request.approver = request.user
            emergency_request.approved_at = timezone.now()
            emergency_request.approval_reason = reason
            emergency_request.save()

            # TRIGGER: Emergency access denied event
            try:
                from .integration_events import trigger_emergency_access_denied
                trigger_emergency_access_denied(
                    emergency_request=emergency_request,
                    reviewer=request.user
                )
            except Exception as e:
                print(f"[INTEGRATION EVENT] Emergency denied trigger failed: {e}")

            return Response({
                'message': 'Emergency access request denied',
                'request_id': emergency_request.id
            }, status=status.HTTP_200_OK)

        # Approve the request
        emergency_request.status = 'APPROVED'
        emergency_request.approver = request.user
        emergency_request.approved_at = timezone.now()
        emergency_request.approval_reason = reason
        emergency_request.save()

        # TRIGGER: Emergency access approved event
        try:
            from .integration_events import trigger_emergency_access_approved
            trigger_emergency_access_approved(
                emergency_request=emergency_request,
                approver=request.user
            )
        except Exception as e:
            print(f"[INTEGRATION EVENT] Emergency approved trigger failed: {e}")

        return Response({
            'message': 'Emergency access request approved',
            'request_id': emergency_request.id,
            'status': 'APPROVED',
            'note': 'Request must be activated by the requester to become active'
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            'error': 'Failed to process emergency access request',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@audit_log(action='EMERGENCY_ACCESS_ACTIVATE', model_name='EmergencyAccess')
def activate_emergency_access(request, request_id):
    """
    Activate an approved emergency access request
    This starts the temporary access period
    """
    try:
        from .models import EmergencyAccess

        # Get the request
        try:
            emergency_request = EmergencyAccess.objects.get(id=request_id)
        except EmergencyAccess.DoesNotExist:
            return Response({
                'error': 'Request not found'
            }, status=status.HTTP_404_NOT_FOUND)

        # Security: Only requester can activate their own request
        if emergency_request.requester != request.user:
            return Response({
                'error': 'Permission denied',
                'detail': 'You can only activate your own emergency access requests'
            }, status=status.HTTP_403_FORBIDDEN)

        # Check if request can be activated
        if emergency_request.status != 'APPROVED':
            return Response({
                'error': 'Request cannot be activated',
                'detail': f'Request status is {emergency_request.get_status_display()}'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Activate the emergency access
        emergency_request.status = 'ACTIVE'
        emergency_request.activated_at = timezone.now()
        
        # Calculate expiration time
        from datetime import timedelta
        if not emergency_request.expires_at:
            emergency_request.expires_at = emergency_request.activated_at + timedelta(hours=emergency_request.duration_hours)
        
        emergency_request.save()

        # Grant the role temporarily - check if already exists first
        existing_role = GlobalsHoldsdesignation.objects.filter(
            user=emergency_request.requester,
            designation=emergency_request.requested_role
        ).first()
        
        if not existing_role:
            GlobalsHoldsdesignation.objects.create(
                user=emergency_request.requester,
                designation=emergency_request.requested_role,
                working=emergency_request.requester
            )

        # TRIGGER: Emergency access activated event
        try:
            from .integration_events import trigger_emergency_access_activated
            trigger_emergency_access_activated(
                emergency_request=emergency_request
            )
        except Exception as e:
            print(f"[INTEGRATION EVENT] Emergency activated trigger failed: {e}")

        return Response({
            'message': 'Emergency access activated successfully',
            'request_id': emergency_request.id,
            'status': 'ACTIVE',
            'expires_at': emergency_request.expires_at.isoformat(),
            'duration_hours': emergency_request.duration_hours,
            'role': {
                'id': emergency_request.requested_role.id,
                'name': emergency_request.requested_role.name,
                'full_name': emergency_request.requested_role.full_name
            }
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            'error': 'Failed to activate emergency access',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@audit_log(action='EMERGENCY_ACCESS_REVOKE', model_name='EmergencyAccess')
def revoke_emergency_access(request, request_id):
    """
    Revoke an active emergency access
    Body: {
        "reason": "Reason for revocation"
    }
    """
    try:
        from .models import EmergencyAccess

        reason = request.data.get('reason', '')

        # Get the request
        try:
            emergency_request = EmergencyAccess.objects.get(id=request_id)
        except EmergencyAccess.DoesNotExist:
            return Response({
                'error': 'Request not found'
            }, status=status.HTTP_404_NOT_FOUND)

        # Security: Only approver (admin) or requester can revoke
        if (emergency_request.requester != request.user and
            emergency_request.approver != request.user and
            not request.user.is_superuser):
            return Response({
                'error': 'Permission denied',
                'detail': 'Only requester, approver, or superuser can revoke'
            }, status=status.HTTP_403_FORBIDDEN)

        # Check if request is active
        if emergency_request.status != 'ACTIVE':
            return Response({
                'error': 'Request is not active',
                'detail': f'Cannot revoke {emergency_request.get_status_display()} request'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Revoke the emergency access
        emergency_request.status = 'REVOKED'
        emergency_request.revoked_at = timezone.now()
        if reason:
            emergency_request.approval_reason = reason
        emergency_request.save()

        # Remove the temporary role assignment
        GlobalsHoldsdesignation.objects.filter(
            user=emergency_request.requester,
            designation=emergency_request.requested_role
        ).delete()

        # TRIGGER: Emergency access revoked event
        try:
            from .integration_events import trigger_emergency_access_revoked
            trigger_emergency_access_revoked(
                emergency_request=emergency_request,
                revoked_by=request.user,
                reason=reason
            )
        except Exception as e:
            print(f"[INTEGRATION EVENT] Emergency revoked trigger failed: {e}")

        return Response({
            'message': 'Emergency access revoked successfully',
            'request_id': emergency_request.id,
            'status': 'REVOKED'
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            'error': 'Failed to revoke emergency access',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_expired_emergency_access(request):
    """
    Check and automatically expire any emergency access that has passed its end time
    """
    try:
        expired_requests = EmergencyAccess.objects.filter(
            status='ACTIVE',
            access_end_time__lt=timezone.now()
        )
        
        count = expired_requests.count()
        
        # Auto-expire them
        for emergency_request in expired_requests:
            emergency_request.status = 'EXPIRED'
            emergency_request.save()
        
        return Response({
            'message': f'Found and expired {count} emergency access requests',
            'expired_count': count
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response({
            'error': 'Failed to check expired emergency access',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== HANDOVER DOCUMENTATION VIEWS ====================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_handover_documents(request):
    """
    List all handover documents with filtering
    """
    try:
        handovers = HandoverDocumentation.objects.all()
        
        # Filter by user
        user_filter = request.query_params.get('user')
        if user_filter:
            handovers = handovers.filter(
                Q(from_user__username__icontains=user_filter) |
                Q(to_user__username__icontains=user_filter)
            )
        
        # Filter by status
        status_filter = request.query_params.get('status')
        if status_filter:
            handovers = handovers.filter(status=status_filter)
        
        serializer = HandoverDocumentationSerializer(handovers, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response({
            'error': 'Failed to retrieve handover documents',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_handover_document(request):
    """
    Create a new handover document
    """
    try:
        data = request.data.copy()
        data['from_user'] = request.user.id
        
        serializer = HandoverDocumentationSerializer(data=data)
        if serializer.is_valid():
            handover = serializer.save()
            return Response({
                'message': 'Handover document created successfully',
                'data': HandoverDocumentationSerializer(handover).data
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        return Response({
            'error': 'Failed to create handover document',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def accept_handover(request, handover_id):
    """
    Accept a handover document
    """
    try:
        handover = HandoverDocumentation.objects.get(id=handover_id)
        
        if handover.to_user != request.user:
            return Response({
                'error': 'Only the assigned user can accept this handover'
            }, status=status.HTTP_403_FORBIDDEN)
        
        if handover.status != 'PENDING':
            return Response({
                'error': 'Handover cannot be accepted in current status'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        handover.status = 'IN_PROGRESS'
        handover.accepted_at = timezone.now()
        handover.to_user_confirmation = True
        handover.save()
        
        return Response({
            'message': 'Handover accepted successfully',
            'data': HandoverDocumentationSerializer(handover).data
        }, status=status.HTTP_200_OK)
    
    except HandoverDocumentation.DoesNotExist:
        return Response({
            'error': 'Handover document not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    except Exception as e:
        return Response({
            'error': 'Failed to accept handover',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def complete_handover(request, handover_id):
    """
    Mark a handover as complete
    """
    try:
        handover = HandoverDocumentation.objects.get(id=handover_id)
        
        # Check permissions
        if handover.from_user != request.user and handover.to_user != request.user:
            return Response({
                'error': 'You do not have permission to complete this handover'
            }, status=status.HTTP_403_FORBIDDEN)
        
        if handover.status != 'IN_PROGRESS':
            return Response({
                'error': 'Handover must be in progress to be completed'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        handover.status = 'COMPLETED'
        handover.completed_at = timezone.now()
        handover.progress_percentage = 100
        handover.save()
        
        return Response({
            'message': 'Handover completed successfully',
            'data': HandoverDocumentationSerializer(handover).data
        }, status=status.HTTP_200_OK)
    
    except HandoverDocumentation.DoesNotExist:
        return Response({
            'error': 'Handover document not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    except Exception as e:
        return Response({
            'error': 'Failed to complete handover',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cancel_handover(request, handover_id):
    """
    Cancel a handover document
    """
    try:
        handover = HandoverDocumentation.objects.get(id=handover_id)
        
        # Only from_user or supervisor can cancel
        if handover.from_user != request.user and handover.supervisor != request.user:
            return Response({
                'error': 'You do not have permission to cancel this handover'
            }, status=status.HTTP_403_FORBIDDEN)
        
        if handover.status in ['COMPLETED', 'CANCELLED']:
            return Response({
                'error': 'Cannot cancel handover in current status'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        handover.status = 'CANCELLED'
        handover.save()
        
        return Response({
            'message': 'Handover cancelled successfully',
            'data': HandoverDocumentationSerializer(handover).data
        }, status=status.HTTP_200_OK)
    
    except HandoverDocumentation.DoesNotExist:
        return Response({
            'error': 'Handover document not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    except Exception as e:
        return Response({
            'error': 'Failed to cancel handover',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

