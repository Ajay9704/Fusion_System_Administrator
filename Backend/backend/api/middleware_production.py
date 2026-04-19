"""
Enterprise Production Middleware
Enhanced security, monitoring, and performance tracking for production deployment
"""

import time
import logging
from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
from django.core.cache import cache
from django.conf import settings
from django.utils import timezone
from ipaddress import ip_address, ip_network

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Add security headers to all HTTP responses
    """

    def process_response(self, request, response):
        # Prevent clickjacking
        response['X-Frame-Options'] = 'DENY'

        # Prevent MIME type sniffing
        response['X-Content-Type-Options'] = 'nosniff'

        # Enable XSS filter
        response['X-XSS-Protection'] = '1; mode=block'

        # Content Security Policy
        response['Content-Security-Policy'] = "default-src 'self'"

        # Referrer policy
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'

        return response


class RateLimitMiddleware(MiddlewareMixin):
    """
    Rate limiting middleware to prevent abuse
    Limits requests based on IP address and endpoint
    """

    # Rate limits: (endpoint, requests_per_minute)
    RATE_LIMITS = {
        'default': 60,  # 60 requests per minute
        '/api/auth/login/': 5,  # 5 login attempts per minute
        '/api/users/reset_password/': 3,  # 3 password resets per minute
    }

    def process_request(self, request):
        # Skip rate limiting for authenticated admin users
        if hasattr(request, 'user') and request.user.is_authenticated:
            if request.user.is_staff or request.user.is_superuser:
                return None

        # Get client IP
        ip = self.get_client_ip(request)

        # Get rate limit for this endpoint
        path = request.path
        rate_limit = self.get_rate_limit(path)

        # Check cache for current request count
        cache_key = f'rate_limit:{ip}:{path}'
        request_count = cache.get(cache_key, 0)

        if request_count >= rate_limit:
            logger.warning(f'Rate limit exceeded for {ip} on {path}')
            return JsonResponse({
                'error': 'Rate limit exceeded',
                'message': f'Maximum {rate_limit} requests per minute allowed',
                'retry_after': 60
            }, status=429)

        # Increment request count
        cache.set(cache_key, request_count + 1, 60)

        return None

    def get_client_ip(self, request):
        """Get client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def get_rate_limit(self, path):
        """Get rate limit for specific path"""
        for endpoint, limit in self.RATE_LIMITS.items():
            if endpoint != 'default' and path.startswith(endpoint):
                return limit
        return self.RATE_LIMITS['default']


class PerformanceMonitoringMiddleware(MiddlewareMixin):
    """
    Monitor API performance and response times
    """

    def process_request(self, request):
        request.start_time = time.time()
        return None

    def process_response(self, request, response):
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time

            # Log slow requests (> 1 second)
            if duration > 1.0:
                logger.warning(
                    f'Slow request: {request.method} {request.path} '
                    f'took {duration:.2f}s'
                )

            # Add response time header
            response['X-Response-Time'] = f'{duration:.3f}s'

        return response
