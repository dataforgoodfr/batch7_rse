from .models import Company, DPEF
from django.views.generic.edit import View
from django.views import generic
from .forms import BasicSearchForm, SearchForm, CompanyForm
from django.shortcuts import render


class IndexView(View):
    template_name = 'polls/index.html'
    form_class = BasicSearchForm

    @staticmethod
    def get_context(form, response=None):
        context = {'form': form}
        if response is not None:
            context['response'] = response
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
        form = self.form_class(request.POST)
        response = None
        if form.is_valid():
            response = None  # TODO: Complete this to get a valid response.
        context = self.get_context(form, response)
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
        company_list = Company.objects.all()
        if form.is_valid():
            company_list = form.filter_company()
        context['company_list'] = company_list
        return context


class CompanyDetailView(generic.DetailView):
    model = Company
    # template_name = 'polls/company_detail.html'
