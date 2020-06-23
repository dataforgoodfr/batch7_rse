from batch7rse.settings.base import *
import django_heroku

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = 'DEBUG' in os.environ

# Activate Django-Heroku, this will set DATABASES['default'] and ALLOWED_HOSTS
django_heroku.settings(locals())

# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases
