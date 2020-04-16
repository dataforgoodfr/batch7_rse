from django.contrib import admin

from .models import Company, File, Sentence

admin.site.register(Company)
admin.site.register(File)
admin.site.register(Sentence)
