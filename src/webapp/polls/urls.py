from django.urls import path

from . import views


app_name = 'polls'
urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    # ex: /polls/company/
    path('company/', views.companies, name='companies'),
    # ex: /polls/company/5/
    path('company/<int:pk>/', views.CompanyView.as_view(), name='company'),
    path('company/<int:company_id>/set/', views.set_file, name='set_file'),
    path('importRSE/', views.ImportRSEView.as_view(), name='importRSE'),
]

