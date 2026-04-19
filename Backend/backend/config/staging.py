"""
Staging Configuration
Staging environment for pre-production testing
"""
from .base import *

# Security
DEBUG = False
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '').split(',') if os.getenv('ALLOWED_HOSTS') else []

# Moderate security for staging
SECURE_SSL_REDIRECT = False  # May not have SSL in staging
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# CORS (staging domains)
CORS_ALLOWED_ORIGINS = os.getenv('CORS_ALLOWED_ORIGINS', '').split(',') if os.getenv('CORS_ALLOWED_ORIGINS') else []
CORS_ALLOW_CREDENTIALS = True

# Database (staging database)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'fusion_staging'),
        'USER': os.getenv('DB_USER', 'postgres'),
        'PASSWORD': os.getenv('DB_PASSWORD', ''),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
        'OPTIONS': {
            'connect_timeout': 10,
        },
        'CONN_MAX_AGE': 600,
        'ATOMIC_REQUESTS': True,
    }
}

# Email (console for testing)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
EMAIL_TEST_MODE = True
EMAIL_TEST_USER = 'staging@example.com'

# Cache (Redis for staging)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/2'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'fusion_staging',
        'TIMEOUT': 300,
    }
}

# Logging (verbose for staging)
LOGGING['handlers']['file'] = {
    'class': 'logging.handlers.RotatingFileHandler',
    'filename': BASE_DIR / 'logs' / 'staging.log',
    'maxBytes': 1024 * 1024 * 10,
    'backupCount': 5,
    'formatter': 'verbose',
}
LOGGING['django']['level'] = 'INFO'

# JWT (medium lifetimes for staging)
from datetime import timedelta
SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'] = timedelta(hours=4)
SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'] = timedelta(days=7)

# Rate limiting (enabled but more lenient)
RATE_LIMIT_ENABLED = True
RATE_LIMIT_RATE = '200/hour'  # 200 requests per hour per user
RATE_LIMIT_SCOPE = 'user'

# Login lockout (enabled)
LOGIN_LOCKOUT_ENABLED = True
MAX_FAILED_LOGIN_ATTEMPTS = 10  # More attempts for testing
FAILED_LOGIN_ATTEMPT_DURATION = 600  # 10 minutes

# Environment label
ENVIRONMENT = 'staging'

# Debug tools (optional in staging)
try:
    import debug_toolbar
    INSTALLED_APPS.append('debug_toolbar')
    MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')
    INTERNAL_IPS = ['127.0.0.1']
except ImportError:
    pass