"""
Role and designation related models.
Handles user roles, designations, department hierarchy, and access control.
"""

from django.db import models


class GlobalsDepartmentinfo(models.Model):
    """Department information with hierarchical structure"""

    name = models.CharField(unique=True, max_length=100)
    parent_department = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='child_departments',
        db_column='parent_department_id'
    )

    class Meta:
        managed = False
        db_table = 'globals_departmentinfo'

    def __str__(self):
        return self.name


class GlobalsDesignation(models.Model):
    """Designation/role definitions with access control"""

    name = models.CharField(unique=True, max_length=50)
    full_name = models.CharField(max_length=100)
    type = models.CharField(max_length=30)
    basic = models.BooleanField(default=False, null=False, blank=False)
    category = models.CharField(max_length=20, null=True, blank=True)
    dept_if_not_basic = models.ForeignKey(
        GlobalsDepartmentinfo,
        on_delete=models.CASCADE,
        blank=True,
        null=True
    )
    is_singular = models.BooleanField(
        default=False,
        help_text="If True, only one user can hold this role at a time"
    )

    class Meta:
        managed = False
        db_table = 'globals_designation'

    def __str__(self):
        return self.name


class GlobalsHoldsdesignation(models.Model):
    """User designation assignments with temporal tracking"""

    held_at = models.DateTimeField(auto_now=True)
    start_date = models.DateField(
        null=True,
        blank=True,
        help_text="Role assignment start date (optional)"
    )
    end_date = models.DateField(
        null=True,
        blank=True,
        help_text="Role assignment end date (optional)"
    )
    designation = models.ForeignKey(
        GlobalsDesignation,
        related_name='designees',
        on_delete=models.CASCADE
    )
    user = models.ForeignKey(
        'AuthUser',
        related_name='holds_designations',
        on_delete=models.CASCADE
    )
    working = models.ForeignKey(
        'AuthUser',
        related_name='current_designation',
        on_delete=models.CASCADE
    )

    class Meta:
        managed = False
        db_table = 'globals_holdsdesignation'
        unique_together = (
            ('user', 'designation'),
            ('working', 'designation'),
        )


class GlobalsModuleaccess(models.Model):
    """Module access permissions for designations"""

    designation = models.CharField(max_length=155)
    program_and_curriculum = models.BooleanField()
    course_registration = models.BooleanField()
    course_management = models.BooleanField()
    other_academics = models.BooleanField()
    spacs = models.BooleanField()
    department = models.BooleanField()
    examinations = models.BooleanField()
    hr = models.BooleanField()
    iwd = models.BooleanField()
    complaint_management = models.BooleanField()
    fts = models.BooleanField()
    purchase_and_store = models.BooleanField()
    rspc = models.BooleanField()
    hostel_management = models.BooleanField()
    mess_management = models.BooleanField()
    gymkhana = models.BooleanField()
    placement_cell = models.BooleanField()
    visitor_hostel = models.BooleanField()
    phc = models.BooleanField()
    inventory_management = models.BooleanField()

    class Meta:
        managed = False
        db_table = 'globals_moduleaccess'

    def __str__(self):
        return f"Access: {self.designation}"


class GlobalsFaculty(models.Model):
    """Faculty specific information"""

    id = models.OneToOneField(
        'GlobalsExtrainfo',
        on_delete=models.CASCADE,
        primary_key=True
    )

    def __str__(self):
        return str(self.id)

    class Meta:
        managed = False
        db_table = 'globals_faculty'


class Staff(models.Model):
    """Staff specific information"""

    id = models.OneToOneField(
        'GlobalsExtrainfo',
        on_delete=models.CASCADE,
        primary_key=True
    )

    def __str__(self):
        return str(self.id)

    class Meta:
        managed = False
        db_table = 'globals_staff'