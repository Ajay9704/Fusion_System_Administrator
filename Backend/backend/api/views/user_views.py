"""
User Management Views - Handles user creation, role management, and user operations
Extracted from the monolithic views.py for enterprise architecture
"""

import logging
from datetime import datetime
from django.conf import settings

from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser

from ..models import (
    AuthUser, GlobalsExtrainfo, GlobalsDesignation, GlobalsHoldsdesignation,
    GlobalsDepartmentinfo, Student, Staff, GlobalsFaculty, Batch
)
from ..serializers import (
    AuthUserSerializer, GlobalExtraInfoSerializer, StudentSerializer,
    GlobalsFacultySerializer, StaffSerializer, GlobalsDepartmentinfoSerializer
)
from ..helpers import (
    create_password, send_email, configure_password_mail,
    add_user_extra_info, add_user_designation_info, add_student_info,
    generate_student_username, generate_staff_faculty_username
)
from ..audit import audit_log, create_audit_log, get_client_ip, get_user_agent

# Configure logger
logger = logging.getLogger('system_admin')


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_role_by_username(request):
    """Get user information and their assigned roles"""
    username = request.query_params.get('username')

    if not username:
        return Response({
            "error": "Username parameter is required"
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = AuthUser.objects.get(username__iexact=username)
        holds_designation_entries = GlobalsHoldsdesignation.objects.filter(user=user)

        if not holds_designation_entries.exists():
            return Response({
                "error": "User has no designations."
            }, status=status.HTTP_404_NOT_FOUND)

        designation_ids = [entry.designation_id for entry in holds_designation_entries]

        roles = GlobalsDesignation.objects.filter(id__in=designation_ids)

        return Response({
            "user": AuthUserSerializer(user).data,
            "roles": [role.name for role in roles],
        }, status=status.HTTP_200_OK)

    except AuthUser.DoesNotExist:
        return Response({
            "error": "User not found"
        }, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        return Response({
            "error": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
@audit_log(action='UPDATE_USER_ROLES', model_name='GlobalsHoldsdesignation')
def update_user_roles(request):
    """Update user roles with validation and conflict checking"""
    username = request.data.get('username')
    roles_to_add = request.data.get('roles', [])

    if not username or not roles_to_add:
        return Response({
            "error": "Username and roles are required."
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        from ..helpers import check_role_conflicts

        user = AuthUser.objects.get(username__iexact=username)

        # Process roles_to_add - handle both dict and string formats
        processed_roles = set()
        for role in roles_to_add:
            if isinstance(role, dict) and 'name' in role:
                processed_roles.add(role['name'])
            elif isinstance(role, str):
                processed_roles.add(role)

        # Validate and assign roles
        for role_name in processed_roles:
            try:
                designation = GlobalsDesignation.objects.get(name=role_name)

                # Check role conflicts
                conflicts = check_role_conflicts(user.id, designation.id)
                if conflicts:
                    return Response({
                        "error": f"Role conflicts detected: {', '.join(conflicts)}",
                        "conflicting_roles": conflicts
                    }, status=status.HTTP_403_FORBIDDEN)

                # Check singular role constraint
                if designation.is_singular:
                    other_users_with_role = GlobalsHoldsdesignation.objects.filter(
                        designation=designation
                    ).exclude(user=user)

                    if other_users_with_role.exists():
                        other_user = other_users_with_role.first().user
                        return Response({
                            "error": f"Role '{role_name}' is a singular role.",
                            "current_holder": other_user.username
                        }, status=status.HTTP_403_FORBIDDEN)

                # Check if already has this role
                if not GlobalsHoldsdesignation.objects.filter(user=user, designation=designation).exists():
                    GlobalsHoldsdesignation.objects.create(
                        user=user,
                        designation=designation,
                        working=user.id,
                        start_date=request.data.get(f'start_date_{role_name}'),
                        end_date=request.data.get(f'end_date_{role_name}')
                    )

            except GlobalsDesignation.DoesNotExist:
                return Response({
                    "error": f"Role '{role_name}' not found"
                }, status=status.HTTP_404_NOT_FOUND)

        return Response({
            "message": "User roles updated successfully."
        }, status=status.HTTP_200_OK)

    except AuthUser.DoesNotExist:
        return Response({
            "error": "User not found"
        }, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        return Response({
            "error": f"Failed to update user roles: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_individual_student(request):
    """Create individual student with comprehensive validation and detailed error messages"""
    # Username is optional - will be auto-generated if not provided
    required_fields = ["first_name", "last_name", "sex", "category",
                      "father_name", "mother_name", "batch", "programme", "department"]

    # Log the incoming request data for debugging
    logger.info(f"Student creation attempt with data: {request.data}")

    data = request.data.copy()

    # Map frontend field names to backend expected names
    field_mappings = {
        'rollNumber': 'username', 'roll_number': 'username',
        'firstName': 'first_name', 'lastName': 'last_name', 'gender': 'sex',
        'fatherName': 'father_name', 'motherName': 'mother_name',
        'email': 'personal_email', 'personalEmail': 'personal_email',
        'phoneNumber': 'phone', 'dateOfBirth': 'dob', 'address': 'address'
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

    # Auto-generate roll number if not provided or empty
    if not data.get('username') or not str(data.get('username', '')).strip():
        # Generate username using the helper function
        try:
            data['username'] = generate_student_username(data)
            logger.info(f"Auto-generated username: {data['username']}")
        except Exception as e:
            logger.error(f"Failed to generate username: {str(e)}")
            return Response({
                "error": "Username generation failed",
                "message": "Could not automatically generate roll number. Please provide one manually.",
                "suggestion": "Ensure batch, programme, and department are correctly selected, or provide a roll number manually."
            }, status=status.HTTP_400_BAD_REQUEST)
    else:
        data['username'] = str(data['username']).strip().upper()

    # Enhanced validation with detailed error messages
    validation_errors = {}

    # Check for missing required fields
    missing_fields = []
    for field in required_fields:
        if field not in data or not str(data[field]).strip():
            missing_fields.append(field)

    if missing_fields:
        validation_errors['missing_fields'] = missing_fields
        validation_errors['non_field_errors'] = [f"The following required fields are empty: {', '.join(missing_fields)}"]
        logger.warning(f"Missing required fields: {missing_fields}")

    # Validate batch is a valid number
    if 'batch' in data:
        try:
            batch_value = int(data['batch'])
            current_year = datetime.now().year
            if batch_value < 2000 or batch_value > current_year + 5:
                validation_errors['batch'] = f"Batch year must be between 2000 and {current_year + 5}"
        except (ValueError, TypeError):
            validation_errors['batch'] = "Batch must be a valid year (e.g., 2023)"

    # Validate department exists
    if 'department' in data:
        try:
            department_id = int(data['department'])
            if not GlobalsDepartmentinfo.objects.filter(id=department_id).exists():
                validation_errors['department'] = f"Department with ID {department_id} does not exist"
        except (ValueError, TypeError):
            validation_errors['department'] = "Department must be a valid ID"

    # Validate programme
    valid_programmes = ['B.Tech', 'M.Tech', 'Ph.D', 'PhD', 'B.Des', 'M.Des']
    if 'programme' in data and data['programme'] not in valid_programmes:
        validation_errors['programme'] = f"Programme must be one of: {', '.join(valid_programmes)}"

    # Validate category
    valid_categories = ['GEN', 'OBC', 'SC', 'ST', 'EWS', 'GEN-EWS']
    if 'category' in data and data['category'] not in valid_categories:
        validation_errors['category'] = f"Category must be one of: {', '.join(valid_categories)}"

    # Validate gender
    valid_genders = ['M', 'F', 'O']
    if 'sex' in data and data['sex'] not in valid_genders:
        validation_errors['sex'] = "Gender must be Male (M), Female (F), or Other (O)"

    # Validate email format if provided
    if 'personal_email' in data and data['personal_email']:
        email = data['personal_email'].strip()
        if '@' not in email or '.' not in email.split('@')[1]:
            validation_errors['personal_email'] = "Please provide a valid email address"

    # Return validation errors if any
    if validation_errors:
        return Response({
            "error": "Validation failed",
            "message": "Please correct the following errors:",
            "validation_errors": validation_errors
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Check if user already exists
        if AuthUser.objects.filter(username=data['username']).exists():
            return Response({
                "error": "Duplicate User",
                "message": f"A student with roll number '{data['username']}' already exists in the system",
                "field": "username",
                "suggestion": "Either leave the roll number field empty to auto-generate, or use a different roll number"
            }, status=status.HTTP_409_CONFLICT)

        # Create user with extended info
        user_response = create_user_with_extrainfo(data, 'student')
        if 'error' in user_response:
            error_detail = user_response['error']
            if isinstance(error_detail, dict):
                # Format validation errors from serializer
                formatted_errors = {}
                for field, error in error_detail.items():
                    if isinstance(error, list):
                        formatted_errors[field] = ' '.join(str(e) for e in error)
                    else:
                        formatted_errors[field] = str(error)

                return Response({
                    "error": "Validation failed",
                    "message": "Please correct the following errors:",
                    "validation_errors": formatted_errors
                }, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({
                    "error": "Creation failed",
                    "message": str(error_detail)
                }, status=status.HTTP_400_BAD_REQUEST)

        user = user_response['user']
        extrainfo = user_response['extrainfo']

        # Add student specific information
        student_response = add_student_info(data, extrainfo)
        if not student_response:
            # Rollback user creation
            user.delete()
            extrainfo.delete()
            return Response({
                "error": "Student record creation failed",
                "message": "Failed to create student academic record. Please verify all academic information is correct.",
                "suggestion": "Ensure batch, programme, and department are correctly selected"
            }, status=status.HTTP_400_BAD_REQUEST)

        # Assign student role
        add_user_designation_info(user.id, 'student')

        # Send password email
        password = data.get('password', create_password(8))
        try:
            configure_password_mail(user.username, password)
        except Exception as email_error:
            # Log email error but don't fail the creation
            logger.warning(f"Failed to send password email for {user.username}: {str(email_error)}")

        return Response({
            "message": "Student created successfully",
            "username": user.username,
            "user_id": user.id,
            "details": {
                "name": f"{user.first_name} {user.last_name}",
                "roll_number": user.username,
                "programme": data.get('programme'),
                "batch": data.get('batch'),
                "email_sent": True
            }
        }, status=status.HTTP_201_CREATED)

    except GlobalsDepartmentinfo.DoesNotExist:
        return Response({
            "error": "Invalid department",
            "message": "The selected department does not exist in the system",
            "suggestion": "Please refresh the page and try again, or contact the administrator"
        }, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        logger.error(f"Unexpected error creating student: {str(e)}", exc_info=True)
        return Response({
            "error": "System error",
            "message": "An unexpected error occurred while creating the student",
            "details": str(e) if settings.DEBUG else "Please contact the administrator if this problem persists"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_individual_staff(request):
    """Create individual staff member with validation"""
    required_fields = ["username", "first_name", "last_name", "sex", "department"]
    data = request.data.copy()

    # Map frontend field names
    field_mappings = {
        'firstName': 'first_name', 'lastName': 'last_name', 'gender': 'sex',
        'email': 'personal_email', 'phoneNumber': 'phone'
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

    # Auto-generate username if not provided
    if not data.get('username') or not str(data['username']).strip():
        data['username'] = generate_staff_faculty_username(data)
    else:
        data['username'] = str(data['username']).strip()

    missing_fields = [field for field in required_fields if field not in data or not data[field]]
    if missing_fields:
        return Response({
            "error": f"Missing required fields: {', '.join(missing_fields)}"
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Check if user already exists
        if AuthUser.objects.filter(username=data['username']).exists():
            return Response({
                "error": "User with this username already exists"
            }, status=status.HTTP_400_BAD_REQUEST)

        # Create user with extended info
        user_response = create_user_with_extrainfo(data, 'staff')
        if 'error' in user_response:
            return Response(user_response, status=status.HTTP_400_BAD_REQUEST)

        user = user_response['user']
        extrainfo = user_response['extrainfo']

        # Create staff record
        Staff.objects.create(id=extrainfo)

        # Assign staff role
        add_user_designation_info(user.id, 'staff')

        # Send credentials email
        password = data.get('password', create_password(8))
        configure_password_mail(user.username, password)

        return Response({
            "message": "Staff created successfully",
            "username": user.username,
            "user_id": user.id
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({
            "error": f"Failed to create staff: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_individual_faculty(request):
    """Create individual faculty member with comprehensive validation and detailed error messages"""
    # Username is optional - will be auto-generated if not provided
    required_fields = ["first_name", "last_name", "sex", "department", "designation"]

    # Log the incoming request data for debugging
    logger.info(f"Faculty creation attempt with data: {request.data}")

    data = request.data.copy()

    # Map frontend field names
    field_mappings = {
        'firstName': 'first_name', 'lastName': 'last_name', 'gender': 'sex',
        'email': 'personal_email', 'phoneNumber': 'phone'
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

    # Auto-generate username if not provided or empty
    if not data.get('username') or not str(data.get('username', '')).strip():
        # Generate username using the helper function
        try:
            data['username'] = generate_staff_faculty_username(data)
            logger.info(f"Auto-generated faculty username: {data['username']}")
        except Exception as e:
            logger.error(f"Failed to generate faculty username: {str(e)}")
            return Response({
                "error": "Username generation failed",
                "message": "Could not automatically generate username. Please provide one manually.",
                "suggestion": "Ensure department and designation are correctly selected, or provide a username manually."
            }, status=status.HTTP_400_BAD_REQUEST)
    else:
        data['username'] = str(data['username']).strip().lower()

    # Enhanced validation with detailed error messages
    validation_errors = {}

    # Check for missing required fields
    missing_fields = []
    for field in required_fields:
        if field not in data or not str(data[field]).strip():
            missing_fields.append(field)

    if missing_fields:
        validation_errors['missing_fields'] = missing_fields
        validation_errors['non_field_errors'] = [f"The following required fields are empty: {', '.join(missing_fields)}"]
        logger.warning(f"Missing required fields for faculty: {missing_fields}")

    # Validate department exists
    if 'department' in data:
        try:
            department_id = int(data['department'])
            if not GlobalsDepartmentinfo.objects.filter(id=department_id).exists():
                validation_errors['department'] = f"Department with ID {department_id} does not exist"
        except (ValueError, TypeError):
            validation_errors['department'] = "Department must be a valid ID"

    # Validate designation exists
    if 'designation' in data:
        try:
            designation_id = int(data['designation'])
            if not GlobalsDesignation.objects.filter(id=designation_id).exists():
                validation_errors['designation'] = f"Designation with ID {designation_id} does not exist"
        except (ValueError, TypeError):
            validation_errors['designation'] = "Designation must be a valid ID"

    # Validate gender
    valid_genders = ['M', 'F', 'O']
    if 'sex' in data and data['sex'] not in valid_genders:
        validation_errors['sex'] = "Gender must be Male (M), Female (F), or Other (O)"

    # Validate email format if provided
    if 'personal_email' in data and data['personal_email']:
        email = data['personal_email'].strip()
        if '@' not in email or '.' not in email.split('@')[1]:
            validation_errors['personal_email'] = "Please provide a valid email address"

    # Return validation errors if any
    if validation_errors:
        return Response({
            "error": "Validation failed",
            "message": "Please correct the following errors:",
            "validation_errors": validation_errors
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Check if user already exists
        if AuthUser.objects.filter(username=data['username']).exists():
            return Response({
                "error": "Duplicate User",
                "message": f"A faculty member with username '{data['username']}' already exists in the system",
                "field": "username",
                "suggestion": "Either leave the username field empty to auto-generate, or use a different username"
            }, status=status.HTTP_409_CONFLICT)

        # Create user with extended info
        user_response = create_user_with_extrainfo(data, 'faculty')
        if 'error' in user_response:
            error_detail = user_response['error']
            if isinstance(error_detail, dict):
                # Format validation errors from serializer
                formatted_errors = {}
                for field, error in error_detail.items():
                    if isinstance(error, list):
                        formatted_errors[field] = ' '.join(str(e) for e in error)
                    else:
                        formatted_errors[field] = str(error)

                return Response({
                    "error": "Validation failed",
                    "message": "Please correct the following errors:",
                    "validation_errors": formatted_errors
                }, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({
                    "error": "Creation failed",
                    "message": str(error_detail)
                }, status=status.HTTP_400_BAD_REQUEST)

        user = user_response['user']
        extrainfo = user_response['extrainfo']

        # Create faculty record
        GlobalsFaculty.objects.create(id=extrainfo)

        # Assign designation/role
        designation_id = data.get('designation')
        if designation_id:
            try:
                GlobalsHoldsdesignation.objects.create(
                    user=user,
                    designation_id=int(designation_id),
                    working=user.id
                )
            except Exception as designation_error:
                logger.error(f"Failed to assign designation: {str(designation_error)}")
                # Continue anyway, faculty is created

        # Send credentials email
        password = data.get('password', create_password(8))
        try:
            configure_password_mail(user.username, password)
        except Exception as email_error:
            # Log email error but don't fail the creation
            logger.warning(f"Failed to send password email for {user.username}: {str(email_error)}")

        return Response({
            "message": "Faculty created successfully",
            "username": user.username,
            "user_id": user.id,
            "details": {
                "name": f"{user.first_name} {user.last_name}",
                "username": user.username,
                "email_sent": True
            }
        }, status=status.HTTP_201_CREATED)

    except GlobalsDepartmentinfo.DoesNotExist:
        return Response({
            "error": "Invalid department",
            "message": "The selected department does not exist in the system",
            "suggestion": "Please refresh the page and try again, or contact the administrator"
        }, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        logger.error(f"Unexpected error creating faculty: {str(e)}", exc_info=True)
        return Response({
            "error": "System error",
            "message": "An unexpected error occurred while creating the faculty member",
            "details": str(e) if settings.DEBUG else "Please contact the administrator if this problem persists"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@audit_log(action='RESET_PASSWORD', model_name='AuthUser')
def reset_password(request):
    """Reset user password with proper validation"""
    username = request.data.get('username')
    new_password = request.data.get('new_password')

    if not username or not new_password:
        return Response({
            "error": "Username and new password are required"
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = AuthUser.objects.get(username__iexact=username)
        user.set_password(new_password)
        user.save()

        # Log the action
        create_audit_log(
            user=request.user,
            action='PASSWORD_RESET',
            model_name='AuthUser',
            object_id=str(user.id),
            description=f"Password reset for user {user.username}",
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
            status='SUCCESS'
        )

        # Send notification email
        try:
            subject = 'Your Password has been reset!!'
            message = f"This Mail is to notify you that your password has been reset by the System Administrator.\n\nPlease check out the new password below:  {new_password}\n\nRegards,\nSystem Administrator,\nIIITDM Jabalpur."
            recipient_list = [user.email]
            send_email(subject=subject, message=message, recipient_list=recipient_list)
        except Exception as e:
            print(f"[ERROR] Failed to send password email: {e}")

        return Response({
            "message": "Password reset successfully."
        }, status=status.HTTP_200_OK)

    except AuthUser.DoesNotExist:
        return Response({
            "error": "User not found"
        }, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        return Response({
            "error": f"Failed to reset password: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@audit_log(action='ARCHIVE_USER', model_name='AuthUser')
def archive_user(request, username):
    """Archive user account (soft delete)"""
    try:
        user = AuthUser.objects.get(username__iexact=username)

        if not user.is_active:
            return Response({
                "error": "User is already archived"
            }, status=status.HTTP_400_BAD_REQUEST)

        # Soft delete by setting is_active to False
        user.is_active = False
        user.save()

        return Response({
            "message": f"User {username} archived successfully"
        }, status=status.HTTP_200_OK)

    except AuthUser.DoesNotExist:
        return Response({
            "error": "User not found"
        }, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        return Response({
            "error": f"Failed to archive user: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@audit_log(action='RESTORE_USER', model_name='AuthUser')
def restore_user(request, username):
    """Restore archived user account"""
    try:
        user = AuthUser.objects.get(username__iexact=username)

        if user.is_active:
            return Response({
                "error": "User is already active"
            }, status=status.HTTP_400_BAD_REQUEST)

        # Reactivate user
        user.is_active = True
        user.save()

        return Response({
            "message": f"User {username} restored successfully"
        }, status=status.HTTP_200_OK)

    except AuthUser.DoesNotExist:
        return Response({
            "error": "User not found"
        }, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        return Response({
            "error": f"Failed to restore user: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserListView(APIView):
    """List users with filtering and pagination"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get users with optional filtering by type"""
        user_type = request.query_params.get('type')

        if user_type == 'student':
            from ..serializers import ViewStudentsWithFiltersSerializer
            queryset = Student.objects.all()
            serializer = ViewStudentsWithFiltersSerializer(queryset, many=True)
        elif user_type == 'staff':
            from ..serializers import ViewStaffWithFiltersSerializer
            queryset = Staff.objects.all()
            serializer = ViewStaffWithFiltersSerializer(queryset, many=True)
        elif user_type == 'faculty':
            from ..serializers import ViewFacultyWithFiltersSerializer
            queryset = GlobalsFaculty.objects.all()
            serializer = ViewFacultyWithFiltersSerializer(queryset, many=True)
        else:
            return Response({
                "error": "Invalid user type. Use 'student', 'staff', or 'faculty'"
            }, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.data, status=status.HTTP_200_OK)


# Helper function for user creation
def create_user_with_extrainfo(data, user_type):
    """Helper function to create user with extended info"""
    try:
        # Create Django user
        user = AuthUser.objects.create_user(
            username=data['username'],
            email=data.get('email', data.get('personal_email', f"{data['username']}@iiitdmj.ac.in")),
            first_name=data.get('first_name', ''),
            last_name=data.get('last_name', ''),
            password=data.get('password', create_password(8))
        )

        # Get department
        try:
            department = GlobalsDepartmentinfo.objects.get(id=data['department'])
        except GlobalsDepartmentinfo.DoesNotExist:
            department = GlobalsDepartmentinfo.objects.get(name=data['department'])

        # Create extended info
        extrainfo_data = {
            'id': data['username'],
            'user': user.id,
            'title': data.get('title', 'Mr.' if data.get('sex') == 'M' else 'Ms.'),
            'sex': data.get('sex', 'M'),
            'date_of_birth': data.get('dob') or data.get('date_of_birth') or '2000-01-01',
            'user_status': 'PRESENT',
            'address': data.get('address', 'N/A'),
            'phone_no': data.get('phone') or data.get('phone_number') or 1234567890,
            'user_type': user_type,
            'profile_picture': data.get('profile_picture'),
            'about_me': data.get('about_me', f'{user_type.capitalize()}'),
            'department': department.id
        }

        extrainfo_serializer = GlobalExtraInfoSerializer(data=extrainfo_data)
        if extrainfo_serializer.is_valid():
            extrainfo = extrainfo_serializer.save()
        else:
            user.delete()
            return {'error': extrainfo_serializer.errors}

        return {
            'user': user,
            'extrainfo': extrainfo
        }

    except Exception as e:
        return {'error': str(e)}