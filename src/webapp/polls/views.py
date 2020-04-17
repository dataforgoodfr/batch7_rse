from .models import Company, File, Sentence
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from django.http import Http404


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

# def set_file(request, )


def company(request, company_id):
    """
    Return the company corresponding to the id passed in argument
    """
    company = get_object_or_404(Company, pk=company_id)
    context = {
        'company': company
    }
    return render(request, 'polls/company.html', context)



