from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    # ex: /polls/company/
    path('company/', views.companies, name='companies'),
    # ex: /polls/company/5/
    path('company/<int:company_id>/', views.company, name='company'),
]

