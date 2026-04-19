"""
Comprehensive Audit Logging Middleware for ALL User Actions
This logs every action by every user, not just admin operations.
"""
import json
from django.utils import timezone
from api.models import AuditLog
from api.audit import get_client_ip, get_user_agent


class ComprehensiveAuditMiddleware:
    """
    Middleware that logs ALL user actions across the entire system.
    This is critical for:
    - Security monitoring (detecting suspicious activity)
    - Compliance (who did what and when)
    - Troubleshooting (tracking data changes)
    - Accountability (non-repudiation)
    - Forensic analysis (investigating incidents)
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Skip logging for:
        # - Health checks
        # - Static files
        # - OPTIONS requests (CORS preflight)
        skip_paths = [
            '/admin/',
            '/static/',
            '/media/',
            '/api/health/',
            '/favicon.ico',
        ]
        
        should_skip = any(request.path.startswith(path) for path in skip_paths)
        should_skip = should_skip or request.method == 'OPTIONS'
        
        if should_skip:
            return self.get_response(request)
        
        # Execute request
        response = self.get_response(request)
        
        # Log the action
        self.log_request(request, response)
        
        return response
    
    def log_request(self, request, response):
        """Log the request/response pair"""
        try:
            # Only log authenticated users
            if not hasattr(request, 'user') or not request.user.is_authenticated:
                return
            
            user = request.user
            method = request.method
            path = request.path
            status_code = response.status_code
            
            # Determine action type based on method and path
            action = self.determine_action(method, path)
            model_name = self.extract_model_name(path)
            description = self.build_description(request, response)
            
            # Determine success/failure
            status = 'SUCCESS' if status_code < 400 else 'FAILED'
            
            # Extract relevant data from request
            request_data = {}
            if hasattr(request, 'data') and request.data:
                # Don't log sensitive data
                request_data = {
                    k: v for k, v in request.data.items()
                    if k not in ['password', 'token', 'secret', 'key']
                }
            
            # Create audit log entry
            AuditLog.objects.create(
                user=user,
                action=action,
                model_name=model_name,
                object_id=self.extract_object_id(path),
                description=description,
                reason=json.dumps(request_data)[:1000] if request_data else '',
                status=status,
                ip_address=get_client_ip(request),
                user_agent=get_user_agent(request)
            )
            
        except Exception as e:
            # Don't let audit logging break the application
            print(f"Audit middleware error: {e}")
    
    def determine_action(self, method, path):
        """Determine the action type based on HTTP method and path"""
        action_map = {
            ('GET', '/api/users/'): 'VIEW_USERS',
            ('GET', '/api/roles/'): 'VIEW_ROLES',
            ('GET', '/api/departments/'): 'VIEW_DEPARTMENTS',
            ('GET', '/api/modules/'): 'VIEW_MODULES',
            ('POST', '/api/users/'): 'CREATE_USER',
            ('PUT', '/api/users/'): 'UPDATE_USER',
            ('PATCH', '/api/users/'): 'UPDATE_USER',
            ('DELETE', '/api/users/'): 'DELETE_USER',
            ('POST', '/api/roles/'): 'CREATE_ROLE',
            ('PUT', '/api/roles/'): 'UPDATE_ROLE',
            ('DELETE', '/api/roles/'): 'DELETE_ROLE',
            ('POST', '/api/departments/'): 'CREATE_DEPARTMENT',
            ('PUT', '/api/departments/'): 'UPDATE_DEPARTMENT',
            ('DELETE', '/api/departments/'): 'DELETE_DEPARTMENT',
            ('POST', '/api/auth/login/'): 'USER_LOGIN',
            ('POST', '/api/auth/logout/'): 'USER_LOGOUT',
            ('POST', '/api/auth/password-change/'): 'PASSWORD_CHANGE',
            ('GET', '/api/audit-logs/'): 'VIEW_AUDIT_LOGS',
            ('GET', '/api/analytics/'): 'VIEW_ANALYTICS',
            ('POST', '/api/emergency-access/'): 'REQUEST_EMERGENCY_ACCESS',
            ('POST', '/api/handovers/'): 'CREATE_HANDOVER',
        }
        
        # Check exact matches first
        for (m, p), action in action_map.items():
            if method == m and path.startswith(p):
                return action
        
        # Default based on method
        method_actions = {
            'GET': 'VIEW_DATA',
            'POST': 'CREATE_DATA',
            'PUT': 'UPDATE_DATA',
            'PATCH': 'UPDATE_DATA',
            'DELETE': 'DELETE_DATA',
        }
        
        return method_actions.get(method, 'UNKNOWN_ACTION')
    
    def extract_model_name(self, path):
        """Extract model name from API path"""
        path_parts = path.split('/')
        if len(path_parts) > 2:
            # /api/users/ -> Users
            # /api/roles/ -> Roles
            model = path_parts[2]
            return model.capitalize().replace('-', '_')
        return 'Unknown'
    
    def extract_object_id(self, path):
        """Extract object ID from path if present"""
        path_parts = path.split('/')
        # /api/users/123/ -> 123
        for part in path_parts:
            if part.isdigit():
                return part
        return None
    
    def build_description(self, request, response):
        """Build human-readable description"""
        method = request.method
        path = request.path
        status_code = response.status_code
        
        desc = f"{method} {path} - Status: {status_code}"
        
        # Add query parameters if present
        if request.GET:
            params = dict(request.GET)
            desc += f" | Params: {params}"
        
        return desc[:500]  # Limit length
