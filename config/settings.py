"""
UNIGEST - Settings Django
File: config/settings.py
Descrizione: Configurazione principale del progetto Django UNIGEST
"""

from pathlib import Path
from decouple import config, Csv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=False, cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=Csv())

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # App di terze parti
    'widget_tweaks',  # Per migliorare i form
    'django_filters',  # Per filtrare dati
    'debug_toolbar',  # Per debug in sviluppo
    'dbbackup',  # Per backup database
    
    # App del progetto
    'core',  # App principale UNIGEST
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    
    # Debug toolbar (solo in sviluppo)
    'debug_toolbar.middleware.DebugToolbarMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'core' / 'templates',  # Template dell'app core
            BASE_DIR / 'templates',  # Template globali (se necessario)
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                
                # Context processor personalizzato per dati globali
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'core.context_processors.anno_accademico_corrente',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Database configuration
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

# Database principale UNIGEST (nuovo)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='3306'),
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    },
    # Database vecchio (per migrazione dati)
    'old_database': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': config('OLD_DB_NAME'),
        'USER': config('OLD_DB_USER'),
        'PASSWORD': config('OLD_DB_PASSWORD'),
        'HOST': config('OLD_DB_HOST', default='localhost'),
        'PORT': config('OLD_DB_PORT', default='3306'),
        'OPTIONS': {
            'charset': 'utf8',
        },
    }
}

# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = []

# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = config('LANGUAGE_CODE', default='it-it')

TIME_ZONE = config('TIME_ZONE', default='Europe/Rome')

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'  # Dove Django raccoglie i file statici in produzione

STATICFILES_DIRS = [
    BASE_DIR / 'core' / 'static',  # File statici dell'app core
    BASE_DIR / 'static',  # File statici globali (se necessario)
]

# Media files (Upload utenti)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Configurazione per formati data/ora italiani
DATE_FORMAT = 'd/m/Y'
DATETIME_FORMAT = 'd/m/Y H:i'
SHORT_DATE_FORMAT = 'd/m/Y'
DATE_INPUT_FORMATS = ['%d/%m/%Y', '%Y-%m-%d']
DATETIME_INPUT_FORMATS = ['%d/%m/%Y %H:%M', '%Y-%m-%d %H:%M']

# Configurazione separatori decimali italiani
USE_THOUSAND_SEPARATOR = True
THOUSAND_SEPARATOR = '.'
DECIMAL_SEPARATOR = ','

# Configurazione email (per notifiche future)
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')

# Configurazione Django Debug Toolbar
INTERNAL_IPS = [
    '127.0.0.1',
    'localhost',
]

# Configurazione backup database
DBBACKUP_STORAGE = 'django.core.files.storage.FileSystemStorage'
DBBACKUP_STORAGE_OPTIONS = {'location': BASE_DIR / 'backups'}

# Configurazione Admin
ADMIN_SITE_HEADER = "UNIGEST - Amministrazione"
ADMIN_SITE_TITLE = "UNIGEST Admin"
ADMIN_INDEX_TITLE = "Benvenuto nel pannello di amministrazione UNIGEST"

# Configurazione paginazione (numero di elementi per pagina)
PAGINATION_PER_PAGE = 50

# Configurazione sessioni
SESSION_COOKIE_AGE = 86400  # 24 ore in secondi
SESSION_SAVE_EVERY_REQUEST = True

# Logging (per tracciare errori e attività)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'unigest.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'core': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}
