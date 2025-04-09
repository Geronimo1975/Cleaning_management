from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('customer/', views.customer_dashboard, name='customer_dashboard'),
    path('company/', views.company_dashboard, name='company_dashboard'),
    path('cleaner/', views.cleaner_dashboard, name='cleaner_dashboard'),
]
