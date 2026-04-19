"""
Bulk Operations Views - Handles bulk import/export, batch emails, and CSV operations
Extracted from the monolithic views.py for enterprise architecture
"""

import csv
from django.http import HttpResponse
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from io import StringIO

from ..models import AuthUser, Student, GlobalsFaculty, Staff, GlobalsDepartmentinfo, GlobalsHoldsdesignation
from ..serializers import (
    ViewStudentsWithFiltersSerializer, ViewFacultyWithFiltersSerializer,
    ViewStaffWithFiltersSerializer
)
from ..helpers import create_password, send_email, configure_password_mail
from ..audit import audit_log, create_audit_log, get_client_ip, get_user_agent


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@audit_log(action='BULK_IMPORT_USERS', model_name='AuthUser')
def bulk_import_users(request):
    """
    Enterprise-grade bulk user import with comprehensive validation
    CSV file headers:
    username, first_name, last_name, sex, category, father_name,
    mother_name, batch, programme, title, dob, address, phone_no, department
    """
    # Configuration
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
    MAX_RECORDS = 1000
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
                "detail": f"File contains {total_rows} records. Maximum allowed is {MAX_RECORDS}."
            }, status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)

        # Processing variables
        created_users = []
        failed_users = []
        validation_errors = []

        # Process rows (simplified version)
        for row_number, row in enumerate(all_rows, start=2):  # +2 for header row
            try:
                # Basic validation
                if len(row) < REQUIRED_COLUMNS:
                    validation_errors.append({
                        'row': row_number,
                        'username': row[0] if len(row) > 0 else 'N/A',
                        'error': 'INSUFFICIENT_COLUMNS'
                    })
                    failed_users.append(row)
                    continue

                # Extract fields
                username = row[0].strip() if row[0] else ''
                first_name = row[1].strip() if len(row) > 1 else ''
                last_name = row[2].strip() if len(row) > 2 else ''
                sex = row[3].strip() if len(row) > 3 else ''
                category = row[4].strip() if len(row) > 4 else ''
                father_name = row[5].strip() if len(row) > 5 else ''
                mother_name = row[6].strip() if len(row) > 6 else ''
                batch = row[7].strip() if len(row) > 7 else ''
                programme = row[8].strip() if len(row) > 8 else ''

                # Validate required fields
                if not all([username, first_name, last_name, sex, category,
                           father_name, mother_name, batch, programme]):
                    validation_errors.append({
                        'row': row_number,
                        'username': username,
                        'error': 'MISSING_REQUIRED_FIELDS'
                    })
                    failed_users.append(row)
                    continue

                # Check if user already exists
                if AuthUser.objects.filter(username=username).exists():
                    validation_errors.append({
                        'row': row_number,
                        'username': username,
                        'error': 'USER_EXISTS'
                    })
                    failed_users.append(row)
                    continue

                # Create user (simplified - full implementation would use user creation helpers)
                password = create_password(8)
                user = AuthUser.objects.create_user(
                    username=username,
                    email=f"{username}@iiitdmj.ac.in",
                    first_name=first_name,
                    last_name=last_name,
                    password=password
                )

                created_users.append({
                    'username': username,
                    'row': row_number
                })

            except Exception as e:
                validation_errors.append({
                    'row': row_number,
                    'username': row[0] if len(row) > 0 else 'N/A',
                    'error': 'PROCESSING_ERROR',
                    'message': str(e)
                })
                failed_users.append(row)

        return Response({
            'message': 'Bulk import completed',
            'total_rows': total_rows,
            'created': len(created_users),
            'failed': len(failed_users),
            'created_users': created_users,
            'errors': validation_errors
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            'error': 'Failed to process CSV file',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def bulk_export_users(request):
    """Export all users to CSV format"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="users_export.csv"'

    writer = csv.writer(response)
    writer.writerow(['username', 'first_name', 'last_name', 'email', 'is_staff', 'is_superuser'])

    users = AuthUser.objects.all()

    for user in users:
        writer.writerow([
            user.username,
            user.first_name,
            user.last_name,
            user.email,
            user.is_staff,
            user.is_superuser
        ])

    return response


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mail_to_whole_batch(request):
    """Send email to all students in a batch"""
    try:
        batch = request.data.get('batch')

        if not batch:
            return Response({
                'error': 'Batch parameter is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        students = Student.objects.filter(batch=batch)

        if not students.exists():
            return Response({
                'error': f'No students found in batch {batch}'
            }, status=status.HTTP_404_NOT_FOUND)

        students_data = [student.id.user for student in students]

        try:
            configure_password_mail(students_data)
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({
            'message': f'Mail sent to {len(students_data)} students successfully.'
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            'error': f'Failed to send batch email: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def download_sample_csv(request):
    """Download sample CSV template for bulk import"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="sample.csv"'

    writer = csv.writer(response)
    writer.writerow([
        "username", "first_name", "last_name", "sex", "category",
        "father_name", "mother_name", "batch", "programme", "title",
        "dob", "address", "phone_no", "department"
    ])

    # Add sample row
    writer.writerow([
        "2022BCS001", "John", "Doe", "M", "GEN",
        "Father's Name", "Mother's Name", "2022", "B.Tech", "Mr.",
        "2000-01-01", "Address Line", "1234567890", "CSE"
    ])

    return response


class UserListView(APIView):
    """List users with filtering and pagination"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get users with optional filtering by type"""
        try:
            user_type = request.GET.get('type')

            if not user_type:
                return Response({
                    "error": "Missing 'type' parameter"
                }, status=status.HTTP_400_BAD_REQUEST)

            if user_type == "student":
                students = Student.objects.select_related(
                    'id__user', 'id__department', 'batch_id'
                )

                # Apply filters
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
                faculty = GlobalsFaculty.objects.select_related(
                    'id__user', 'id__department'
                ).prefetch_related('id__user__holds_designations__designation')

                # Apply filters
                designation = request.GET.get("designation")
                gender = request.GET.get("gender")

                if designation:
                    faculty = faculty.filter(
                        id__user__holds_designations__designation__name__iexact=designation
                    ).distinct()
                if gender:
                    faculty = faculty.filter(id__sex__iexact=gender)

                serializer = ViewFacultyWithFiltersSerializer(faculty, many=True)

            elif user_type == "staff":
                staff = Staff.objects.select_related(
                    "id__user", "id__department"
                ).prefetch_related('id__user__holds_designations__designation')

                # Apply filters
                designation = request.GET.get("designation")
                gender = request.GET.get("gender")

                if designation:
                    staff = staff.filter(
                        id__user__holds_designations__designation__name__iexact=designation
                    ).distinct()
                if gender:
                    staff = staff.filter(id__sex__iexact=gender)

                serializer = ViewStaffWithFiltersSerializer(staff, many=True)

            else:
                return Response({
                    "error": "Invalid user type. Use 'student', 'staff', or 'faculty'"
                }, status=status.HTTP_400_BAD_REQUEST)

            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "error": f"Internal server error: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)