from batch7rse.settings.base import *
from batch7rse.settings.credentials import DB_NAME, DB_USERNAME, DB_PASSWORD, DB_HOST, DB_PORT

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = 'DEBUG' in os.environ

# Activate Django-Heroku, this will set DATABASES['default'] and ALLOWED_HOSTS
# django_heroku.settings(locals())

# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': DB_NAME,
        'USER': DB_USERNAME,
        'PASSWORD': DB_PASSWORD,
        'HOST': DB_HOST,
        'PORT': DB_PORT,  # default will be selected
    }
}
