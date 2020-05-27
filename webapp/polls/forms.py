from django.utils.translation import gettext_lazy as _
from django import forms
from polls.models import ActivitySector as Sectors, Company, Sentence
from datetime import date
from polls.models import Company
from polls import nlp


class CompanyForm(forms.Form):
    company_name = forms.CharField(label=_("Nom de l'entreprise"), max_length=100, required=False)
    sector_list = [(sector.id, sector.name) for sector in Sectors.objects.all()]
    sectors = forms.MultipleChoiceField(choices=sector_list, initial=[s[0] for s in sector_list],
                                        widget=forms.CheckboxSelectMultiple, required=False)

    def filter_company(self):
        try:
            if self.cleaned_data['company_name'] == '':  # no company name set
                companies = Company.objects.filter(_activity_sectors__in=self.cleaned_data['sectors'])
            else:
                companies = Company.objects\
                    .filter(name__contains=self.cleaned_data['company_name'])\
                    .filter(_activity_sectors__in=self.cleaned_data['sectors'])
        except AttributeError:
            companies = Company.objects.all()
        return companies.distinct()


class BasicSearchForm(forms.Form):
    search_bar = forms.CharField(label=_("Rechercher"), max_length="100", required=True)

    def get_sentences(self):
        try:
            search_vector = nlp(self.cleaned_data['search_bar']).vector
            sentences = Sentence.objects.all()
            sentences = [(s, Sentence.similarity_vector(s.vector, search_vector)) for s in sentences]
            sentences = sorted(sentences, key=lambda s: s[1], reverse=False)
        except AttributeError:
            sentences = Sentence.objects.all()
        # TODO: add filter for sectors
        return sentences[:10]


class SearchForm(BasicSearchForm):
    company_name = forms.CharField(label=_("Nom de l'entreprise"), max_length=100, required=False)
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
        sentences = super().get_sentences()
        return sentences

    def get_response(self):
        companies = None
