from batch7rse.settings.base import *
from batch7rse.settings.credentials import DB_PASSWORD

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['127.0.0.1', 'localhost']


# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
#         'OPTIONS': {
#             'timeout': 25, # in seconds
#         },
#     }
# }

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'dpef_db',
        'USER': 'batch7rse',
        'PASSWORD': DB_PASSWORD,
        'HOST': 'localhost',
        'PORT': '',  # default will be selected
    }
}