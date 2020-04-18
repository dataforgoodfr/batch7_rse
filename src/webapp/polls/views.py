from .models import Company, File, Sentence
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.views import generic


class IndexView(generic.ListView):
    template_name = 'polls/index.html'
    context_object_name = 'company_list'

    def get_queryset(self):
        return Company.objects.all()


def companies(request):
    return HttpResponseRedirect(reverse('polls:index'))


class CompanyView(generic.DetailView):
    model = Company
    # template_name = 'polls/company_detail.html'


def set_file(request, company_id):
    company = get_object_or_404(Company, pk=company_id)
    try:
        selected_choice = company.file_set.get(pk=request.POST['file'])
    except (KeyError, File.DoesNotExist):
        # Redisplay the question voting form.
        return render(request, 'polls/company_forms.html', {
            'company': company,
            'error_message': "You didn't select a choice.",
        })
    else:
        # selected_choice.votes += 1
        # selected_choice.save()
        # Always return an HttpResponseRedirect after successfully dealing
        # with POST data. This prevents data from being posted twice if a
        # user hits the Back button.
        return HttpResponseRedirect(reverse('polls:company', args=(company.id,)))






