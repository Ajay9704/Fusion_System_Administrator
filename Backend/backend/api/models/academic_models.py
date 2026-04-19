"""
Academic related models.
Handles programmes, disciplines, curriculum, batches, and student information.
"""

from django.db import models
import datetime


class Programme(models.Model):
    """Academic programme information"""

    category = models.CharField(max_length=3, null=False, blank=False)
    name = models.CharField(max_length=70, null=False, unique=True, blank=False)
    programme_begin_year = models.PositiveIntegerField(
        default=datetime.date.today().year,
        null=False
    )

    class Meta:
        managed = False
        db_table = 'programme_curriculum_programme'

    def __str__(self):
        return f"{self.category} - {self.name}"


class Discipline(models.Model):
    """Academic discipline/department information"""

    name = models.CharField(max_length=100, null=False, unique=True, blank=False)
    acronym = models.CharField(max_length=10, null=False, default="", blank=False)
    programmes = models.ManyToManyField(Programme, blank=True)

    class Meta:
        managed = False
        db_table = 'programme_curriculum_discipline'

    def __str__(self):
        return f"{self.name} {self.acronym}"


class Curriculum(models.Model):
    """Curriculum information for programmes"""

    programme = models.ForeignKey(Programme, on_delete=models.CASCADE, null=False)
    name = models.CharField(max_length=100, null=False, blank=False)
    version = models.DecimalField(default=1.0, max_digits=5, decimal_places=1)
    working_curriculum = models.BooleanField(default=True, null=False)
    no_of_semester = models.PositiveIntegerField(default=1, null=False)
    min_credit = models.PositiveIntegerField(default=0, null=False)
    latest_version = models.BooleanField(default=True)

    class Meta:
        unique_together = ('name', 'version',)
        managed = False
        db_table = 'programme_curriculum_curriculum'

    def __str__(self):
        return f"{self.name} v{self.version}"


class Batch(models.Model):
    """Student batch information"""

    name = models.CharField(max_length=50, null=False, blank=False)
    discipline = models.ForeignKey(Discipline, null=False, on_delete=models.CASCADE)
    year = models.PositiveIntegerField(
        default=datetime.date.today().year,
        null=False
    )
    curriculum = models.ForeignKey(Curriculum, null=True, blank=True, on_delete=models.SET_NULL)
    running_batch = models.BooleanField(default=True)

    class Meta:
        unique_together = ('name', 'discipline', 'year',)
        managed = False
        db_table = 'programme_curriculum_batch'

    def __str__(self):
        return f"{self.name} {self.discipline.acronym} {self.year}"


class Student(models.Model):
    """Student academic and personal information"""

    id = models.OneToOneField('GlobalsExtrainfo', on_delete=models.CASCADE, primary_key=True)
    programme = models.CharField(max_length=10)
    batch = models.IntegerField(default=2016)
    batch_id = models.ForeignKey(Batch, null=True, blank=True, on_delete=models.CASCADE)
    cpi = models.FloatField(default=0)
    category = models.CharField(max_length=10, null=False)
    father_name = models.CharField(max_length=40, default='', null=True)
    mother_name = models.CharField(max_length=40, default='', null=True)
    hall_no = models.IntegerField(default=0)
    room_no = models.CharField(max_length=10, blank=True, null=True)
    specialization = models.CharField(max_length=40, null=True, default='')
    curr_semester_no = models.IntegerField(default=1)

    class Meta:
        managed = False
        db_table = 'academic_information_student'

    def __str__(self):
        return str(self.id.user.username)