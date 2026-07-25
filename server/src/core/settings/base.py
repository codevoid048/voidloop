import os
import sys
from pathlib import Path
import dj_database_url

# Add the parent directory to Python path to allow absolute imports starting with 'src'
sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))

from config import config

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = config.secret_key
DEBUG = config.debug

ALLOWED_HOSTS = config.allowed_hosts_list

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third Party
    'corsheaders',
    'ninja',
    'ninja_jwt',
    'storages',

    # SDK & Infrastructure
    '_sdk',

    # Local Apps
    'users',
    'habits',
    'tasks',
    'notes',
    'stats',
]

MIDDLEWARE = [
    # CORS (EARLY - before other middleware)
    'corsheaders.middleware.CorsMiddleware',

    # Security Headers (Django built-in)
    'django.middleware.security.SecurityMiddleware',

    # Request Context (business-specific: sets request ID, timing, audit context)
    '_sdk.middleware.RequestContextMiddleware',

    # Session & Request Processing
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'ninja.compatibility.files.fix_request_files_middleware',
    'django.middleware.csrf.CsrfViewMiddleware',

    # Authentication (Django's built-in)
    'django.contrib.auth.middleware.AuthenticationMiddleware',

    # Messages & Security
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'
WSGI_APPLICATION = 'core.wsgi.application'
ASGI_APPLICATION = 'core.asgi.application'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

DATABASES = {
    'default': dj_database_url.parse(config.db.url.strip('"'), conn_max_age=600)
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Django storage configuration: keep static local, optionally move media to S3.
STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage',
    },
}

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Media config
if config.aws.use_s3:
    AWS_STORAGE_BUCKET_NAME = config.aws.s3_bucket_name
    AWS_S3_REGION_NAME = config.aws.s3_region_name
    AWS_S3_CUSTOM_DOMAIN = config.aws.cloudfront_domain or (
        f"{AWS_STORAGE_BUCKET_NAME}.s3.{AWS_S3_REGION_NAME}.amazonaws.com"
    )
    AWS_S3_OBJECT_PARAMETERS = {'CacheControl': 'max-age=86400'}
    AWS_DEFAULT_ACL = None
    AWS_QUERYSTRING_AUTH = False
    AWS_S3_FILE_OVERWRITE = False

    STORAGES['default'] = {'BACKEND': '_sdk.storages.MediaStorage'}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom User Model (Must be set before authentication system is initialized)
AUTH_USER_MODEL = 'users.User'

CORS_ALLOWED_ORIGINS = config.cors_allowed_origins_list
CORS_ALLOW_CREDENTIALS = True


# Logging Best Practices Configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            '()': '_sdk.logging.JsonLogFormatter',
        },
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'json',
        },
        'audit': {
            'level': 'INFO',
            'class': 'logging.StreamHandler', # In prod, stream to DataDog or CloudWatch
            'formatter': 'json',
        }
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
        'audit_logger': {
            'handlers': ['audit'],
            'level': 'INFO',
            'propagate': False,
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    }
}

# JWT Configuration
NINJA_JWT = {
    'ACCESS_TOKEN_LIFETIME': config.jwt.access_token_lifetime,
    'REFRESH_TOKEN_LIFETIME': config.jwt.refresh_token_lifetime,
    'ROTATE_REFRESH_TOKENS': config.jwt.rotate_refresh_tokens,
    'BLACKLIST_AFTER_ROTATION': config.jwt.blacklist_after_rotation,
    'ALGORITHM': config.jwt.algorithm,
    'SIGNING_KEY': config.jwt.secret_key,  # Different from Django SECRET_KEY for security
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,
    'JSON_ENCODER': None,
    'JWK_URL': None,
    'LEEWAY': 0,

    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'USER_AUTHENTICATION_RULE': 'ninja_jwt.authentication.default_user_authentication_rule',

    'AUTH_TOKEN_CLASSES': ('ninja_jwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    'TOKEN_USER_CLASS': 'ninja_jwt.models.TokenUser',

    'JTI_CLAIM': 'jti',

    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': config.jwt.access_token_lifetime,
    'SLIDING_TOKEN_REFRESH_LIFETIME': config.jwt.refresh_token_lifetime,

    'TOKEN_OBTAIN_SERIALIZER': 'ninja_jwt.serializers.TokenObtainPairSerializer',
    'TOKEN_REFRESH_SERIALIZER': 'ninja_jwt.serializers.TokenRefreshSerializer',
    'TOKEN_VERIFY_SERIALIZER': 'ninja_jwt.serializers.TokenVerifySerializer',
    'TOKEN_BLACKLIST_SERIALIZER': 'ninja_jwt.serializers.TokenBlacklistSerializer',
    'SLIDING_TOKEN_OBTAIN_SERIALIZER': 'ninja_jwt.serializers.TokenObtainSlidingSerializer',
    'SLIDING_TOKEN_REFRESH_SERIALIZER': 'ninja_jwt.serializers.TokenRefreshSlidingSerializer',
}
