"""
Backward compatibility layer for models.
This maintains existing imports while using the new modular structure.
DEPRECATED: Please import directly from api.models.domain_modules
"""

# Import all models from the new modular structure
from .models.user_models import AuthUser, AuthUserManager, GlobalsExtrainfo
from .models.academic_models import Programme, Discipline, Curriculum, Batch, Student
from .models.role_models import (
    GlobalsDesignation, GlobalsHoldsdesignation, GlobalsModuleaccess,
    GlobalsFaculty, Staff, GlobalsDepartmentinfo
)
from .models.audit_models import AuditLog
from .models.emergency_models import EmergencyAccess, HandoverDocumentation

# Export all models for backward compatibility
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