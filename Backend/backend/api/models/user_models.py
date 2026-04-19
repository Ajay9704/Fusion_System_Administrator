"""
User and authentication related models.
Handles user accounts, credentials, and basic profile information.
"""

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager


class AuthUserManager(BaseUserManager):
    """Custom user manager for AuthUser model"""

    def create_user(self, username, email, password=None, **extra_fields):
        if not username:
            raise ValueError('The Username field must be set')
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        return self.create_user(username, email, password, **extra_fields)


class AuthUser(AbstractBaseUser):
    """Custom user model extending Django's AbstractBaseUser"""

    id = models.AutoField(primary_key=True)
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(blank=True, null=True)
    is_superuser = models.BooleanField(default=False)
    username = models.CharField(unique=True, max_length=150)
    first_name = models.CharField(max_length=150, blank=True, default='')
    last_name = models.CharField(max_length=150, blank=True, default='')
    email = models.CharField(max_length=254, blank=True, default='')
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(auto_now_add=True)

    objects = AuthUserManager()

    USERNAME_FIELD = 'username'
    EMAIL_FIELD = 'email'
    REQUIRED_FIELDS = ['email']

    def __str__(self):
        return self.username

    def has_perm(self, perm, obj=None):
        return True

    def has_module_perms(self, app_label):
        return True

    class Meta:
        managed = False
        db_table = 'auth_user'


class GlobalsExtrainfo(models.Model):
    """Extended user information and profile data"""

    id = models.CharField(primary_key=True, max_length=50)
    title = models.CharField(max_length=20)
    sex = models.CharField(max_length=2)
    date_of_birth = models.DateField()
    user_status = models.CharField(max_length=50)
    address = models.TextField()
    phone_no = models.BigIntegerField(blank=True, null=True)
    user_type = models.CharField(max_length=20)
    profile_picture = models.CharField(max_length=100, blank=True, null=True)
    about_me = models.TextField()
    date_modified = models.DateTimeField(blank=True, null=True)
    department = models.ForeignKey(
        'GlobalsDepartmentinfo',
        on_delete=models.CASCADE,
        blank=True,
        null=True
    )
    user = models.OneToOneField(AuthUser, on_delete=models.CASCADE)

    class Meta:
        managed = False
        db_table = 'globals_extrainfo'

    def __str__(self):
        return f"{self.id} - {self.user.username}"