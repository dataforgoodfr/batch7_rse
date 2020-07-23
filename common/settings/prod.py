from common.settings.base import *
try:
    from common.settings.credentials import DB_NAME, DB_USERNAME, DB_PASSWORD, DB_HOST, DB_PORT
except:
    # env injection from clever cloud
    DB_NAME = os.getenv("DB_NAME")
    DB_USERNAME = os.getenv("DB_USERNAME")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = os.getenv("DB_PORT")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = 'DEBUG' in os.environ
print(DEBUG)
DEBUG = True

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
