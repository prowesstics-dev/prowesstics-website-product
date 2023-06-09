"""
Django settings for prowesstics project.

Generated by 'django-admin startproject' using Django 3.2.4.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.2/ref/settings/
"""
import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-ymjjw^q$u_p=ovtc=ne9lcgs823nk5ur3433sb&3_qh6xm(7b%'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['www.prowesstics.com','*']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'sweetify',
    'ckeditor_uploader',
    'ckeditor',
    'lms',
    'dashboard',
    'payroll',
    "django_apscheduler",

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

ROOT_URLCONF = 'prowesstics.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'lms.context_processor.check_for_new_msg',
                'lms.context_processor.name_x',
                'lms.context_processor.notifications'
            ],
        },
    },
]

WSGI_APPLICATION = 'prowesstics.wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases


# server mysql
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.mysql',
#         'NAME': 'imran06$prowesstics',
#         'USER': 'imran06',
#         'PASSWORD': 'Cyberpunk@123',
#         'HOST': 'imran06.mysql.pythonanywhere-services.com',
#     }
# }

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'lms',
        'USER': 'root',
        'PASSWORD': 'admin',
        'HOST': 'localhost',
        'PORT': '3306',
    }
}

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': 'lms',
#         'USER': 'postgres',
#         'PASSWORD': 'admin',
#         'HOST': 'localhost'
#     }
# }

# server mysql connection pool #old
# DATABASES = {
#     'default': {
#         'ENGINE': 'dj_db_conn_pool.backends.mysql',
#         'NAME': 'imran06$prowesstics',
#         'USER': 'imran06',
#         'PASSWORD': 'Cyberpunk@123',
#         'HOST': 'imran06.mysql.pythonanywhere-services.com',
#         'POOL_OPTIONS': {
#             'POOL_SIZE': 20,
#             'MAX_OVERFLOW': 0
#         }
#     }
# }



# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

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

AUTH_USER_MODEL = 'lms.User'

# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE =  'Asia/Kolkata'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# mail send
DEFAULT_FROM_EMAIL = 'mohanakku0001@gmail.com'
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_USE_TLS = True
'''
# sendinblue
EMAIL_HOST = 'smtp-relay.sendinblue.com'
EMAIL_HOST_USER = 'sudhakar.v@prowesstics.com'
EMAIL_HOST_PASSWORD = 'kFVbTAt8GRsEqZz6'
'''
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_HOST_USER = 'mohanakku0001@gmail.com'
EMAIL_HOST_PASSWORD = 'schtgbzabxqhhegp'

EMAIL_PORT = 587




# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/

STATIC_URL = '/static/'

STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'static'),
)

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
X_FRAME_OPTIONS = 'SAMEORIGIN'

CKEDITOR_UPLOAD_PATH = "uploads/"
CKEDITOR_BASEPATH = "/static/ckeditor/ckeditor/"
APSCHEDULER_DATETIME_FORMAT = "N j, Y, f:s a"
SCHEDULER_AUTOSTART = False
