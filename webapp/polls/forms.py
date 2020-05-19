from django.utils.translation import gettext_lazy as _
from django import forms
from polls.models import ActivitySector as Sectors, Company, Sentence
from datetime import date
from polls.models import Company

class CompanyForm(forms.Form):
    company_name = forms.CharField(label=_("Nom de l'entreprise"), max_length=100, required=False)
    sector_list = [(sector.id, sector.name) for sector in Sectors.objects.all()]
    sectors = forms.MultipleChoiceField(choices=sector_list, initial=[s[0] for s in sector_list],
                                        widget=forms.CheckboxSelectMultiple, required=False)

    def filter_company(self):
        try:
            companies = Company.objects.all().filter(name=self.cleaned_data['company_name'])
        except AttributeError:
            companies = Company.objects.all()
        # TODO: add filter for sectors
        return companies


class BasicSearchForm(forms.Form):
    search_bar = forms.CharField(label=_("Rechercher"), max_length="100", required=True)


class SearchForm(BasicSearchForm):
    start_period = forms.IntegerField(label=_("De"), min_value=1990, max_value=date.today().year + 1, required=False)
    end_period = forms.IntegerField(label=_("à"), min_value=1990, max_value=date.today().year + 1, required=False)
    sector_list = [(sector.id, sector.name) for sector in Sectors.objects.all()]
    sectors = forms.MultipleChoiceField(choices=sector_list, initial=[s[0] for s in sector_list],
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
        super().is_valid()
        return True

    def get_sentences(self):
        try:
            # Pourquoi on a pas ce fichu cleaned data !!! .......
            sentences = Sentence.objects.all()
        except AttributeError:
            companies = Company.objects.all()
        # TODO: add filter for sectors
        return companies

    def get_response(self):
        companies =