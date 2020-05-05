from .models import Company, DPEF
from django.views.generic.edit import View, FormView
from django.views import generic
from .forms import BasicSearchForm, SearchForm
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


class CompanyListView(generic.ListView):
    template_name = 'polls/company_list.html'
    context_object_name = 'company_list'

    def get_queryset(self):
        companies = Company.objects.all()
        return companies


class CompanyDetailView(generic.DetailView):
    model = Company
    # template_name = 'polls/company_detail.html'
