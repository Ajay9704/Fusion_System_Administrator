"""
Development Configuration
Local development environment settings
"""
from .base import *

# Security
DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'testserver']

# Development CORS (more permissive)
CORS_ALLOWED_ORIGINS = [
    'http://localhost:5173',
    'http://127.0.0.1:5173',
    'http://localhost:3000',
    'http://127.0.0.1:3000',
]

# Database (development database)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'fusion_dev'),
        'USER': os.getenv('DB_USER', 'postgres'),
        'PASSWORD': os.getenv('DB_PASSWORD', ''),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
        'OPTIONS': {
            'connect_timeout': 10,
        }
    }
}

# Email (console backend for development)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
EMAIL_TEST_MODE = True
EMAIL_TEST_USER = 'test@example.com'

# Cache (use memory cache in development)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

# Logging (verbose for development)
LOGGING['handlers']['console']['level'] = 'DEBUG'
LOGGING['django']['level'] = 'DEBUG'

# Debug Toolbar
try:
    import debug_toolbar
    INSTALLED_APPS.append('debug_toolbar')
    MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')
    INTERNAL_IPS = ['127.0.0.1', 'localhost']
except ImportError:
    pass

# JWT (longer lifetimes for development)
SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'] = timedelta(hours=24)
SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'] = timedelta(days=30)

# Rate limiting (disabled in development)
RATE_LIMIT_ENABLED = False

# Login lockout (disabled in development)
LOGIN_LOCKOUT_ENABLED = False
MAX_FAILED_LOGIN_ATTEMPTS = 5
FAILED_LOGIN_ATTEMPT_DURATION = 300  # 5 minutes

# Environment label
ENVIRONMENT = 'development'