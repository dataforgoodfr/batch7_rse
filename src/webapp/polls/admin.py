from django.contrib import admin

from .models import Company, File, Sentence, ActivitySector

admin.site.register(Company)
admin.site.register(File)
admin.site.register(Sentence)
admin.site.register(ActivitySector)
