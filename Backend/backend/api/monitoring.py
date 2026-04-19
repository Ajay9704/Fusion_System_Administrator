"""
Production Monitoring and Health Checks
System health monitoring, metrics collection, and alerting
"""

import time
import logging
import psutil
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db import connection
from django.core.cache import cache
from django.conf import settings
from django.utils import timezone
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@require_http_methods(["GET"])
@csrf_exempt
def health_check(request):
    """
    Basic health check endpoint
    Returns 200 if system is healthy
    """
    try:
        # Check database connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            db_status = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        db_status = "unhealthy"
        return JsonResponse({
            'status': 'unhealthy',
            'database': db_status,
            'timestamp': timezone.now().isoformat()
        }, status=503)

    # Check cache
    try:
        cache.set('health_check', 'ok', 10)
        cache.get('health_check')
        cache_status = "healthy"
    except Exception as e:
        logger.error(f"Cache health check failed: {str(e)}")
        cache_status = "unhealthy"

    return JsonResponse({
        'status': 'healthy',
        'database': db_status,
        'cache': cache_status,
        'timestamp': timezone.now().isoformat()
    })


@require_http_methods(["GET"])
@csrf_exempt
def detailed_health_check(request):
    """
    Detailed health check with system metrics
    Includes CPU, memory, disk usage, and application metrics
    """
    health_status = {
        'status': 'healthy',
        'timestamp': timezone.now().isoformat(),
        'system': {},
        'database': {},
        'cache': {},
        'application': {}
    }

    # System metrics
    try:
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        health_status['system']['cpu'] = {
            'usage_percent': cpu_percent,
            'status': 'healthy' if cpu_percent < 80 else 'warning'
        }

        # Memory usage
        memory = psutil.virtual_memory()
        health_status['system']['memory'] = {
            'total_gb': round(memory.total / (1024**3), 2),
            'available_gb': round(memory.available / (1024**3), 2),
            'usage_percent': memory.percent,
            'status': 'healthy' if memory.percent < 80 else 'warning'
        }

        # Disk usage
        disk = psutil.disk_usage('/')
        health_status['system']['disk'] = {
            'total_gb': round(disk.total / (1024**3), 2),
            'free_gb': round(disk.free / (1024**3), 2),
            'usage_percent': disk.percent,
            'status': 'healthy' if disk.percent < 80 else 'warning'
        }

    except Exception as e:
        logger.error(f"System metrics collection failed: {str(e)}")
        health_status['system']['error'] = str(e)

    # Database metrics
    try:
        with connection.cursor() as cursor:
            # Check connection count
            cursor.execute("""
                SELECT count(*) FROM pg_stat_activity
                WHERE datname = current_database()
            """)
            db_connections = cursor.fetchone()[0]

            # Check database size
            cursor.execute("""
                SELECT pg_size_pretty(pg_database_size(current_database()))
            """)
            db_size = cursor.fetchone()[0]

            health_status['database'] = {
                'connections': db_connections,
                'size': db_size,
                'status': 'healthy'
            }

    except Exception as e:
        logger.error(f"Database metrics collection failed: {str(e)}")
        health_status['database'] = {
            'status': 'unhealthy',
            'error': str(e)
        }

    # Cache metrics
    try:
        # Test cache operations
        cache.set('health_check_test', 'test_value', 10)
        cache.get('health_check_test')

        health_status['cache'] = {
            'status': 'healthy',
            'backend': settings.CACHES['default']['BACKEND']
        }

    except Exception as e:
        logger.error(f"Cache metrics collection failed: {str(e)}")
        health_status['cache'] = {
            'status': 'unhealthy',
            'error': str(e)
        }

    # Application metrics
    try:
        # Get application uptime (approximate from process start time)
        process = psutil.Process()
        create_time = datetime.fromtimestamp(process.create_time())
        uptime = datetime.now() - create_time

        health_status['application'] = {
            'uptime_seconds': uptime.total_seconds(),
            'uptime_human': str(uptime).split('.')[0],  # Remove microseconds
            'debug_mode': settings.DEBUG,
            'environment': getattr(settings, 'ENVIRONMENT', 'development')
        }

    except Exception as e:
        logger.error(f"Application metrics collection failed: {str(e)}")
        health_status['application']['error'] = str(e)

    # Determine overall status
    if any(component.get('status') == 'unhealthy' for component in [
        health_status['database'],
        health_status['cache']
    ]):
        health_status['status'] = 'unhealthy'
        status_code = 503
    elif any(component.get('status') == 'warning' for component in [
        health_status['system'].get('cpu', {}),
        health_status['system'].get('memory', {}),
        health_status['system'].get('disk', {})
    ]):
        health_status['status'] = 'warning'
        status_code = 200  # Still return 200 for warnings
    else:
        status_code = 200

    return JsonResponse(health_status, status=status_code)


@require_http_methods(["GET"])
@csrf_exempt
def metrics(request):
    """
    Prometheus-style metrics endpoint
    Returns application metrics in text format
    """
    metrics_data = []

    # System metrics
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()

    metrics_data.append(f'# HELP system_cpu_percent CPU usage percentage')
    metrics_data.append(f'# TYPE system_cpu_percent gauge')
    metrics_data.append(f'system_cpu_percent {cpu_percent}')

    metrics_data.append(f'# HELP system_memory_percent Memory usage percentage')
    metrics_data.append(f'# TYPE system_memory_percent gauge')
    metrics_data.append(f'system_memory_percent {memory.percent}')

    # Application metrics (you can add more custom metrics here)
    metrics_data.append(f'# HELP app_requests_total Total number of requests')
    metrics_data.append(f'# TYPE app_requests_total counter')
    metrics_data.append(f'app_requests_total {get_request_count()}')

    metrics_data.append(f'# HELP app_active_users Total number of active users')
    metrics_data.append(f'# TYPE app_active_users gauge')
    metrics_data.append(f'app_active_users {get_active_user_count()}')

    return JsonResponse({
        'metrics': '\n'.join(metrics_data)
    }, content_type='text/plain')


def get_request_count():
    """Get total request count from cache or database"""
    cache_key = 'total_request_count'
    count = cache.get(cache_key)

    if count is None:
        # Initialize counter
        count = 0
        cache.set(cache_key, count)

    return count


def get_active_user_count():
    """Get number of active users from database"""
    from api.models import AuthUser
    from django.utils import timezone
    from datetime import timedelta

    # Count users active in last 30 minutes
    thirty_minutes_ago = timezone.now() - timedelta(minutes=30)

    try:
        active_count = AuthUser.objects.filter(
            last_login__gte=thirty_minutes_ago,
            is_active=True
        ).count()

        return active_count
    except Exception as e:
        logger.error(f"Failed to get active user count: {str(e)}")
        return 0


class MetricsMiddleware:
    """
    Middleware to collect application metrics
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Record request start time
        start_time = time.time()

        # Process request
        response = self.get_response(request)

        # Calculate request duration
        duration = time.time() - start_time

        # Update metrics
        self.update_request_metrics(request, response, duration)

        return response

    def update_request_metrics(self, request, response, duration):
        """Update request metrics in cache"""
        try:
            # Increment total request count
            cache_key = 'total_request_count'
            count = cache.get(cache_key, 0) + 1
            cache.set(cache_key, count, timeout=3600)  # Keep for 1 hour

            # Log slow requests
            if duration > 2.0:
                logger.warning(
                    f"Slow request detected: {request.method} {request.path} "
                    f"took {duration:.2f}s and returned {response.status_code}"
                )

        except Exception as e:
            logger.error(f"Failed to update metrics: {str(e)}")


def monitor_system_health():
    """
    Background task to monitor system health and send alerts
    Should be called periodically (e.g., every 5 minutes)
    """
    warnings = []
    errors = []

    # Check CPU usage
    cpu_percent = psutil.cpu_percent(interval=1)
    if cpu_percent > 90:
        errors.append(f"Critical CPU usage: {cpu_percent}%")
    elif cpu_percent > 75:
        warnings.append(f"High CPU usage: {cpu_percent}%")

    # Check memory usage
    memory = psutil.virtual_memory()
    if memory.percent > 90:
        errors.append(f"Critical memory usage: {memory.percent}%")
    elif memory.percent > 75:
        warnings.append(f"High memory usage: {memory.percent}%")

    # Check disk usage
    disk = psutil.disk_usage('/')
    if disk.percent > 90:
        errors.append(f"Critical disk usage: {disk.percent}%")
    elif disk.percent > 75:
        warnings.append(f"High disk usage: {disk.percent}%")

    # Log warnings and errors
    if warnings:
        logger.warning(f"System health warnings: {'; '.join(warnings)}")

    if errors:
        logger.error(f"System health errors: {'; '.join(errors)}")

    return {
        'warnings': warnings,
        'errors': errors,
        'status': 'healthy' if not errors else 'unhealthy'
    }


# Example usage in urls.py:
"""
from api.monitoring import health_check, detailed_health_check, metrics

urlpatterns = [
    path('health/', health_check, name='health_check'),
    path('health/detailed/', detailed_health_check, name='detailed_health_check'),
    path('metrics/', metrics, name='metrics'),
]
"""