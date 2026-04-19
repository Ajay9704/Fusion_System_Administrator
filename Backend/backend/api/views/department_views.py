"""
Department Management Views - Handles department operations, hierarchy, and management
Extracted from the monolithic views.py for enterprise architecture
"""

from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from ..models import GlobalsDepartmentinfo
from ..serializers import GlobalsDepartmentinfoSerializer
from ..audit import audit_log, create_audit_log, get_client_ip, get_user_agent


@api_view(['GET'])
def get_all_departments(request):
    """Get academic departments only"""
    academic_departments = [
        'CSE', 'ECE', 'ME', 'MT', 'SM', 'CSE M.Tech', 'CSE Ph.D', 'CSE B.Tech',
        'ECE M.Tech', 'ECE Ph.D', 'ECE B.Tech', 'Natural Science', 'Mechatronics',
        'Design', 'Workshop'
    ]
    records = GlobalsDepartmentinfo.objects.filter(
        name__in=academic_departments
    ).order_by('id')
    serializer = GlobalsDepartmentinfoSerializer(records, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def get_all_departments_admin(request):
    """All departments including administrative ones — used for staff assignment"""
    records = GlobalsDepartmentinfo.objects.all().order_by('name')
    serializer = GlobalsDepartmentinfoSerializer(records, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def get_departments_by_programme(request):
    """Get departments filtered by programme"""
    programme = request.query_params.get('programme')
    academic_departments = [
        'CSE', 'ECE', 'ME', 'MT', 'SM', 'CSE M.Tech', 'CSE Ph.D', 'CSE B.Tech',
        'ECE M.Tech', 'ECE Ph.D', 'ECE B.Tech', 'Natural Science', 'Mechatronics',
        'Design', 'Workshop'
    ]

    if not programme:
        # If no programme specified, return all academic departments
        depts = academic_departments
    else:
        # Filter departments based on programme
        programme_dept_mapping = {
            'B.Tech': ['CSE', 'ECE', 'ME', 'MT', 'SM', 'CSE B.Tech', 'ECE B.Tech',
                     'Natural Science', 'Mechatronics', 'Workshop'],
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
def get_all_departments_with_hierarchy(request):
    """Get all departments with hierarchical structure"""
    departments = GlobalsDepartmentinfo.objects.all().order_by('name')

    department_list = []
    for dept in departments:
        dept_data = {
            'id': dept.id,
            'name': dept.name,
            'description': dept.description if hasattr(dept, 'description') else '',
        }

        # Add parent department info if exists
        if hasattr(dept, 'parent') and dept.parent:
            dept_data['parent_id'] = dept.parent.id
            dept_data['parent_name'] = dept.parent.name
        else:
            dept_data['parent_id'] = None
            dept_data['parent_name'] = None

        department_list.append(dept_data)

    return Response({
        'departments': department_list,
        'total_count': len(department_list)
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@audit_log(action='CREATE_DEPARTMENT', model_name='GlobalsDepartmentinfo')
def create_department(request):
    """Create a new department"""
    try:
        data = request.data.copy()

        # Check if department with same name already exists
        if GlobalsDepartmentinfo.objects.filter(name=data.get('name')).exists():
            return Response({
                'error': 'Department with this name already exists'
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer = GlobalsDepartmentinfoSerializer(data=data)

        if serializer.is_valid():
            department = serializer.save()

            return Response({
                'message': 'Department created successfully',
                'department': serializer.data
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'error': 'Invalid data',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        return Response({
            'error': f'Failed to create department: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
@audit_log(action='UPDATE_DEPARTMENT', model_name='GlobalsDepartmentinfo')
def update_department(request, department_id):
    """Update existing department"""
    try:
        try:
            department = GlobalsDepartmentinfo.objects.get(id=department_id)
        except GlobalsDepartmentinfo.DoesNotExist:
            return Response({
                'error': f'Department with id {department_id} not found'
            }, status=status.HTTP_404_NOT_FOUND)

        partial = request.method == 'PATCH'
        serializer = GlobalsDepartmentinfoSerializer(
            department,
            data=request.data,
            partial=partial
        )

        if serializer.is_valid():
            serializer.save()

            return Response({
                'message': 'Department updated successfully',
                'department': serializer.data
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': 'Invalid data',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        return Response({
            'error': f'Failed to update department: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
@audit_log(action='DELETE_DEPARTMENT', model_name='GlobalsDepartmentinfo')
def delete_department(request, department_id):
    """Delete a department"""
    try:
        try:
            department = GlobalsDepartmentinfo.objects.get(id=department_id)
        except GlobalsDepartmentinfo.DoesNotExist:
            return Response({
                'error': f'Department with id {department_id} not found'
            }, status=status.HTTP_404_NOT_FOUND)

        department_name = department.name
        department.delete()

        return Response({
            'message': f'Department {department_name} deleted successfully'
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            'error': f'Failed to delete department: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_department_tree(request):
    """Get department tree structure"""
    try:
        departments = GlobalsDepartmentinfo.objects.all().order_by('name')

        # Build tree structure
        tree_data = []
        for dept in departments:
            node = {
                'id': dept.id,
                'name': dept.name,
                'children': []
            }

            # Add children departments if they exist
            if hasattr(dept, 'children') and dept.children.exists():
                for child in dept.children.all():
                    node['children'].append({
                        'id': child.id,
                        'name': child.name
                    })

            tree_data.append(node)

        return Response({
            'tree': tree_data,
            'total_departments': len(tree_data)
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            'error': f'Failed to get department tree: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)