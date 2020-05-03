from django.contrib import admin

from .models import Company, DPEF, Sentence, ActivitySector

admin.site.register(Company)
admin.site.register(DPEF)
admin.site.register(Sentence)
admin.site.register(ActivitySector)
