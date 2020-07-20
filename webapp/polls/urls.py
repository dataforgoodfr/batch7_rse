from django.urls import path

from . import views


app_name = 'polls'
urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('entreprises/', views.CompanyListView.as_view(), name='company_list'),
    path('entreprises/<int:pk>/', views.CompanyDisplay.as_view(), name='company_detail'),
    path('search/', views.SearchView.as_view(), name='search'),
    path("entreprises/<int:pk>/<int:year>", views.pdf_download_view, name="download")
]

