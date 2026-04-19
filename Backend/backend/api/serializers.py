from rest_framework import serializers
from .models import GlobalsExtrainfo, GlobalsDesignation, GlobalsHoldsdesignation, AuthUser, GlobalsModuleaccess, Student, Batch, Curriculum, Discipline, Programme, Staff, GlobalsFaculty, GlobalsDepartmentinfo, AuditLog

class GlobalExtraInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = GlobalsExtrainfo
        fields = '__all__'

class GlobalsDesignationSerializer(serializers.ModelSerializer):
    class Meta:
        model = GlobalsDesignation
        fields = '__all__'

class GlobalsDepartmentinfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = GlobalsDepartmentinfo
        fields = '__all__'
        
class GlobalsHoldsDesignationSerializer(serializers.ModelSerializer):
    designation_name = serializers.CharField(source='designation.name', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = GlobalsHoldsdesignation
        fields = '__all__'
        
class AuthUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuthUser
        fields = '__all__'
        
class GlobalsModuleaccessSerializer(serializers.ModelSerializer):
    class Meta:
        model = GlobalsModuleaccess
        fields = '__all__'

    def validate_id(self, value):
        if GlobalsModuleaccess.objects.filter(id=value).exists():
            raise serializers.ValidationError("The ID must be unique.")
        return value

class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = '__all__'

class StaffSerializer(serializers.ModelSerializer):
    class Meta:
        model = Staff
        fields = '__all__'

class BatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Batch
        fields = '__all__'

class CurriculumSerializer(serializers.ModelSerializer):
    class Meta:
        model = Curriculum
        fields = '__all__'


class DisciplineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Discipline
        fields = '__all__'

class ProgrammeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Programme
        fields = '__all__'

class GlobalsFacultySerializer(serializers.ModelSerializer):
    class Meta:
        model = GlobalsFaculty
        fields = '__all__'

class ViewStudentsWithFiltersSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='id.user.username')
    full_name = serializers.SerializerMethodField()
    programme = serializers.CharField()
    batch = serializers.IntegerField()
    curr_semester_no = serializers.IntegerField()
    discipline = serializers.SerializerMethodField()
    user_type = serializers.SerializerMethodField()
    category = serializers.CharField()
    gender = serializers.CharField(source='id.sex')
    is_active = serializers.BooleanField(source='id.user.is_active')

    class Meta:
        model = Student
        fields = ['id', 'username', 'full_name', 'user_type', 'programme', 'discipline', 'batch', 'curr_semester_no', 'category', 'gender', 'is_active']
    
    def get_full_name(self, obj):
        return f"{obj.id.user.first_name} {obj.id.user.last_name}".strip()

    def get_user_type(self, obj):
        return "student"

    def get_discipline(self, obj):
        if obj.batch_id and obj.batch_id.discipline:
            return obj.batch_id.discipline.name
        return None

class ViewStaffWithFiltersSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='id.user.username')
    full_name = serializers.SerializerMethodField()
    user_type = serializers.SerializerMethodField()
    gender = serializers.CharField(source='id.sex', default=None)
    designations = serializers.SerializerMethodField()
    is_active = serializers.BooleanField(source='id.user.is_active')

    class Meta:
        model = Staff
        fields = ['id', 'username', 'full_name', 'user_type', 'gender', 'designations', 'is_active']
    
    def get_full_name(self, obj):
        return f"{obj.id.user.first_name} {obj.id.user.last_name}".strip()

    def get_user_type(self, obj):
        return "staff"

    def get_designations(self, obj):
        return [
            d.designation.name
            for d in obj.id.user.holds_designations.all()
        ]

class ViewFacultyWithFiltersSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='id.user.username')
    full_name = serializers.SerializerMethodField()
    department = serializers.CharField(source='id.department.name', default=None)
    designations = serializers.SerializerMethodField()
    user_type = serializers.SerializerMethodField()
    gender = serializers.CharField(source='id.sex', default=None)
    is_active = serializers.BooleanField(source='id.user.is_active')

    class Meta:
        model = GlobalsFaculty
        fields = ['id', 'username', 'full_name', 'user_type', 'department', 'designations', 'gender', 'is_active']
    
    def get_full_name(self, obj):
        return f"{obj.id.user.first_name} {obj.id.user.last_name}".strip()

    def get_user_type(self, obj):
        return "faculty"
    
    def get_designations(self, obj):
        return [
            d.designation.name 
            for d in obj.id.user.holds_designations.all()
        ]


class AuditLogSerializer(serializers.ModelSerializer):
    user_username = serializers.SerializerMethodField()
    user_email = serializers.SerializerMethodField()

    class Meta:
        model = AuditLog
        fields = '__all__'
        read_only_fields = ['timestamp']

    def get_user_username(self, obj):
        try:
            return obj.user.username if obj.user else 'System'
        except:
            return 'System'

    def get_user_email(self, obj):
        try:
            return obj.user.email if obj.user else ''
        except:
            return ''