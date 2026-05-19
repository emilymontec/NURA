# nura/settings.py
"""Django settings for NURA project.
Generated with modular structure and environment variable support.
"""
import os
from pathlib import Path
from urllib.parse import unquote, urlparse
from dotenv import load_dotenv

# Load .env variables
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'unsafe-secret-key')
DEBUG = os.getenv('DJANGO_DEBUG', 'True') == 'True'
ALLOWED_HOSTS = os.getenv('DJANGO_ALLOWED_HOSTS', '*').split(',')

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Local apps
    'analytics',
    'ai',
    'chat',
    'corsheaders',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

CORS_ALLOW_ALL_ORIGINS = True

ROOT_URLCONF = 'nura.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'templates',
            BASE_DIR.parent / 'frontend',
            BASE_DIR.parent / 'frontend' / 'views',
        ],
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

WSGI_APPLICATION = 'nura.wsgi.application'

SUPABASE_DB_URL = os.getenv('SUPABASE_DB_URL', '').strip()
USE_SQLITE_LOCAL = os.getenv('USE_SQLITE_LOCAL', 'False').lower() == 'true'
SQLITE_DB_PATH = os.getenv('SQLITE_DB_PATH', str(BASE_DIR / 'db.sqlite3'))

if USE_SQLITE_LOCAL:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': SQLITE_DB_PATH,
        }
    }
elif SUPABASE_DB_URL:
    parsed_db_url = urlparse(SUPABASE_DB_URL)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': parsed_db_url.path.lstrip('/'),
            'USER': unquote(parsed_db_url.username or ''),
            'PASSWORD': unquote(parsed_db_url.password or ''),
            'HOST': parsed_db_url.hostname or '',
            'PORT': parsed_db_url.port or '5432',
            'CONN_MAX_AGE': int(os.getenv('DB_CONN_MAX_AGE', '60')),
            'OPTIONS': {
                'sslmode': os.getenv('POSTGRES_SSLMODE', 'require'),
            },
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': os.getenv('POSTGRES_ENGINE', 'django.db.backends.sqlite3'),
            'NAME': os.getenv('POSTGRES_DB', SQLITE_DB_PATH),
            'USER': os.getenv('POSTGRES_USER', ''),
            'PASSWORD': os.getenv('POSTGRES_PASSWORD', ''),
            'HOST': os.getenv('POSTGRES_HOST', ''),
            'PORT': os.getenv('POSTGRES_PORT', ''),
        }
    }

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    ('assets', BASE_DIR.parent / 'frontend' / 'assets'),
    ('styles', BASE_DIR.parent / 'frontend' / 'styles'),
    ('scripts', BASE_DIR.parent / 'frontend' / 'scripts'),
]

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
