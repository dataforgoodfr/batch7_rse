from batch7rse.settings.base import *
import django_heroku

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = ['dataforgood.renauddha.ovh', 'rse-explorer.herokuapp.com']

# Activate Django-Heroku.
django_heroku.settings(locals())

# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
#         'OPTIONS': {
#             'timeout': 25, # in seconds
#         }
#     }
# }
