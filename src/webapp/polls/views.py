from .models import Company, File, Sentence
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse


def index(request):
    company_list = Company.objects.all()
    context = {
        'company_list': company_list,
    }
    return render(request, 'polls/index.html', context)


def companies(request):
    """
    Return the whole list of companies.
    """
    return HttpResponse(f"Here are the company registered in the database : "
                        f"{[str(c) for c in Company.objects.all()]}.")


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


def company(request, company_id):
    """
    Return the company corresponding to the id passed in argument
    """
    company = get_object_or_404(Company, pk=company_id)
    context = {
        'company': company
    }
    return render(request, 'polls/company.html', context)



