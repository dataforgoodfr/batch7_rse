from .models import Company, DPEF, ActivitySector
from django.views.generic.edit import View
from django.views import generic
from .forms import BasicSearchForm, SearchForm, CompanyForm
from django.shortcuts import render
from django.db.models import Count


class IndexView(View):
    template_name = 'polls/index.html'
    form_class = BasicSearchForm

    @staticmethod
    def get_context(form):
        context = {'form': form}
        response = []
        if form.is_valid() and form.is_bound:
            response = form.get_sentences()
        context['sentences'] = response
        context['total_companies'] = len(Company.objects.all())
        context['total_docs'] = len(DPEF.objects.all())
        context['total_sectors'] = len(ActivitySector.objects.all())
        context['total_sentences'] = len(list(DPEF.objects.aggregate(Count('sentence'))))
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


class CompanyDetailView(generic.DetailView):
    model = Company
    # template_name = 'polls/company_detail.html'
