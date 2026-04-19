"""
Authentication Views - Handles login, logout, token refresh, and user session management
Extracted from the monolithic views.py for enterprise architecture
"""

from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from datetime import timedelta, datetime
from django.utils import timezone

from ..models import AuthUser, GlobalsHoldsdesignation, AuditLog
from ..audit import audit_log, create_audit_log, get_client_ip, log_failed_login, get_user_agent


@api_view(['POST'])
def login_view(request):
    """
    Authenticate user and return JWT tokens.
    Accepts username OR email + password.
    """
    username_or_email = request.data.get('username')
    password = request.data.get('password')

    if not username_or_email or not password:
        return Response(
            {"error": "Username/email and password are required"},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        # Try to find user by username or email
        if '@' in username_or_email:
            user = AuthUser.objects.get(email__iexact=username_or_email)
        else:
            user = AuthUser.objects.get(username__iexact=username_or_email)

        # Check for account lockout due to failed login attempts
        from backend.settings import LOGIN_LOCKOUT_ENABLED, MAX_FAILED_LOGIN_ATTEMPTS, FAILED_LOGIN_ATTEMPT_DURATION
        if LOGIN_LOCKOUT_ENABLED:
            lockout_window = timezone.now() - timedelta(seconds=FAILED_LOGIN_ATTEMPT_DURATION)
            recent_failures = AuditLog.objects.filter(
                action='FAILED_LOGIN',
                description__contains=username_or_email,
                timestamp__gte=lockout_window
            ).count()

            if recent_failures >= MAX_FAILED_LOGIN_ATTEMPTS:
                return Response({
                    "error": f"Account locked due to multiple failed login attempts. Please try again after {FAILED_LOGIN_ATTEMPT_DURATION // 60} minutes."
                }, status=status.HTTP_429_TOO_MANY_REQUESTS)

    except AuthUser.DoesNotExist:
        # Log failed login attempt
        try:
            log_failed_login(
                username_or_email=username_or_email,
                reason='User does not exist',
                ip_address=get_client_ip(request),
                user_agent=get_user_agent(request)
            )
        except Exception:
            pass
        return Response(
            {"error": "Invalid credentials"},
            status=status.HTTP_401_UNAUTHORIZED
        )

    # Check password
    from django.contrib.auth import authenticate
    if not authenticate(username=user.username, password=password):
        # Log failed login attempt
        try:
            log_failed_login(
                username_or_email=username_or_email,
                reason='Invalid password',
                ip_address=get_client_ip(request),
                user_agent=get_user_agent(request)
            )
        except Exception:
            pass
        return Response(
            {"error": "Invalid credentials"},
            status=status.HTTP_401_UNAUTHORIZED
        )

    if not user.is_active:
        # Log failed login attempt
        try:
            log_failed_login(
                username_or_email=username_or_email,
                reason='Account is disabled',
                ip_address=get_client_ip(request),
                user_agent=get_user_agent(request)
            )
        except Exception:
            pass
        return Response(
            {"error": "Account is disabled"},
            status=status.HTTP_403_FORBIDDEN
        )

    # SYSTEM ADMIN RESTRICTION: Only admin users (is_staff or is_superuser) can access System Admin
    if not user.is_staff and not user.is_superuser:
        try:
            log_failed_login(
                username_or_email=username_or_email,
                reason='Non-admin user attempted to access System Admin',
                ip_address=get_client_ip(request),
                user_agent=get_user_agent(request)
            )
        except Exception:
            pass
        return Response(
            {"error": "Access denied. System Admin is restricted to administrators only."},
            status=status.HTTP_403_FORBIDDEN
        )

    # Generate tokens
    try:
        refresh = RefreshToken.for_user(user)
        user.last_login = timezone.now()
        user.save()

        user_roles = GlobalsHoldsdesignation.objects.filter(user=user).select_related('designation')
        roles = [entry.designation.name for entry in user_roles]

        create_audit_log(
            user=user,
            action='USER_LOGIN',
            model_name='AuthUser',
            object_id=str(user.id),
            description=f"User {user.username} logged in successfully",
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
            status='SUCCESS'
        )

        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'roles': roles,
                'is_staff': user.is_staff,
                'is_superuser': user.is_superuser
            }
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {"error": "Failed to generate authentication tokens", "detail": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class CustomTokenRefreshView(TokenRefreshView):
    """Custom token refresh that returns user data"""
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)

        if response.status_code == 200:
            try:
                refresh = RefreshToken(request.data.get('refresh'))
                user_id = refresh['user_id']
                user = AuthUser.objects.get(id=user_id)

                user_roles = GlobalsHoldsdesignation.objects.filter(user=user).select_related('designation')
                roles = [entry.designation.name for entry in user_roles]

                response.data['user'] = {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'roles': roles,
                    'is_staff': user.is_staff,
                }
            except Exception:
                pass

        return response


@api_view(['POST'])
def logout_view(request):
    """Log out user and record audit trail"""
    user = request.user

    if user.is_authenticated:
        create_audit_log(
            user=user,
            action='USER_LOGOUT',
            model_name='AuthUser',
            object_id=str(user.id),
            description=f"User {user.username} logged out",
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
            status='SUCCESS'
        )

        return Response({"message": "Successfully logged out"}, status=status.HTTP_200_OK)

    return Response({"error": "Not authenticated"}, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_current_user(request):
    """Get current authenticated user's information"""
    user = request.user

    try:
        user_roles = GlobalsHoldsdesignation.objects.filter(user=user).select_related('designation')
        roles = [entry.designation.name for entry in user_roles]

        return Response({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'roles': roles,
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser,
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            "error": f"Failed to get user info: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)