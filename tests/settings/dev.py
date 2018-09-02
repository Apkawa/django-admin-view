import os
import sys

DEBUG = True

SITE_ID = 1

TEST_ROOT = os.path.normcase(os.path.dirname(os.path.abspath(__file__)))

sys.path.insert(0, os.path.abspath(os.path.join(TEST_ROOT, '..', '..')))

FIXTURES_ROOT = os.path.join(TEST_ROOT, 'fixtures')

MEDIA_ROOT = os.path.join('/tmp/', 'media')
MEDIA_URL = '/media/'

STATIC_ROOT = os.path.join('/tmp/', 'static')
STATIC_URL = '/static/'

STATICFILES_DIRS = (
    os.path.join(TEST_ROOT, '..' 'static'),
    # ('frontend', os.path.join(FRONTEND_ROOT, 'dist'))
)

# https://docs.djangoproject.com/en/1.10/ref/contrib/staticfiles/#staticfiles-finders
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)

DATABASE_ENGINE = 'sqlite3'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(TEST_ROOT, 'db.sqlite3'),
    }
}

INSTALLED_APPS = [
    'django.contrib.sessions',
    'django.contrib.contenttypes',
    'django.contrib.sites',
    'django.contrib.auth',
    'django.contrib.admin',
    'django.contrib.staticfiles',

    'easy_thumbnails',
    'django_filters',

    'admin_view',
    'tests',

]

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(TEST_ROOT, 'templates')],
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

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)

# This is only needed for the 1.4.X test environment
USE_TZ = True

SECRET_KEY = 'easy'
ROOT_URLCONF = 'tests.urls'
