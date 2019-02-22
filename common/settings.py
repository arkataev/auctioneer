import os

VERSION = 2.0

# ENV's
SENTRY_DSN = os.getenv('SENTRY_DSN', '')
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'amqp://')
DB_NAME = os.getenv('POSTGRES_DB', 'auctioneer')
DB_USER = os.getenv('POSTGRES_USER', 'aleksandr.kataev')
DB_PASSWORD = os.getenv('POSTGRES_PASSWORD', '')
DB_HOST = os.getenv('POSTGRES_HOST', 'localhost')
DB_PORT = int(os.getenv('POSTGRES_PORT', '5432'))
CALLBACK_HOST = os.getenv('CALLBACK_HOST', 'localhost:8000')
DEBUG = os.getenv('DEBUG', True)
# Yandex direct API auth settings
YD_CLIENT_ID = os.getenv('YD_CLIENT_ID')
YD_CLIENT_SECRET = os.getenv('YD_CLIENT_SECRET')

# CELERY SETUP
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'
DJANGO_CELERY_BEAT_TZ_AWARE = True
CELERY_RESULT_BACKEND = 'django-db'
TASK_ROUTES = {
    'calculate_keyword_bids': {'queue': 'keyword_bids'},
}
TASK_DEFAULT_RETRIES = 3

# Base
SECRET_KEY = 'wdz8^p(v%#41)uiluzg@4^s9n@&)t-3gy2r+t3^be2-)m9@kn2'
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ALLOWED_HOSTS = ['*']
TIME_ZONE = 'Europe/Moscow'
USE_TZ = True
DATETIME_FORMAT = 'j N Y H:i:s'

# Web
ROOT_URLCONF = 'common.urls'

# DB
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': DB_NAME,
        'USER': DB_USER,
        'PASSWORD': DB_PASSWORD,
        'HOST': DB_HOST,
        'PORT': DB_PORT,
    }
}

# Static
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [],
    'APP_DIRS': False,
    'OPTIONS': {
        'context_processors': [
            'django.template.context_processors.debug',
            'django.template.context_processors.media',
            'django.template.context_processors.request',
            'django.contrib.auth.context_processors.auth',
            'django.contrib.messages.context_processors.messages',
        ],
        'loaders': [
            'django.template.loaders.filesystem.Loader',
            'django.template.loaders.app_directories.Loader'
        ],
    },
}]

# Apps and middleware
INSTALLED_APPS = [
    'common',
    'common.account',
    'admin_interface',
    'colorfield',
    'common.task_runner',
    'common.reporter',
    'auctioneer',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_celery_results',
    'django_celery_beat',
    'raven.contrib.django.raven_compat'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Logging
LOGGING = {
    'version': 1,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'full_info',
        },
        'console_json': {
            'class': 'logging.StreamHandler',
            'formatter': 'json',
        },
    },
    'formatters': {
        'full_info': {
            'format': '[%(asctime)s] [%(levelname)-5s] %(filename)s:%(lineno)d [%(name)s] - %(message)s',
        },
        'limited_info': {
            'format': '[%(asctime)s] [%(levelname)-5s] - %(message)s',
        },
        'json': {
            '()': 'common.logger.ElasticJsonFormatter',
            'format': '%(levelname)s %(asctime)s %(message)s',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'console_json'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'django.template': {
            'handlers': ['console', 'console_json'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['console', 'console_json'],
            'level': 'WARNING',
            'propagate': False,
        },
        'common': {
            'handlers': ['console', 'console_json'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'auctioneer': {
            'handlers': ['console', 'console_json'],
            'level': 'DEBUG',
            'propagate': False,
        },
    }
}
