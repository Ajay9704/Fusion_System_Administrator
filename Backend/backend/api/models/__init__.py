"""
Enterprise Model Architecture
Models are organized by domain for better maintainability and separation of concerns.
"""

from .user_models import AuthUser, AuthUserManager, GlobalsExtrainfo
from .academic_models import Programme, Discipline, Curriculum, Batch, Student
from .role_models import (
    GlobalsDesignation, GlobalsHoldsdesignation, GlobalsModuleaccess,
    GlobalsFaculty, Staff, GlobalsDepartmentinfo
)
from .audit_models import AuditLog
from .emergency_models import EmergencyAccess, HandoverDocumentation

__all__ = [
    # User models
    'AuthUser', 'AuthUserManager', 'GlobalsExtrainfo',

    # Academic models
    'Programme', 'Discipline', 'Curriculum', 'Batch', 'Student',

    # Role models
    'GlobalsDesignation', 'GlobalsHoldsdesignation', 'GlobalsModuleaccess',
    'GlobalsFaculty', 'Staff', 'GlobalsDepartmentinfo',

    # Audit models
    'AuditLog',

    # Emergency models
    'EmergencyAccess', 'HandoverDocumentation',
]