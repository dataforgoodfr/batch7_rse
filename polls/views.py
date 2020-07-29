from pathlib import Path
import os
from django.http import HttpResponseForbidden, HttpResponse
from django.urls import reverse
from django.views.generic.detail import SingleObjectMixin
from django.db.models import Q

from .models import Company, DPEF, ActivitySector, Sentence, DPEF
from django.views.generic.edit import View
from django.views import generic
from .forms import BasicSearchForm, SearchForm, CompanyForm, CompanyDetailSearchForm
from django.shortcuts import render

class IndexView(View):
    template_name = 'polls/index.html'
    form_class = BasicSearchForm

    @staticmethod
    def get_context(form):
        context = {'form': form}
        response = []
        context["highlighted_words"] = [(word, 35) for word in ["engagement", "préservation", "environnement"]]
        if form.is_valid() and form.is_bound:
            response = form.get_best_matching_sentences()
            context["highlighted_words"] = [(word, 35) for word in form.cleaned_data['search_bar'].strip().split()]
        context['sentences'] = response
        context['total_companies'] = Company.objects.all().count()
        context['total_docs'] = DPEF.objects.all().count()
        context['total_sectors'] = ActivitySector.objects.all().count()
        context['total_sentences'] = Sentence.objects.all().count()
        return context

    def render(self, request, context: dict):
        return render(request, self.template_name, context)

    def get(self, request, *args, **kwargs):
        context = self.get_context(self.form_class())
        return self.render(request, context)

class SearchView(IndexView):
    template_name = 'polls/search.html'
    form_class = SearchForm

    def post(self, request, *args, **kwargs):
        context = self.get_context(self.form_class(request.POST))
        return self.render(request, context)

class CompanyListView(View):
    template_name = 'polls/company_list.html'
    form_class = CompanyForm

    def get(self, request, *args, **kwargs):
        context = self.get_context(self.form_class())
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        context = self.get_context(self.form_class(request.POST))
        return render(request, self.template_name, context)

    @staticmethod
    def get_context(form):
        context = {'form': form}
        if form.is_valid() and form.is_bound:
            company_list = form.filter_company()
        else:
            company_list = Company.objects.all()
        context['company_list'] = company_list
        context['total_companies'] = len(company_list)
        context['total_docs'] = len(DPEF.objects.all())
        context['total_sectors'] = len(ActivitySector.objects.all())
        return context


class CompanyDisplay(generic.DetailView):
    model = Company
    form = CompanyDetailSearchForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = CompanyDetailSearchForm()
        # Overwriting to have access to company named
        form.company_name = self.object.name
        context['form'] = form
        context["sentences"] = form.get_best_matching_sentences()
        company = Company.objects.filter(name__contains=self.object.name)
        context["dpefs"] = DPEF.objects.filter(company__in=company)
        return context


# todo: remove default values
def pdf_download_view(request, pk=1, year=2018):

    dpef = DPEF.objects.filter(Q(company__pk=pk) & Q(year=year))
    dpef_name = dpef[0].file_name
    dpef_path = Path(os.getcwd()) / 'data/polls/models/dpef/' / dpef_name

    with open(dpef_path, 'rb') as pdf:
        response = HttpResponse(pdf.read(), content_type='application/pdf')
        response['Content-Disposition'] = 'download;filename={dpef_name}.pdf'.format(dpef_name=dpef_name)
        return response
