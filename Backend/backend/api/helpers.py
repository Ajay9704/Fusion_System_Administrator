from rest_framework.response import Response
from rest_framework import status
import concurrent.futures
import random
import re
import string
from django.contrib.auth.hashers import make_password
from django.core.mail import send_mail
from django.conf import settings
from datetime import datetime
from .models import (
    GlobalsDepartmentinfo, Batch, GlobalsDesignation, AuthUser,
    GlobalsHoldsdesignation
)
from .serializers import GlobalExtraInfoSerializer, GlobalsHoldsDesignationSerializer, StudentSerializer
import os

def normalize_username(username):
    if not username:
        return ''
    value = username.strip().lower()
    value = re.sub(r'[^a-z0-9_.-]', '', value)
    return value


def format_college_email(username):
    return f"{normalize_username(username)}@iiitdmj.ac.in"


def generate_student_username(data):
    existing_username = data.get('username')
    if existing_username and existing_username.strip():
        return existing_username.strip().upper()

    batch = str(data.get('batch') or datetime.now().year)
    yy = batch[-2:]  # last 2 digits of year e.g. "23"

    programme = (data.get('programme') or 'B.Tech').strip()
    department_id = data.get('department')

    # Resolve department name from ID
    dept_name = ''
    if department_id:
        try:
            dept_name = GlobalsDepartmentinfo.objects.get(id=department_id).name
        except GlobalsDepartmentinfo.DoesNotExist:
            dept_name = ''

    # Build the prefix code matching the institute's roll number convention:
    # B.Tech  → B + dept_code  (BCS, BEC, BME, BSM, BMT, BME for Mechatronics)
    # B.Des   → BDS
    # M.Tech  → M + dept_code  (MCS, MEC, MMET for MT)
    # M.Des   → MDS
    # Ph.D    → P + dept_code  (PCS, PEC)
    BTECH_DEPT_CODES = {
        'CSE': 'BCS',
        'ECE': 'BEC',
        'ME':  'BME',
        'SM':  'BSM',
        'MT':  'BMT',
        'Mechatronics': 'BME',
        'Design': 'BDS',
    }
    MTECH_DEPT_CODES = {
        'CSE': 'MCS',
        'ECE': 'MEC',
        'MT':  'MMET',
        'ME':  'MME',
    }
    PHD_DEPT_CODES = {
        'CSE': 'PCS',
        'ECE': 'PEC',
    }

    if programme == 'B.Tech':
        code = BTECH_DEPT_CODES.get(dept_name, 'BCS')
    elif programme == 'B.Des':
        code = 'BDS'
    elif programme == 'M.Tech':
        code = MTECH_DEPT_CODES.get(dept_name, 'MCS')
    elif programme == 'M.Des':
        code = 'MDS'
    elif programme in ('Ph.D', 'PhD'):
        code = PHD_DEPT_CODES.get(dept_name, 'PCS')
    else:
        # fallback
        code = 'BCS'

    prefix = f"{yy}{code}"

    # Find the highest existing sequence number for this prefix
    existing = AuthUser.objects.filter(username__iregex=rf'^{prefix}\d+$').values_list('username', flat=True)
    nums = []
    for u in existing:
        suffix = u[len(prefix):]
        if suffix.isdigit():
            nums.append(int(suffix))
    next_num = max(nums, default=0) + 1

    # Pad to 3 digits (e.g. 001, 012, 123) — matches institute format
    return f"{prefix}{next_num:03d}"


def generate_staff_faculty_username(data):
    existing_username = data.get('username')
    if existing_username and existing_username.strip():
        return normalize_username(existing_username)

    first = data.get('first_name', '').strip().lower()
    last = data.get('last_name', '').strip().lower()
    if first and last:
        base_username = f"{first}.{last}"
    elif first:
        base_username = first
    elif last:
        base_username = last
    else:
        base_username = 'user'

    base_username = normalize_username(base_username)
    existing_usernames = set(AuthUser.objects.filter(username__istartswith=base_username).values_list('username', flat=True))
    if base_username not in existing_usernames:
        return base_username

    suffix = 1
    while f"{base_username}{suffix}" in existing_usernames:
        suffix += 1
    return f"{base_username}{suffix}"


def create_password(data):
    base = ''
    if data.get('username'):
        base = normalize_username(data['username'])
    elif data.get('first_name'):
        base = normalize_username(data['first_name'])
    else:
        base = 'fusion'
    base = base[:8].capitalize() or 'Fusion'
    special_characters = string.punctuation
    random_specials = ''.join(random.choice(special_characters) for _ in range(3))
    random_digits = ''.join(random.choice(string.digits) for _ in range(2))
    return f"{base}{random_digits}{random_specials}"


def create_password_from_authuser(student):
    special_characters = string.punctuation
    random_specials = "".join(random.choice(special_characters) for _ in range(2))
    roll_no = student.email[5:-14].upper()
    password = f"{student.first_name.lower().capitalize().split(' ')[0]}{roll_no}{random_specials}"
    hashed_password = make_password(password)
    return password, hashed_password


def save_password(student, hashed_password):
    student.password = hashed_password
    student.save()


def send_email(
    subject,
    message,
    from_email=settings.EMAIL_HOST_USER,
    recipient_list=[
        settings.EMAIL_TEST_USER,
    ],
):
    if not from_email:
        return Response(
            {"error": "No sender email provided."}, status=status.HTTP_400_BAD_REQUEST
        )
    try:
        send_mail(subject, message, from_email, recipient_list)
    except Exception as e:
        print(e)
        raise e

def configure_password_mail(students):
    count = len(students)
    if int(settings.EMAIL_TEST_MODE) == 1 :
        count = int(settings.EMAIL_TEST_COUNT)
    
    try:
        for student in students[:count]:
            plain_password, hashed_password = create_password_from_authuser(student)
            save_password(student, hashed_password)
            # save_password(student, make_password("user@123"))
            try:
                mail_to_user_single(student, plain_password)
            except Exception as e:
                log_failed_email(student, plain_password, hashed_password, str(e))
                
        return Response(
            {"message": "Email sent successfully."}, status=status.HTTP_200_OK
        )
    except Exception as e:
        print(e)
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def log_failed_email(student, plain_password, hashed_password, error):
    log_dir = "failed_emails"
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "failed_emails.txt")
    with open(log_file, "a") as f:
        f.write(f"Failed to send email to: {student.email}\n")
        f.write(f"Username: {student.username}\n")
        f.write(f"Plain Password: {plain_password}\n")
        f.write(f"Hashed Password: {hashed_password}\n")
        f.write(f"Error: {error}\n")
        f.write("\n")

def mail_to_user_single(user_data, password, recipient_email=None):
    recipient = recipient_email or user_data.get('email')
    if not recipient:
        raise ValueError('Recipient email is required to send credentials.')

    subject = "Fusion Portal Credentials"
    portal_email = user_data.get('email') or recipient
    username = user_data.get('username', '').upper()
    message = (
        f"Dear User,\n\n"
        "Your Fusion portal account has been created. Please find your login credentials below:\n\n"
        f"Portal Link: http://fusion.iiitdmj.ac.in\n"
        f"Username: {username}\n"
        f"Login Email: {portal_email}\n"
        f"Password: {password}\n\n"
        "Important Instructions:\n"
        "1. Initial Login: Use the credentials above to log in to the portal.\n"
        "2. Change Password: After login, change your password immediately.\n"
        "3. Keep these credentials confidential.\n\n"
        "If you face any issues, contact fusion@iiitdmj.ac.in.\n\n"
        "Best regards,\n"
        "Fusion Development Team\n"
        "PDPM IIITDM Jabalpur"
    )
    recipient_list = [recipient]
    if int(getattr(settings, 'EMAIL_TEST_MODE', 0)) == 1:
        recipient_list = [settings.EMAIL_TEST_USER]
    send_email(subject=subject, message=message, recipient_list=recipient_list)


def mail_to_user(created_users, recipient_email=None):
    try:
        max_threads = min(10, len(created_users))
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_threads) as executor:
            future_to_user = [
                executor.submit(mail_to_user_single, user, "user@123", recipient_email) for user in created_users
            ]

            for future, user in zip(future_to_user, created_users):
                try:
                    future.result()
                except Exception as e:
                    log_failed_email(user, "user@123", make_password("user@123"), str(e))
        print("Emails sent successfully.")
    except Exception as e:
        print(e)

def convert_to_iso(date_str):
    for fmt in ("%d-%m-%Y", "%d/%m/%Y", "%d/%m/%y", "%d-%m-%y"):
        try:
            date = datetime.strptime(date_str, fmt)
            return date.strftime("%Y-%m-%d")
        except ValueError:
            continue
    dummy_date = datetime.strptime("01-01-2004", "%d-%m-%Y")
    return dummy_date.strftime("%Y-%m-%d")

def add_user_extra_info(row,user):
    department_name = row[13] if row[13] else 'CSE'

    # Department name mapping - handles various formats
    dept_mapping = {
        # Full names to abbreviations
        'Computer Science': 'CSE',
        'Computer Science & Engineering': 'CSE',
        'Information Technology': 'CSE',
        'Mechanical': 'ME',
        'Mechanical Engineering': 'ME',
        'Electronics': 'ECE',
        'Electronics & Communication': 'ECE',
        'Natural Science': 'SM',
        'Mechatronics': 'SM',
        'Data Science': 'CSE',
        'Design': 'Design',  # For B.Des students
        # Already abbreviations - keep as is
        'CSE': 'CSE',
        'ECE': 'ECE',
        'ME': 'ME',
        'SM': 'SM',
        'MT': 'MT',
    }

    # Try exact match first
    try:
        department = GlobalsDepartmentinfo.objects.get(name=department_name).id
    except GlobalsDepartmentinfo.DoesNotExist:
        # Try mapping
        mapped_name = dept_mapping.get(department_name, department_name)
        try:
            dept_obj = GlobalsDepartmentinfo.objects.get(name=mapped_name)
            department = dept_obj.id
            print(f"[INFO] Mapped department '{department_name}' to '{mapped_name}'")
        except GlobalsDepartmentinfo.DoesNotExist:
            # Default to CSE if not found
            try:
                department = GlobalsDepartmentinfo.objects.get(name='CSE').id
                print(f"[WARNING] Department '{department_name}' not found, using CSE")
            except GlobalsDepartmentinfo.DoesNotExist:
                # Use first available department
                first_dept = GlobalsDepartmentinfo.objects.first()
                if first_dept:
                    department = first_dept.id
                    print(f"[WARNING] Using first available department: {first_dept.name}")
                else:
                    raise Exception("No departments found in database")

    extra_info_data = {
        'id': row[0].upper(),
        'title': row[9].capitalize() if row[9] else 'Mr.' if row[3] and row[3][0].upper() == 'M' else 'Ms.',
        'sex': row[3][0].upper(),
        'date_of_birth': convert_to_iso(row[10]),
        'user_status': "PRESENT",
        'address': row[11].lower().capitalize() if row[11] else 'NA',
        'phone_no': row[12] if row[12] else 9999999999,
        'user_type': 'student',
        'profile_picture': None,
        'about_me': 'NA',
        'date_modified': datetime.now().strftime("%Y-%m-%d"),
        'department': department,
        'user': user.id,
    }
    extra_info_serializer = GlobalExtraInfoSerializer(data=extra_info_data)
    if extra_info_serializer.is_valid():
        return extra_info_serializer
    else:
        print(f"[ERROR] ExtraInfo serializer errors: {extra_info_serializer.errors}")
    return None

def add_user_designation_info(user_id, designation='student'):
    designation_id = GlobalsDesignation.objects.get(name=designation).id
    data = {
        'designation' : designation_id,
        'user' : user_id,
        'working' : user_id,
    }
    serializer = GlobalsHoldsDesignationSerializer(data=data)
    if serializer.is_valid():
        return serializer
    return None

def add_student_info(row, extrainfo):
    batch = int(row[7]) if row[7] else datetime.now().year
    batch_id = Batch.objects.all().filter(name = row[8], discipline__acronym = extrainfo.department.name, year = batch)
    data = {
        'id' : extrainfo.id,
        'programme' : row[8] if row[8] else 'B.Tech',
        'batch' : batch,
        'batch_id' : batch_id.first().id if batch_id else None,
        'cpi': 0.0,
        'category' : row[4].upper() if row[4].upper() else 'GEN',
        'father_name' : row[5].lower().capitalize() if row[5] else 'NA',
        'mother_name' : row[6].lower().capitalize() if row[6] else 'NA',
        'hall_no': 3,
        'room_no': None,
        'specialization': None,
        'curr_semester_no' : 2*(datetime.now().year - batch) + datetime.now().month // 7,
    }
    serializer = StudentSerializer(data=data)
    if serializer.is_valid():
        return serializer
    return None
# Role conflict rules definition
ROLE_CONFLICT_RULES = {
    'director': ['dean', 'hod'],
    'dean': ['director', 'hod'],
    'hod': ['director', 'dean'],
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

def get_available_roles_for_user(user_type):
    """
    Get available roles based on user type (student, faculty, staff)
    """
    if user_type == 'student':
        return list(GlobalsDesignation.objects.filter(category='student').values_list('name', flat=True))
    elif user_type == 'faculty':
        return list(GlobalsDesignation.objects.filter(category__in=['faculty', None]).values_list('name', flat=True))
    elif user_type == 'staff':
        return list(GlobalsDesignation.objects.filter(category__in=['staff', None]).values_list('name', flat=True))
    return []

def switch_user_role(username, designation_id):
    """
    Switch user's current active role
    """
    try:
        user = AuthUser.objects.get(username__iexact=username)
        designation = GlobalsDesignation.objects.get(id=designation_id)

        # Check if user has this role
        role_assignment = GlobalsHoldsdesignation.objects.filter(
            user=user,
            designation=designation
        ).first()

        if not role_assignment:
            return {
                'success': False,
                'error': 'User does not have this role'
            }

        # Update the working designation
        GlobalsHoldsdesignation.objects.filter(user=user).update(working=user.id)
        role_assignment.working = user.id
        role_assignment.save()

        return {
            'success': True,
            'message': f'Switched to role: {designation.name}',
            'current_role': designation.name
        }

    except AuthUser.DoesNotExist:
        return {
            'success': False,
            'error': 'User not found'
        }
    except GlobalsDesignation.DoesNotExist:
        return {
            'success': False,
            'error': 'Designation not found'
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }
