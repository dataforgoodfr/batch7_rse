from django.utils.translation import gettext_lazy as _
from django import forms
from .models import ActivitySector as Sectors, File
import datetime


class ImportRSEForm(forms.Form):
    company_name = forms.CharField(label=_("Company Name"), max_length=50)
    sector = forms.ChoiceField(label=_("Company sector"), choices=Sectors.objects.all())
    company_introduction = forms.Textarea()  # label="Introduce your company", required=False)
    company_files = forms.FileField()
    file_year = forms.DateField(initial=datetime.date(year=2018, month=1, day=1),
                                required=False)
    file_type = forms.ChoiceField(label=_("File type"), choices=File.FileType.choices)
    start_rse_page = forms.IntegerField(label="Page where RSE part begins")
    end_rse_page = forms.IntegerField(label="Page where RSE part ends")

