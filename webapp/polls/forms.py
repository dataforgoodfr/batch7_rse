from django.utils.translation import gettext_lazy as _
from django import forms
from django.db.models import Q
from polls.models import ActivitySector as Sectors, Company, Sentence, DPEF
from datetime import date
from polls import nlp


def filter_company_from_form(my_form):
    """
        Takes an instance of a form object and apply the filter company on cleaned_data.
        It is created outside of functions to prevent duplication in CompanyForm and SearchForm
    """
    print(my_form.cleaned_data)
    print(my_form.cleaned_data['sectors'])
    try:
        if my_form.cleaned_data['company_name'].strip() == '':  # no company name set
            companies = Company.objects.filter(_activity_sectors__in=my_form.cleaned_data['sectors'])
        else:
            companies = Company.objects \
                .filter(name__contains=my_form.cleaned_data['company_name']) \
                .filter(_activity_sectors__in=my_form.cleaned_data['sectors'])
    except AttributeError:
        print("Error while filtering sectors OR the filled company name is unknown.")
        companies = Company.objects.all()
    return companies.distinct()


class CompanyForm(forms.Form):
    company_name = forms.CharField(label=_("Nom de l'entreprise"), max_length=100, required=False)
    sector_list = [(sector.id, sector.name) for sector in Sectors.objects.all()]
    sectors = forms.MultipleChoiceField(choices=sector_list, initial=[s[0] for s in sector_list],
                                        widget=forms.CheckboxSelectMultiple, required=False)

    def filter_company(self):
        return filter_company_from_form(self)


class BasicSearchForm(forms.Form):
    search_bar = forms.CharField(label=_("Rechercher"), max_length="100", required=True)

    def gather_sentences(self):
        """ This gather sentences into a QuerySet. It can be overwritten in child class SearchForm"""
        sentences = Sentence.objects.all()
        return sentences

    def get_best_matching_sentences(self):
        try:
            search_vector = nlp(self.cleaned_data['search_bar'].strip()).vector
        except AttributeError:
            # TODO: this should generate some sort of message somewhere to inform user that the query is not known.
            print("The query word was unknown. Returning empty QuerySet.")
            sentences = Sentence.objects.none()
            return sentences
        sentences = self.gather_sentences()
        sentences = [(s, Sentence.similarity_vector(s.vector, search_vector)) for s in sentences]
        sentences = sorted(sentences, key=lambda s: s[1], reverse=True)
        return sentences[:10]

    def clean_search_bar(self):
        cleaned_search_bar = self.cleaned_data['search_bar'].lower().strip()
        # TODO: here the test could be made that the vector exists.
        if cleaned_search_bar == "":
            msg = "Your query is empty."
            self.add_error('search_bar', msg)
        return cleaned_search_bar



class SearchForm(BasicSearchForm):
    company_name = forms.CharField(label=_("Nom de l'entreprise"), max_length=100, required=False)
    start_period = forms.IntegerField(label=_("De"), min_value=1990, max_value=date.today().year + 1, required=False)
    end_period = forms.IntegerField(label=_("à"), min_value=1990, max_value=date.today().year + 1, required=False)
    sector_list = [(sector.id, sector.name) for sector in Sectors.objects.all()]
    sectors = forms.MultipleChoiceField(choices=sector_list, initial=[s[0] for s in sector_list],
                                        widget=forms.CheckboxSelectMultiple, required=False)

    def _is_period_valid(self):
        try: # TODO: check if this should be self.data["start_period"] instead
            if self.start_period and self.end_period:
                if self.start_period > self.end_period:
                    return False
            return True
        except AttributeError:
            return True

    def is_valid(self):
        super().is_valid()
        return True

    def gather_sentences(self):
        """ This gather sentences into a QuerySet, filtering on sectors."""
        companies = filter_company_from_form(self)
        print(companies)
        dpefs = DPEF.objects
        if self.cleaned_data["start_period"] is not None:
            dpefs = dpefs.filter(year__gte=self.cleaned_data["start_period"])
        if self.cleaned_data["end_period"] is not None:
            dpefs = dpefs.filter(year__lte=self.cleaned_data["end_period"])
        dpefs = dpefs.filter(company__in=companies)
        print (self.cleaned_data["start_period"], self.cleaned_data["end_period"])
        print(dpefs)
        sentences = Sentence.objects.filter(dpef__in=dpefs).all()
        print(sentences)
        return sentences

    def get_response(self):
        companies = None
