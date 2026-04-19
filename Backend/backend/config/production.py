"""
Production Configuration
Production environment settings with maximum security
"""
from .base import *

# Security
DEBUG = False
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '').split(',') if os.getenv('ALLOWED_HOSTS') else []

# Security Headers
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Frame Options
X_FRAME_OPTIONS = 'DENY'

# CORS (production domains only)
CORS_ALLOWED_ORIGINS = os.getenv('CORS_ALLOWED_ORIGINS', '').split(',') if os.getenv('CORS_ALLOWED_ORIGINS') else []
CORS_ALLOW_CREDENTIALS = True

# Database (production database with connection pooling)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'fusion_prod'),
        'USER': os.getenv('DB_USER', 'postgres'),
        'PASSWORD': os.getenv('DB_PASSWORD', ''),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
        'OPTIONS': {
            'connect_timeout': 10,
            'sslmode': 'require',  # Require SSL in production
        },
        'CONN_MAX_AGE': 600,  # Connection pooling (10 minutes)
        'ATOMIC_REQUESTS': True,  # Atomic requests for data integrity
    }
}

# Email (production email backend)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@fusion.edu')
SERVER_EMAIL = os.getenv('SERVER_EMAIL', 'server@fusion.edu')
EMAIL_TEST_MODE = False

# Cache (Redis for production)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True,
            },
        },
        'KEY_PREFIX': 'fusion_prod',
        'TIMEOUT': 300,
    }
}

# Session (database-backed sessions with Redis cache)
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

# Logging (file-based for production)
import sys
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
        'json': {
            'format': '{"level": "%(levelname)s", "time": "%(asctime)s", "module": "%(module)s", "message": "%(message)s"}',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'maxBytes': 1024 * 1024 * 10,  # 10MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'error_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'django-error.log',
            'maxBytes': 1024 * 1024 * 10,  # 10MB
            'backupCount': 10,
            'formatter': 'verbose',
            'level': 'ERROR',
        },
    },
    'root': {
        'handlers': ['console', 'file', 'error_file'],
        'level': 'INFO',
    },
    'django': {
        'handlers': ['console', 'file'],
        'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
        'propagate': False,
    },
    'django.security': {
        'handlers': ['error_file'],
        'level': 'WARNING',
        'propagate': False,
    },
}

# JWT (shorter lifetimes for production security)
from datetime import timedelta
SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'] = timedelta(minutes=15)
SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'] = timedelta(days=1)
SIMPLE_JWT['BLACKLIST_AFTER_ROTATION'] = True

# Rate limiting (enabled in production)
RATE_LIMIT_ENABLED = True
RATE_LIMIT_RATE = '100/hour'  # 100 requests per hour per user
RATE_LIMIT_SCOPE = 'user'

# Login lockout (enabled in production)
LOGIN_LOCKOUT_ENABLED = True
MAX_FAILED_LOGIN_ATTEMPTS = 5
FAILED_LOGIN_ATTEMPT_DURATION = 900  # 15 minutes

# Static files (whitenoise for production)
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files (use cloud storage in production)
# DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

# Security middleware
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Performance optimization
CONN_MAX_AGE = 600  # Persistent database connections

# Monitoring
SENTRY_DSN = os.getenv('SENTRY_DSN', '')
if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration()],
        traces_sample_rate=0.1,
        send_default_pii=False
    )

# Environment label
ENVIRONMENT = 'production'