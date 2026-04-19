"""
Serializers for Emergency Access and Handover Documentation
"""
from rest_framework import serializers
from .models import EmergencyAccess, HandoverDocumentation, AuthUser, GlobalsDesignation


class EmergencyAccessSerializer(serializers.ModelSerializer):
    requester_username = serializers.CharField(source='requester.username', read_only=True)
    approver_username = serializers.CharField(source='approver.username', read_only=True)
    requested_role_name = serializers.CharField(source='requested_role.name', read_only=True)
    is_active_status = serializers.SerializerMethodField()
    is_expired_status = serializers.SerializerMethodField()
    
    class Meta:
        model = EmergencyAccess
        fields = '__all__'
        read_only_fields = ['requester', 'approver', 'created_at', 'approved_at', 
                           'activated_at', 'revoked_at', 'ip_address', 'user_agent']
    
    def get_is_active_status(self, obj):
        return obj.is_active()
    
    def get_is_expired_status(self, obj):
        return obj.is_expired()


class HandoverDocumentationSerializer(serializers.ModelSerializer):
    from_user_username = serializers.CharField(source='from_user.username', read_only=True)
    to_user_username = serializers.CharField(source='to_user.username', read_only=True)
    supervisor_username = serializers.CharField(source='supervisor.username', read_only=True, allow_null=True)
    department_name = serializers.CharField(source='department.name', read_only=True, allow_null=True)
    is_overdue_status = serializers.SerializerMethodField()
    
    class Meta:
        model = HandoverDocumentation
        fields = '__all__'
        read_only_fields = ['from_user', 'created_at', 'accepted_at', 'completed_at',
                           'ip_address', 'user_agent']
    
    def get_is_overdue_status(self, obj):
        return obj.is_overdue()
