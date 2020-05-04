from .models import Company, DPEF
from django.views.generic.edit import FormView
from django.views import generic
from .forms import IndexForm


class IndexView(FormView):
    template_name = 'polls/index.html'
    form_class = IndexForm
    success_url = 'polls:search'

    def form_valid(self, form):
        return super().form_valid(form)


class CompanyListView(generic.ListView):
    template_name = 'polls/company_list.html'
    context_object_name = 'company_list'

    def get_queryset(self):
        companies = Company.objects.all()
        return companies


class CompanyDetailView(generic.DetailView):
    model = Company
    # template_name = 'polls/company_detail.html'


class SearchView(FormView):
    template_name = 'polls/search.html'
    form_class = IndexForm
    success_url = 'polls:search'

    def form_valid(self, form):
        return super().form_valid(form)
