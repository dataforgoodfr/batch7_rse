from .models import Company, DPEF
from django.views.generic.edit import FormView
from django.views import generic


class IndexView(generic.TemplateView):
    template_name = 'polls/index.html'


class CompanyListView(generic.ListView):
    template_name = 'polls/company_list.html'
    context_object_name = 'company_list'

    def get_queryset(self):
        companies = Company.objects.all()
        # for company in companies:
        #     company.dpef_list = DPEF.objects.filter(company__id=company.id)
        return companies


class CompanyDetailView(generic.DetailView):
    model = Company
    # template_name = 'polls/company_detail.html'


# class SearchView(FormView):

