from rest_framework.response import Response
from rest_framework import status
import concurrent.futures
import random
import string
from django.contrib.auth.hashers import make_password
from django.core.mail import send_mail
from django.conf import settings
from datetime import datetime
from .models import GlobalsDepartmentinfo, Batch, GlobalsDesignation
from .serializers import GlobalExtraInfoSerializer, GlobalsHoldsDesignationSerializer, StudentSerializer
import os
import re

def validate_email_format(email):
    """Validate email format"""
    if not email:
        return False
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_pattern, email) is not None

def validate_personal_email(email):
    """
    Validate personal email
    - Must be valid email format
    - Cannot be @iiitdmj.ac.in domain (must be external)
    """
    if not validate_email_format(email):
        return False, "Invalid email format"
    
    if email.lower().endswith('@iiitdmj.ac.in'):
        return False, "Please provide a personal email (not college email)"
    
    return True, "Valid"


def create_password(data):
    user_name = data.get('username', '').lower().capitalize()
    if not user_name:
        return "Fusion@2025"  # Default for bulk uploads
    special_characters = string.punctuation
    random_specials = ''.join(random.choice(special_characters) for _ in range(3))
    return f"{user_name}{random_specials}"


def convert_to_iso(date_string):
    """
    Convert various date formats to ISO format (YYYY-MM-DD)
    Handles: DD-MM-YYYY, MM/DD/YYYY, YYYY-MM-DD
    """
    import datetime
    if not date_string or date_string.strip() == '':
        return "2025-01-01"
    
    date_str = date_string.strip()
    
    # Try different formats
    formats = [
        '%Y-%m-%d',      # 2000-01-30
        '%d-%m-%Y',      # 30-01-2000
        '%m/%d/%Y',      # 01/30/2000
        '%d/%m/%Y',      # 30/01/2000
    ]
    
    for fmt in formats:
        try:
            date_obj = datetime.datetime.strptime(date_str, fmt)
            return date_obj.strftime('%Y-%m-%d')
        except ValueError:
            continue
    
    # If all formats fail, return default
    return "2025-01-01"


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

def mail_to_user_single(student, password, college_email=None):
    """
    Send credential email to user's personal email
    Includes college email information if provided
    """
    user = {"username": student['username'], "password": password, "email": student['email']}
    subject = "Fusion Portal Credentials - IIITDM Jabalpur"
    
    # Build college email section if available
    college_email_section = ""
    if college_email:
        college_email_section = f"""
Your College Email Address:
College Email: {college_email}
(This is your official institute email for academic purposes)
"""
    
    message = (
        f"Dear Student,\n\n"
        "We are excited to introduce Fusion, our new ERP software, being developed by our own students, "
        "which is now live for the Pre-Registration Process. "
        "This platform will streamline your academic journey and provide a seamless experience for course registrations "
        "and other academic-related activities.\n\n"
        "Please find your login credentials below:\n\n"
        "Portal Link: \n http://fusion.iiitdmj.ac.in:8000 \n http://fusion.iiitdmj.ac.in/ \n http://172.27.16.216:8000/  (On LAN Only) /\n"
        f"Username: {user['username'].upper()}\n"
        f"Password: {password}\n\n"
        f"{college_email_section}"
        "Important Instructions:\n"
        "1. Initial Login: Use the credentials provided above to log in to the portal.\n"
        "2. Change Password: Upon first login, change your password with the following steps:\n"
        "   - Log Out\n"
        "   - Change Password\n"
        "   - Create a new password.\n\n"
        "Please choose a strong password and keep it confidential.\n\n"
        "Help & Support:\n"
        "If you encounter any issues, feel free to reach out to the support team at fusion@iiitdmj.ac.in, "
        "or fill out the Google form at: https://forms.gle/aHvzGoS9XAAoHyix6\n\n"
        "We look forward to your smooth experience with Fusion!\n\n"
        "Best regards,\n"
        "Fusion Development Team,\n"
        "PDPM IIITDM Jabalpur"
    )
    recipient_list = [f"{user['email']}"]  # This is now personal_email
    if(int(settings.EMAIL_TEST_MODE) == 1):
        recipient_list = [settings.EMAIL_TEST_USER]
    send_email(
        subject=subject, message=message, recipient_list=recipient_list
    )   
    
def mail_to_user(created_users):
    try:
        max_threads = min(10, len(created_users)
        )
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_threads) as executor:
            future_to_user = [
                executor.submit(mail_to_user_single, user, "user@123") for user in created_users
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