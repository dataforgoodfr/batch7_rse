release: cd webapp && python manage.py populate_db --settings batch7rse.settings.dev --task model --mode final
web: cd webapp && gunicorn batch7rse.wsgi