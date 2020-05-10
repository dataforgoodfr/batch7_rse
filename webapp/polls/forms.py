from django.utils.translation import gettext_lazy as _
from django import forms
from polls.models import ActivitySector as Sectors
from datetime import date
from polls.models import Company

class BasicSearchForm(forms.Form):
    search_bar = forms.CharField(label=_("Rechercher"), max_length="100", required=True)


class SearchForm(BasicSearchForm):
    start_period = forms.IntegerField(label=_("De"), min_value=1990, max_value=date.today().year + 1, required=False)
    end_period = forms.IntegerField(label=_("à"), min_value=1990, max_value=date.today().year + 1, required=False)
    sectors = forms.MultipleChoiceField(choices=[(sector.id, sector.name) for sector in Sectors.objects.all()],
                                        widget=forms.CheckboxSelectMultiple, required=False)

    def _is_period_valid(self):
        try:
            if self.start_period and self.end_period:
                if self.start_period > self.end_period:
                    return False
            return True
        except AttributeError:
            return True

    def is_valid(self):
        return self._is_period_valid()

    def get_response(self):
        companies =